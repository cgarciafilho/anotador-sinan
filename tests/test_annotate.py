import pytest

from sinan_anotador.annotate import (KNOWN_DBF_PREFIXES, FieldPlan, age_years, build_plan, code_of, detect_def,
                                     label_for)
from sinan_anotador.cnv import parse_cnv, parse_def


@pytest.mark.parametrize("code,years", [
    (4035, 35), ("4035", 35), (4000, 0), (4120, 120), (3005, 0), (2015, 0), (1010, 0),
    (None, None), ("", None), (0, None), (35, None), (5000, None), ("ABCD", None), (float("nan"), None), (4035.0, 35),
])
def test_age_years(code, years):
    assert age_years(code) == years


def test_code_of():
    assert code_of(None) == "" and code_of(float("nan")) == "" and code_of(4035.0) == "4035"
    assert code_of(" 01 ") == "01" and code_of(7) == "7"


def test_label_for_blank_and_unknown(tab_dir):
    fp = FieldPlan("CS_SEXO", parse_cnv(tab_dir / "Sexo.cnv"), 1)
    assert label_for("M", fp) == "Masculino"
    assert label_for("", fp) == "Em Branco"            # the table has its own blank line
    assert label_for("X", fp) == "[X] sem rótulo"
    fp2 = FieldPlan("X", parse_cnv(tab_dir / "Fxidad10NET.cnv"), 1)
    assert label_for("", fp2) == "Ign/Branco"           # no blank line in the table -> criterion 3 default
    assert label_for("4600", fp2) == "[4600] sem rótulo"


def test_label_for_start_position(tab_dir):
    fp = FieldPlan("DT", parse_cnv(tab_dir / "Meses.cnv"), 5)
    assert label_for("20190304", fp) == "Marco"


def test_municipality_chain(tab_dir):
    fp = FieldPlan("ID_MN_RESI", parse_cnv(tab_dir / "Municce.cnv"), 1, [parse_cnv(tab_dir / "Municbr.cnv")])
    assert label_for("230440", fp) == "Fortaleza"
    assert label_for("292700", fp) == "Rio Real (BA)"             # CE table wins
    assert label_for("355030", fp) == "São Paulo"                  # BR fallback
    assert label_for("999999", fp) == "Ignorado ou exterior"              # BR catch-all
    assert label_for("ABCDEF", fp) == "[ABCDEF] sem rótulo"


def test_detect_known_names(tab_dir):
    for prefix, names in KNOWN_DBF_PREFIXES.items():
        d, notes = detect_def(f"{prefix}.DBF", [], tab_dir)
        assert d is not None and d.name in names, (prefix, notes)
    d, _ = detect_def("TUBENET.DBF", ["TEST_MOLEC", "CS_SEXO"], tab_dir)
    assert d.name == "TuberculNET5_0"


def test_detect_by_pattern_and_fields(tab_dir):
    d, notes = detect_def("HANSNET2024.DBF", [], tab_dir)
    assert d.name == "HansNET"
    cols = sorted(parse_def(tab_dir / "MeningeNET.def").fields)
    d, notes = detect_def("EXPORT.DBF", cols, tab_dir)
    assert d.name == "MeningeNET" and any("conjunto de campos" in n for n in notes)
    d, notes = detect_def("EXPORT.DBF", ["A", "B"], tab_dir)
    assert d is None


def test_detect_sifilis_congenita_real_name(tab_dir):
    # Sinan NET exports congenital syphilis as SIFICNET.DBF; the TabWin .def pattern (Sifc*.DB?) never matched it
    d, notes = detect_def("SIFICNET.DBF", [], tab_dir)
    assert d.name == "SifilisNET" and any("nome do arquivo" in n for n in notes), notes


def test_detect_by_fields_prefers_specific_def_over_generic(tab_dir):
    # column set of the real SIFICNET.DBF (2026-10-28): all SifilisNET fields but the 7 CRI_* ones, plus the generic
    # notification fields; ranking by share alone picked NotnegatNET.def (5 of 5 present) over SifilisNET.def (47 of 54)
    sif = parse_def(tab_dir / "SifilisNET.def").fields
    neg = parse_def(tab_dir / "NotnegatNET.def").fields
    cols = sorted((sif - {f for f in sif if f.startswith("CRI_")}) | neg | {"DS_OBS", "NM_PACIENT", "DT_DIGITA"})
    d, notes = detect_def("EXPORT.DBF", cols, tab_dir)
    assert d.name == "SifilisNET", notes
    assert any("conjunto de campos" in n and "SifilisNET.def (47 de 54" in n for n in notes), notes
    # a DBF that really is the generic individual notification still gets the generic .def
    ind = sorted(parse_def(tab_dir / "NotIndiviNet.def").fields)
    d, notes = detect_def("EXPORT.DBF", ind, tab_dir)
    assert d.name == "NotIndiviNet", notes


def test_build_plan_tb(tab_dir):
    d = parse_def(tab_dir / "TuberculNET5_0.def")
    cols = sorted(d.fields)
    types = {c: ("D" if c.startswith("DT_") else "N" if c == "NU_IDADE_N" else "C") for c in cols}
    plan = build_plan(d, cols, types, tab_dir)
    for f in ["CS_SEXO", "CS_RACA", "CS_ESCOL_N", "CS_GESTANT", "TRATAMENTO", "FORMA", "SITUA_ENCE", "HIV",
              "ID_MN_RESI", "ID_MUNICIP", "ID_MUNIC_A", "AGRAVAIDS", "BACILOSC_E", "TEST_MOLEC", "CS_ZONA"]:
        assert f in plan.fields, f
    assert plan.fields["CS_SEXO"].cnv.name == "Sexo.cnv"
    assert plan.fields["ID_MN_RESI"].cnv.name == "Municce.cnv" and plan.fields["ID_MN_RESI"].fallbacks[0].name == "Municbr.cnv"
    assert plan.age_field == "NU_IDADE_N" and plan.age_band.name == "Fxidad10NET.cnv"
    for f in ["SG_UF", "SG_UF_NOT", "SG_UF_AT", "UF_TRANSF"]:          # UF fields: UFCODIGO is their category table
        assert f in plan.fields and plan.fields[f].cnv.name.upper() == "UFCODIGO.CNV", f
    assert not any("UFCCODIG" in w for w in plan.warnings)      # UFCODIGO/UFCCODIG are the same list, no warning
    assert label_for("CE", plan.fields["SG_UF"]) == "Ceará" and label_for("23", plan.fields["SG_UF"]) == "Ceará"
    assert "DT_NOTIFIC" not in plan.fields
    from sinan_anotador.lookup import LookupTable          # external tables present in tabelas/tab_sinannet since 2026-10-23;
    # unidanet.csv (public CNES, 2026-10-24) wins over TabWin's UNIDANET.DBF, which stays in the chain as a complement
    assert isinstance(plan.fields["ID_UNIDADE"].cnv, LookupTable) and plan.fields["ID_UNIDADE"].cnv.name == "unidanet.csv"
    assert [t.name for t in plan.fields["ID_UNIDADE"].fallbacks] == ["UNIDANET.DBF", "UNIDINVEST.DBF"]
    assert plan.fields["ID_UNID_AT"].cnv.name == "UNIDINVEST.DBF" and [t.name for t in plan.fields["ID_UNID_AT"].fallbacks] == ["unidanet.csv", "UNIDANET.DBF"]
    assert plan.fields["ID_OCUPA_N"].cnv.name == "OCUPANET.DBF"
    assert "ID_BAIRRO" not in plan.fields                 # BAIRRNET.DBF ships empty
    assert any(w.startswith("tabela externa BAIRRNET.DBF") for w in plan.warnings)   # ships empty -> refused
