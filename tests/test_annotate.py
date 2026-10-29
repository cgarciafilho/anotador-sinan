import pytest

from sinan_anotador.annotate import (KNOWN_DBF_PREFIXES, FieldPlan, age_years, apply_plan, build_plan, code_of, detect_def,
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
    assert not any("BAIRRNET" in w for w in plan.warnings)      # ships empty: not an AVISO, a per-field note
    assert any(s.startswith("ID_BAIRRO: tabela externa bairrnet.dbf vem vazia") for s in plan.skipped), plan.skipped


def test_dbf_field_aliases_plan_and_outside_list(tab_dir):
    """HANSNET.DBF exports BACILOSCO where HansNET.def says BACILOSCOP (2026-10-28): the column is planned under its own
    name and labelled with POSNEG.CNV; LTANET's DT_DESC3 is the .def's DT_DES3 (a date: no label, but not 'unknown')."""
    d = parse_def(tab_dir / "HansNET.def")
    plan = build_plan(d, ["BACILOSCO", "CS_SEXO"], {"BACILOSCO": "C", "CS_SEXO": "C"}, tab_dir)
    assert plan.fields["BACILOSCO"].cnv.name.upper() == "POSNEG.CNV"
    assert not any(s.startswith("BACILOSCOP:") for s in plan.skipped)
    from sinan_anotador.cnv import def_field
    assert def_field("BACILOSCO") == "BACILOSCOP" and def_field("DT_DESC3") == "DT_DES3" and def_field("cs_sexo") == "CS_SEXO"


def test_real_export_names_recognised_by_def_pattern(tab_dir, monkeypatch):
    """The `A` lines of the .def files carry the Sinan NET export names as the SESA-CE TabWin writes them (TUBEN*.DBF,
    SifiCN*.DBF…), so the eight export names seen in real bases resolve by pattern alone; KNOWN_DBF_PREFIXES is only a reserve."""
    import sinan_anotador.annotate as A
    monkeypatch.setattr(A, "KNOWN_DBF_PREFIXES", {})
    expect = {"TUBENET.DBF": "TuberculNET5_0", "SIFGENET.DBF": "GestSifNET", "SIFICNET.DBF": "SifilisNET", "HANSNET.DBF": "HansNET",
              "LEISHNET.DBF": "LeishvisNET", "MENINNET.DBF": "MeningeNET", "LTANET.DBF": "LeishtegNET", "DENGNET.DBF": "DengueNET",
              "NINDINET.DBF": "NotIndiviNet", "EPIZONET.DBF": "EpizotNet", "TETANNET.DBF": "TetneoNET"}
    for dbf, name in expect.items():
        d = parse_def(tab_dir / f"{name}.def")
        chosen, notes = detect_def(dbf, sorted(d.fields), tab_dir)
        assert chosen is not None and chosen.name == name, (dbf, chosen and chosen.name, notes)
        assert "reconhecido pelo padrão de arquivo do .def" in notes[0], notes


def test_prison_units_table_does_not_displace_cnes_lookup(tab_dir):
    """NotIndiviNet.def (SESA version) cites Unid_Prisionais.CNV for ID_UNIDADE; the field keeps the CNES lookup chain."""
    d = parse_def(tab_dir / "NotIndiviNet.def")
    assert any(ln.cnv and ln.cnv.lower() == "unid_prisionais.cnv" for ln in d.lines)
    cols = ["ID_UNIDADE", "ID_OCUPA_N"]
    plan = build_plan(d, cols, {c: "C" for c in cols}, tab_dir)
    fp = plan.fields["ID_UNIDADE"]
    assert "unidanet" in fp.cnv.name.lower(), fp.cnv.name
    assert [f.name for f in fp.fallbacks][-1] == "Unid_Prisionais.CNV"
    assert "ITAITINGA" in label_for("6375286", fp).upper()           # prison unit: named by the CNES table itself
    assert "WALTER CANT" in label_for("2561492", fp).upper()         # a hospital: would be "sem rótulo" with the prison table alone
    assert any(n.startswith("ID_UNIDADE: tabela externa unidanet.dbf primeiro") for n in plan.notes), plan.notes
    # same rule gives NotIndiviNet occupations their CBO names instead of the GRUPO1a.CNV major groups
    fo = plan.fields["ID_OCUPA_N"]
    assert "ocupanet" in fo.cnv.name.lower() and label_for("223505", fo).upper() == "ENFERMEIRO"      # CBO 2235-05


def test_missing_cnv_rebuilt_from_dictionary_csv(tab_dir, tmp_path):
    """When a .cnv cited by the .def is absent and the agravo's dictionary CSV carries its categories (categorias_cnv), the
    table is rebuilt in memory and the log says where it came from. ESQUETER.CNV / ESQUETERatu.CNV (HansNET.def) were the
    real case until 2026-10-29 (the partial TAB_SINANNET extraction lacked them); the full package has them, so the test
    removes the two files from a copy of the folder (symlinks) to keep exercising the fallback, then checks that with the
    real folder the real table is used and gives the same labels."""
    tab = tmp_path / "tab"
    tab.mkdir()
    for p in tab_dir.iterdir():
        if p.name.upper() not in ("ESQUETER.CNV", "ESQUETERATU.CNV"):
            (tab / p.name).symlink_to(p)
    d = parse_def(tab / "HansNET.def")
    cols = ["ESQ_INI_N", "ESQ_ATU_N", "CS_SEXO"]
    plan = build_plan(d, cols, {c: "C" for c in cols}, tab, csv_dir=tab_dir.parent / "dicionarios")
    fp = plan.fields["ESQ_INI_N"]
    assert fp.cnv.name.startswith("ESQUETER.CNV (reconstruída de dicionario_hans.csv)")
    assert label_for("1", fp) == "PQT/PB/6 DOSES" and label_for("2", fp) == "PQT/MB/12 DOSES"
    assert label_for("0", fp) == "Ign/Branco" and label_for("", fp) == "Ign/Branco" or label_for("", fp) == "[em branco]"
    assert plan.fields["ESQ_ATU_N"].cnv.name.startswith("ESQUETERatu.CNV (reconstruída")
    assert {"ESQUETER.CNV", "ESQUETERatu.CNV"} <= plan.missing_cnv
    assert any(n.startswith("ESQ_INI_N: tabela ESQUETER.CNV ausente") for n in plan.notes), plan.notes
    assert not any("ESQ_INI_N" in w for w in plan.warnings)
    # without the CSV the field stays unlabelled and the table is still listed as missing
    plan2 = build_plan(d, cols, {c: "C" for c in cols}, tab, csv_dir=tab / "nenhum")
    assert "ESQ_INI_N" not in plan2.fields and "ESQUETER.CNV" in plan2.missing_cnv
    assert any(w.startswith("ESQ_INI_N: tabela ESQUETER.CNV citada no .def não está disponível") for w in plan2.warnings)
    # with the real folder (full TAB_SINANNET) the real file wins and agrees with the dictionary
    plan3 = build_plan(parse_def(tab_dir / "HansNET.def"), cols, {c: "C" for c in cols}, tab_dir)
    fp3 = plan3.fields["ESQ_INI_N"]
    assert fp3.cnv.name == "ESQUETER.CNV" and not plan3.missing_cnv
    assert [label_for(c, fp3) for c in "123"] == [label_for(c, fp) for c in "123"]
    assert label_for("3", plan3.fields["ESQ_ATU_N"]) == "OUTROS ESQUEMAS SUBSTITUTIVOS"


def test_dose_recebida_table_switches_on_classopera(tab_dir):
    """DOSE_RECEB has three tables in HansNET.def; '6 doses' is the full scheme only for paucibacillary cases, so the table
    follows CLASSOPERA in each record (1 -> nudosePB, 2 -> nudoseMB, other -> plain count)."""
    import pandas as pd
    d = parse_def(tab_dir / "HansNET.def")
    cols = ["DOSE_RECEB", "CLASSOPERA"]
    plan = build_plan(d, cols, {"DOSE_RECEB": "N", "CLASSOPERA": "C"}, tab_dir)
    fp = plan.fields["DOSE_RECEB"]
    assert fp.switch is not None and fp.switch[0] == "CLASSOPERA" and fp.cnv.name.lower() == "nudoses.cnv"
    assert not any("DOSE_RECEB" in w for w in plan.warnings)
    assert any(n.startswith("DOSE_RECEB: tabela escolhida por CLASSOPERA") for n in plan.notes), plan.notes
    df = pd.DataFrame({"DOSE_RECEB": ["06", "06", "12", "12", "03", ""], "CLASSOPERA": ["1", "2", "2", "1", "9", "1"]})
    out, dic = apply_plan(df, plan)
    assert out["DOSE_RECEB_rotulo"].tolist() == ["6 doses", "<12", "12 doses", "maior que 6", "03", "não preenchido/Ign"]
    assert set(dic[dic["campo"] == "DOSE_RECEB"]["tabela"].str.lower()) == {"nudosepb.cnv", "nudosemb.cnv", "nudoses.cnv"}


def test_dengue_criterio_table_follows_notification_year(tab_dir):
    """DengueNET.def lists CONFDESC.CNV ("ate2010") and CONFDESCDENG2011.CNV ("pos2010") for CRITERIO: the table follows
    NU_ANO in each record; code 3 is 'Em Investigação' only in the 2011 form (tables from TAB_SINANONLINE.zip, 2026-10-28)."""
    import pandas as pd
    d = parse_def(tab_dir / "DengueNET.def")
    cols = ["CRITERIO", "NU_ANO", "CLASSI_FIN"]
    plan = build_plan(d, cols, {"CRITERIO": "C", "NU_ANO": "C", "CLASSI_FIN": "C"}, tab_dir)
    fp = plan.fields["CRITERIO"]
    assert fp.switch is not None and fp.switch[0] == "NU_ANO" and fp.cnv.name.upper() == "CONFDESCDENG2011.CNV"
    assert any(n.startswith("CRITERIO: tabela escolhida por NU_ANO") and "1990–2010 → " in n for n in plan.notes), plan.notes
    df = pd.DataFrame({"CRITERIO": ["1", "3", "3", "2"], "NU_ANO": ["2009", "2010", "2024", ""], "CLASSI_FIN": ["1", "10", "11", "12"]})
    out, _ = apply_plan(df, plan)
    # 2010: the old table has no code 3 and its blank line covers 0-9, so 3 reads as Ign/Branco; 2024: 'Em Investigação'
    assert out["CRITERIO_rotulo"].tolist() == ["Laboratórial", "Ign/Branco", "Em Investigação", "Clínico-epidemiológico"]
    assert out["CLASSI_FIN_rotulo"].tolist() == ["Dengue Clássico", "Dengue", "Dengue com sinais de alarme", "Dengre grave"]
