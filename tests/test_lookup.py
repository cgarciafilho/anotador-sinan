"""External lookup tables (unidanet.dbf-style) for health units, occupations and similar fields."""
import datetime as dt
import shutil
from collections import Counter
from pathlib import Path

import pytest

from dbf_writer import write_dbf
from sinan_anotador.cli import annotate_file
from sinan_anotador.cnv import def_files, parse_def
from sinan_anotador.lookup import LookupTable, load_lookup
from test_end_to_end import column, read_sheet

UNITS = {"2561492": "HOSPITAL GERAL DE FORTALEZA", "2497654": "UBS JOSÉ WALTER", "2528223": "HOSPITAL SÃO JOSÉ",
         "6789012": "CENTRO DE SAÚDE AÇUDE"}
CBO = {"223505": "Enfermeiro", "322205": "Técnico de enfermagem", "999999": "Ocupação ignorada"}


@pytest.fixture(scope="module")
def tab_with_lookups(tab_dir, tmp_path_factory) -> Path:
    """A copy of the TabWin tables plus a synthetic unidanet.dbf (cp850) and ocupanet.csv."""
    d = tmp_path_factory.mktemp("tab")
    for p in def_files(tab_dir) + list(tab_dir.glob("*.cnv")):
        shutil.copy(p, d / p.name)
    write_dbf(d / "unidanet.dbf", [("ID_UNIDADE", "C", 7, 0), ("NM_UNIDADE", "C", 60, 0)],
              [{"ID_UNIDADE": k, "NM_UNIDADE": v} for k, v in UNITS.items()], encoding="cp850")
    (d / "ocupanet.csv").write_text("ID_OCUPA_N,NM_OCUPACA\n" + "\n".join(f"{k},{v}" for k, v in CBO.items()) + "\n",
                                    encoding="utf-8")
    return d


def test_load_dbf_and_csv(tab_with_lookups):
    t = load_lookup(tab_with_lookups / "unidanet.dbf", "ID_UNIDADE", "NM_UNIDADE")
    assert t.n_rows == 4 and t.lookup("2497654") == "UBS JOSÉ WALTER" and t.lookup("6789012") == "CENTRO DE SAÚDE AÇUDE"
    assert t.lookup("0000000") is None and t.lookup("") is None
    c = load_lookup(tab_with_lookups / "ocupanet.csv", "ID_OCUPA_N", "NM_OCUPACA")
    assert c.lookup("223505") == "Enfermeiro" and c.lookup("22350") is None


def test_units_and_occupation_get_labels(tab_with_lookups, tmp_path):
    deffile = parse_def(tab_with_lookups / "TuberculNET5_0.def")
    fields = [("NU_NOTIFIC", "C", 7, 0), ("DT_NOTIFIC", "D", 8, 0), ("ID_UNIDADE", "C", 7, 0), ("ID_UNID_AT", "C", 7, 0),
              ("ID_OCUPA_N", "C", 6, 0), ("CS_SEXO", "C", 1, 0)]
    codes = list(UNITS) + ["1234567", "", "2561492"]
    recs = [dict(NU_NOTIFIC=f"{i:07d}", DT_NOTIFIC=dt.date(2020, 1, 1), ID_UNIDADE=c, ID_UNID_AT=c,
                 ID_OCUPA_N=["223505", "322205", "", "000001"][i % 4], CS_SEXO="M") for i, c in enumerate(codes)]
    dbf = write_dbf(tmp_path / "TUBENET.DBF", fields, recs)
    ok, files = annotate_file(dbf, tab_with_lookups, None, None, 1_048_575)
    assert ok
    header, rows = read_sheet(files[0], "dados")
    assert "ID_UNIDADE_rotulo" in header and "ID_UNID_AT_rotulo" in header and "ID_OCUPA_N_rotulo" in header
    got = Counter(column(header, rows, "ID_UNIDADE_rotulo"))
    exp = Counter([*UNITS.values(), "[1234567] sem rótulo", "Ign/Branco", "HOSPITAL GERAL DE FORTALEZA"])
    assert got == exp
    assert column(header, rows, "ID_UNID_AT_rotulo") == column(header, rows, "ID_UNIDADE_rotulo")
    assert Counter(column(header, rows, "ID_OCUPA_N_rotulo")) == Counter(
        ["Enfermeiro", "Técnico de enfermagem", "Ign/Branco", "[000001] sem rótulo"] * (len(codes) // 4)
        + ["Enfermeiro", "Técnico de enfermagem", "Ign/Branco", "[000001] sem rótulo"][: len(codes) % 4])
    dic_h, dic = read_sheet(files[0], "dicionario")
    unit_rows = [r for r in dic if r[1] == "unidanet.dbf"]
    assert {r[2] for r in unit_rows} == set(UNITS) and all(r[4].startswith("tabela externa") for r in unit_rows)
    log = (tmp_path / "TUBENET_anotado.log.txt").read_text(encoding="utf-8")
    assert "Tabela externa unidanet.dbf: 4 códigos" in log and "ocupanet.csv: 3 códigos" in log
    assert "Tabela externa unidanet.dbf" in log


def test_without_lookup_files_fields_are_skipped_with_message(tab_dir, tmp_path):
    bare = tmp_path / "tab"
    bare.mkdir()
    for p in def_files(tab_dir) + list(tab_dir.glob("*.cnv")):
        shutil.copy(p, bare / p.name)
    fields = [("NU_NOTIFIC", "C", 7, 0), ("ID_UNIDADE", "C", 7, 0), ("CS_SEXO", "C", 1, 0)]
    dbf = write_dbf(tmp_path / "TUBENET.DBF", fields, [dict(NU_NOTIFIC="0000001", ID_UNIDADE="2561492", CS_SEXO="M")])
    ok, files = annotate_file(dbf, bare, None, None, 1_048_575)
    header, rows = read_sheet(files[0], "dados")
    assert "ID_UNIDADE_rotulo" not in header
    assert "ID_UNIDADE: tabela externa unidanet.dbf não disponível" in (tmp_path / "TUBENET_anotado.log.txt").read_text(encoding="utf-8")


def test_real_tabwin_tables(tab_dir, tmp_path):
    """tabelas/tab_sinannet now holds the DATASUS tables (2021): UNIDANET and UNIDINVEST complement each other."""
    fields = [("NU_NOTIFIC", "C", 7, 0), ("ID_UNIDADE", "C", 7, 0), ("ID_UNID_AT", "C", 7, 0), ("ID_OCUPA_N", "C", 6, 0),
              ("ID_PAIS", "C", 4, 0), ("ID_AGRAVO", "C", 4, 0), ("CS_SEXO", "C", 1, 0)]
    recs = [dict(NU_NOTIFIC="0000001", ID_UNIDADE="2561492", ID_UNID_AT="2561492", ID_OCUPA_N="223505", ID_PAIS="1",
                 ID_AGRAVO="A159", CS_SEXO="M"),
            dict(NU_NOTIFIC="0000002", ID_UNIDADE="9999999", ID_UNID_AT="", ID_OCUPA_N="", ID_PAIS="", ID_AGRAVO="", CS_SEXO="F")]
    dbf = write_dbf(tmp_path / "TUBENET.DBF", fields, recs)
    ok, files = annotate_file(dbf, tab_dir, None, None, 1_048_575)
    assert ok
    header, rows = read_sheet(files[0], "dados")
    assert column(header, rows, "ID_UNIDADE_rotulo") == ["HOSPITAL UNIVERSITARIO WALTER CANTIDIO", "[9999999] sem rótulo"]
    assert column(header, rows, "ID_UNID_AT_rotulo") == ["HOSPITAL UNIVERSITARIO WALTER CANTIDIO", "Ign/Branco"]
    assert column(header, rows, "ID_OCUPA_N_rotulo") == ["ENFERMEIRO", "Ign/Branco"]
    assert column(header, rows, "ID_PAIS_rotulo") == ["BRASIL", "Ign/Branco"]
    assert "ID_AGRAVO_rotulo" not in header            # ID_AGRAVO is not in the TB .def (AGRAVNET.DBF has no name column anyway)
    log = (tmp_path / "TUBENET_anotado.log.txt").read_text(encoding="utf-8")
    assert "UNIDANET.DBF: 37693 códigos" in log and "UNIDINVEST.DBF: 55658 códigos" in log


def test_csv_wins_over_dbf_and_dbf_complements(tab_with_lookups, tmp_path):
    """A unidanet.csv (built from the public CNES) beats TabWin's unidanet.dbf; codes only in the DBF still get a label."""
    from sinan_anotador.lookup import find_lookup_files
    d = tmp_path / "tab"
    shutil.copytree(tab_with_lookups, d)
    (d / "unidanet.csv").write_text("ID_UNIDADE,NM_UNIDADE\n2561492,HOSPITAL UNIVERSITARIO WALTER CANTIDIO\n"
                                    "7000001,UBS NOVA (2026)\n", encoding="utf-8")
    assert [p.name for p in find_lookup_files("unidanet.dbf", d)] == ["unidanet.csv", "unidanet.dbf"]
    deffile = parse_def(d / "TuberculNET5_0.def")
    fields = [("NU_NOTIFIC", "C", 7, 0), ("ID_UNIDADE", "C", 7, 0), ("CS_SEXO", "C", 1, 0)]
    recs = [dict(NU_NOTIFIC=f"{i:07d}", ID_UNIDADE=c, CS_SEXO="M") for i, c in enumerate(["2561492", "7000001", "2497654", "1"])]
    dbf = write_dbf(tmp_path / "TUBENET.DBF", fields, recs)
    ok, files = annotate_file(dbf, d, None, None, 1_048_575)
    assert ok
    header, rows = read_sheet(files[0], "dados")
    assert column(header, rows, "ID_UNIDADE_rotulo") == [
        "HOSPITAL UNIVERSITARIO WALTER CANTIDIO",     # CSV wins over the DBF's "HOSPITAL GERAL DE FORTALEZA"
        "UBS NOVA (2026)",                            # only in the CSV
        "UBS JOSÉ WALTER",                            # only in the DBF: complement
        "[1] sem rótulo"]
    log = (tmp_path / "TUBENET_anotado.log.txt").read_text(encoding="utf-8")
    assert "unidanet.csv: 2 códigos" in log and "unidanet.dbf: 4 códigos" in log
    assert ("Cobertura ID_UNIDADE: 4 registros preenchidos; rotulados por unidanet.csv 2 (2 códigos), unidanet.dbf 1 (1 códigos); "
            "sem rótulo 1 (25.0%; 1 códigos distintos)") in log


def test_csv_gz_is_read(tmp_path):
    import gzip
    p = tmp_path / "unidanet.csv.gz"
    p.write_bytes(gzip.compress("ID_UNIDADE,NM_UNIDADE\n0000001,UNIDADE UM\n".encode("utf-8")))
    t = load_lookup(p, "ID_UNIDADE", "NM_UNIDADE")
    assert t.lookup("0000001") == "UNIDADE UM" and t.lookup("1") == "UNIDADE UM"


def test_code_column_falls_back_to_first_id_column(tmp_path):
    """MeningeNET.def reads ATE_HOSP_1 (and GestSifNET PRE_UNIPRE) from UNIDINVEST.dbf, whose code column is ID_UNIDADE:
    the first ID_/CO_/CD_ column serves as code column, with a note, instead of refusing the table (2026-10-28)."""
    write_dbf(tmp_path / "unidinvest.dbf", [("ID_UNIDADE", "C", 7, 0), ("NM_UNIDADE", "C", 60, 0)],
              [{"ID_UNIDADE": k, "NM_UNIDADE": v} for k, v in UNITS.items()], encoding="cp850")
    t = load_lookup(tmp_path / "unidinvest.dbf", "ATE_HOSP_1", "NM_UNIDADE")
    assert t.lookup("2561492") == "HOSPITAL GERAL DE FORTALEZA"
    assert any(n.startswith("coluna ATE_HOSP_1 ausente; códigos lidos de ID_UNIDADE") for n in t.notes), t.notes
    write_dbf(tmp_path / "tres.dbf", [("ID_UNIDADE", "C", 7, 0), ("NM_UNIDADE", "C", 60, 0), ("ID_ESTAB", "C", 7, 0)],
              [{"ID_UNIDADE": k, "NM_UNIDADE": v, "ID_ESTAB": k} for k, v in UNITS.items()], encoding="cp850")
    with pytest.raises(ValueError):
        load_lookup(tmp_path / "tres.dbf", "ATE_HOSP_1", "NM_OUTRA")     # no name column: still refused


# --- 2026-10-29: what the 35 real SESA bases showed (METODO 2026-10-29, C1-C4) ---------------------------------------------

def test_pick_columns_contains_and_truncated_names():
    """C1: CNAENET.DBF holds CLASS_CNAE/DS_CNAE/CO_SEQ and the .def asks (cnae, ds_cnae); DISTRNET.dbf holds NM_DISTRIT and the
    .def of esquistossomose asks NM_DISTRITO (DBF names stop at 10 characters). Before: CO_SEQ was taken as the code column."""
    from sinan_anotador.lookup import _pick_columns
    notes: list[str] = []
    assert _pick_columns(["CLASS_CNAE", "DS_CNAE", "CO_SEQ"], "cnae", "ds_cnae", notes) == ("CLASS_CNAE", "DS_CNAE")
    assert any("CLASS_CNAE" in n for n in notes)
    notes = []
    cols = ["ID_DISTRIT", "NM_DISTRIT", "ID_MUNICIP", "ID_DT_RESI", "ST_ATIVO", "ID_SISTEMA"]
    assert _pick_columns(cols, "CODISINF", "NM_DISTRITO", notes) == ("ID_DISTRIT", "NM_DISTRIT")
    assert any("10 caracteres" in n for n in notes)
    # exact names still win and leave no note
    notes = []
    assert _pick_columns(["ID_UNIDADE", "NM_UNIDADE", "CO_CNES"], "ID_UNIDADE", "NM_UNIDADE", notes) == ("ID_UNIDADE", "NM_UNIDADE")
    assert notes == []


def test_cnae_table_labels_by_class_code(tab_dir, tmp_path):
    d = tmp_path / "tab"
    d.mkdir()
    for p in def_files(tab_dir) + list(tab_dir.glob("*.cnv")) + list(tab_dir.glob("*.CNV")):
        shutil.copy(p, d / p.name)
    write_dbf(d / "CNAENET.DBF", [("CLASS_CNAE", "C", 5, 0), ("DS_CNAE", "C", 60, 0), ("CO_SEQ", "N", 5, 0)],
              [{"CLASS_CNAE": "15890", "DS_CNAE": "FABRICACAO DE OUTROS PRODUTOS ALIMENTICIOS", "CO_SEQ": 69},
               {"CLASS_CNAE": "45217", "DS_CNAE": "EDIFICACOES", "CO_SEQ": 300}])
    t = load_lookup(d / "CNAENET.DBF", "cnae", "ds_cnae")
    assert t.lookup("15890") == "FABRICACAO DE OUTROS PRODUTOS ALIMENTICIOS" and t.lookup("69") is None
    fields = [("NU_NOTIFIC", "C", 7, 0), ("DT_NOTIFIC", "D", 8, 0), ("CNAE", "C", 5, 0), ("CS_SEXO", "C", 1, 0)]
    recs = [dict(NU_NOTIFIC=f"{i:07d}", DT_NOTIFIC=dt.date(2026, 1, 1), CNAE=c, CS_SEXO="M")
            for i, c in enumerate(["15890", "45217", "", "99999"])]
    dbf = write_dbf(tmp_path / "ACGRANET.DBF", fields, recs)
    ok, files = annotate_file(dbf, d, None, None, 1_048_575)
    assert ok
    header, rows = read_sheet(files[0], "dados")
    assert column(header, rows, "CNAE_rotulo") == ["FABRICACAO DE OUTROS PRODUTOS ALIMENTICIOS", "EDIFICACOES", "Ign/Branco",
                                                   "[99999] sem rótulo"]


def test_cid10_csv_answers_for_agravnet(tab_dir, tmp_path):
    """C2/C3: agravnet.csv (CID-10 from the TabWin of the SIM) labels CID_ACID; TabWin's AGRAVNET.DBF (no name column) is noted,
    not warned about; a 4-character code the table lacks falls back to its 3-character category."""
    csv_path = tab_dir / "agravnet.csv"
    assert csv_path.exists()
    t = load_lookup(csv_path, "CID_ACID", "NM_AGRAVO")
    assert t.n_rows >= 14_400
    assert t.lookup("A000") == "Cólera devida a Vibrio cholerae 01, biótipo cholerae"
    assert t.lookup("X45") == "Envenenamento [intoxicação] acidental por e exposição ao álcool"
    assert t.lookup("X450") == "Envenenamento [intoxicação] acidental por e exposição ao álcool - residência"
    assert t.lookup("M545") == "Dor lombar baixa" and t.lookup("D170") == "Neoplasia lipomatosa benigna da pele e do tecido subcutâneo da cabeça, face e pescoço"
    assert t.lookup("Z999") == "Dependência de máquina e aparelho capacitante não especificado"
    assert t.lookup("A002") == t.lookup("A00") == "Cólera"      # subcategory the CID-10 lacks -> its category
    assert t.lookup("2497654") is None and t.lookup("Q999") is not None
    d = tmp_path / "tab"
    d.mkdir()
    for p in def_files(tab_dir) + list(tab_dir.glob("*.cnv")) + list(tab_dir.glob("*.CNV")) + [csv_path, tab_dir / "AGRAVNET.DBF"]:
        shutil.copy(p, d / p.name)
    fields = [("NU_NOTIFIC", "C", 7, 0), ("DT_NOTIFIC", "D", 8, 0), ("CID_ACID", "C", 4, 0), ("CS_SEXO", "C", 1, 0)]
    recs = [dict(NU_NOTIFIC=f"{i:07d}", DT_NOTIFIC=dt.date(2026, 1, 1), CID_ACID=c, CS_SEXO="M")
            for i, c in enumerate(["X450", "X45", "M545", "", "A002", "ZZZZ"])]
    dbf = write_dbf(tmp_path / "ACGRANET.DBF", fields, recs)
    ok, files = annotate_file(dbf, d, None, None, 1_048_575)
    assert ok
    header, rows = read_sheet(files[0], "dados")
    assert column(header, rows, "CID_ACID_rotulo") == [
        "Envenenamento [intoxicação] acidental por e exposição ao álcool - residência",
        "Envenenamento [intoxicação] acidental por e exposição ao álcool", "Dor lombar baixa", "Ign/Branco",
        "Cólera", "[ZZZZ] sem rótulo"]
    log = Path(str(files[0]).replace("_anotado.xlsx", "_anotado.log.txt")).read_text(encoding="utf-8")
    assert "AVISO tabela externa AGRAVNET.DBF" not in log and "substituída por agravnet.csv" in log


# ----------------------------------------------------------------------------- CNAE 2.3 next to CNAE 1.0 (METODO 2026-11-04)
def _tab_with_cnae(tab_dir, d: Path) -> Path:
    """TabWin tables plus a two-row CNAENET.DBF (CNAE 1.0) and the real cnaenet_cnae23.csv of the repository."""
    d.mkdir()
    for p in def_files(tab_dir) + list(tab_dir.glob("*.cnv")) + list(tab_dir.glob("*.CNV")):
        shutil.copy(p, d / p.name)
    shutil.copy(tab_dir / "cnaenet_cnae23.csv", d / "cnaenet_cnae23.csv")
    write_dbf(d / "CNAENET.DBF", [("CLASS_CNAE", "C", 5, 0), ("DS_CNAE", "C", 60, 0), ("CO_SEQ", "N", 5, 0)],
              [{"CLASS_CNAE": "15890", "DS_CNAE": "FABRICACAO DE OUTROS PRODUTOS ALIMENTICIOS", "CO_SEQ": 69},
               {"CLASS_CNAE": "45217", "DS_CNAE": "EDIFICACOES", "CO_SEQ": 300}])
    return d


def test_cnae23_csv_is_complete_and_disjoint_from_cnae10(tab_dir):
    """C1: the shipped CNAE 2.3 table has the 673 classes and 1.332 subclasses, every subclass starts with its class, and no
    5-digit code of the TabWin CNAE 1.0 table (CNAENET.DBF, 580 classes) exists in it."""
    import csv
    rows = list(csv.DictReader((tab_dir / "cnaenet_cnae23.csv").open(encoding="utf-8")))
    classes = {r["CODIGO"] for r in rows if r["NIVEL"] == "classe"}
    subs = {r["CODIGO"] for r in rows if r["NIVEL"] == "subclasse"}
    assert len(rows) == 2005 and len(classes) == 673 and len(subs) == 1332
    assert all(len(c) == 5 and c.isdigit() for c in classes) and all(len(s) == 7 and s.isdigit() for s in subs)
    assert all(s[:5] in classes for s in subs)
    assert all(r["NOME"] for r in rows) and len({r["CODIGO"] for r in rows}) == len(rows)
    t10 = load_lookup(tab_dir / "CNAENET.DBF", "cnae", "ds_cnae")
    assert t10.n_rows == 580
    assert not [c for c in classes if t10.lookup(c) is not None]      # zero codes in common between the versions
    t23 = load_lookup(tab_dir / "cnaenet_cnae23.csv", "cnae", "ds_cnae")
    assert t23.lookup("86101") == "Atividades de atendimento hospitalar" and t23.lookup("9900800")
    assert t23.lookup("8610101").startswith("Atividades de atendimento hospitalar, exceto")
    assert t23.lookup("4713001") == t23.lookup("47130")        # subclass retired in 2.3 -> its class
    assert t23.lookup("15890") is None and t23.lookup("1234567") is None


def test_complement_files_follow_csv_and_precede_dbf(tab_dir, tmp_path):
    """C2: `<stem>_*.csv` complements come after `<stem>.csv` and before the DBF; the CNAE chain is cnaenet_cnae23.csv, CNAENET.DBF."""
    from sinan_anotador.lookup import find_lookup_files
    d = _tab_with_cnae(tab_dir, tmp_path / "tab")
    assert [p.name for p in find_lookup_files("cnaenet.dbf", d)] == ["cnaenet_cnae23.csv", "CNAENET.DBF"]
    (d / "CNAENET.csv").write_text("CODIGO,NOME\n99999,Teste\n", encoding="utf-8")
    (d / "cnaenet_b.csv.gz").write_bytes(b"")
    assert [p.name for p in find_lookup_files("cnaenet.dbf", d)] == ["CNAENET.csv", "cnaenet_b.csv.gz", "cnaenet_cnae23.csv",
                                                                     "CNAENET.DBF"]
    assert [p.name for p in find_lookup_files("unidanet.dbf", d)] == []


def test_cnae_fields_label_both_versions_and_log_lists_missing_codes(tab_dir, tmp_path):
    """C2/C3 end to end: 1.0 code keeps the 1.0 name, 2.3 class and subclass get the 2.3 name, a retired subclass falls back to
    its class, unknown codes stay unlabelled; the log breaks the unlabelled codes down by length and lists them; the dictionary
    sheet carries one row per unlabelled code."""
    d = _tab_with_cnae(tab_dir, tmp_path / "tab")
    fields = [("NU_NOTIFIC", "C", 7, 0), ("DT_NOTIFIC", "D", 8, 0), ("CNAE", "C", 7, 0), ("CS_SEXO", "C", 1, 0)]
    codes = ["15890", "86101", "8610101", "4713001", "", "99999", "99999", "1234567", "123"]
    recs = [dict(NU_NOTIFIC=f"{i:07d}", DT_NOTIFIC=dt.date(2026, 1, 1), CNAE=c, CS_SEXO="M") for i, c in enumerate(codes)]
    dbf = write_dbf(tmp_path / "ACGRANET.DBF", fields, recs)
    ok, files = annotate_file(dbf, d, None, None, 1_048_575)
    assert ok
    header, rows = read_sheet(files[0], "dados")
    assert column(header, rows, "CNAE_rotulo") == [
        "FABRICACAO DE OUTROS PRODUTOS ALIMENTICIOS", "Atividades de atendimento hospitalar",
        "Atividades de atendimento hospitalar, exceto pronto-socorro e unidades para atendimento a urgências",
        "Comércio varejista de mercadorias em geral, sem predominância de produtos alimentícios", "Ign/Branco",
        "[99999] sem rótulo", "[99999] sem rótulo", "[1234567] sem rótulo", "[123] sem rótulo"]
    log = (tmp_path / "ACGRANET_anotado.log.txt").read_text(encoding="utf-8")
    cov = next(l for l in log.splitlines() if l.strip().startswith("Cobertura CNAE:"))
    assert "8 registros preenchidos" in cov and "cnaenet_cnae23.csv 3 (3 códigos)" in cov and "CNAENET.DBF 1 (1 códigos)" in cov
    assert "sem rótulo 4 (50.0%; 3 códigos distintos)" in cov
    assert ("Códigos sem rótulo em CNAE (3 distintos; por comprimento: 3 dígitos 1; 5 dígitos 1; 7 dígitos 1): "
            "99999 ×2, 123 ×1, 1234567 ×1") in log
    dh, drows = read_sheet(files[0], "dicionario")
    missing = [r for r in drows if r[dh.index("campo")] == "CNAE" and r[dh.index("rotulo")] == "[sem rótulo]"]
    assert sorted(r[dh.index("codigos")] for r in missing) == ["123", "1234567", "99999"]
    assert all(r[dh.index("uso")].startswith("tabela externa (código ausente das tabelas; ") for r in missing)
    assert all(not r[dh.index("tabela")] for r in missing)        # in none of the tables of the chain
    labelled = [r for r in drows if r[dh.index("campo")] == "CNAE" and r[dh.index("rotulo")] != "[sem rótulo]"]
    assert {r[dh.index("tabela")] for r in labelled} == {"cnaenet_cnae23.csv", "CNAENET.DBF"}


def test_cnes_code_absent_from_unidanet_does_not_fall_back_to_a_prefix(tab_with_lookups):
    """The class-prefix fallback is for CNAE tables only: a 7-digit CNES code the unit table lacks stays unlabelled even when its
    first five digits happen to be a code of the table."""
    d = tab_with_lookups
    (d / "unidanet.csv").write_text("ID_UNIDADE,NM_UNIDADE\n25614,UNIDADE DE CINCO DIGITOS\n", encoding="utf-8")
    try:
        t = load_lookup(d / "unidanet.csv", "ID_UNIDADE", "NM_UNIDADE")
        assert t.class_prefix == 0 and t.lookup("25614") and t.lookup("2561492") is None
    finally:
        (d / "unidanet.csv").unlink()


# ----------------------------------------------------------------------------- code review of 2026-11-04 (findings 4-5)
def test_dictionary_lists_a_code_only_under_the_table_that_labelled_it():
    """Finding 4: a code labelled by the first fallback was listed again under every later fallback that also knew it, with
    that table's unused name; the dictionary rows now follow the chain the way label_for walks it."""
    import pandas as pd
    from sinan_anotador.annotate import FieldPlan, Plan, apply_plan
    from sinan_anotador.cnv import DefFile
    t1 = LookupTable("a.csv", Path("a.csv"), "ID_UNIDADE", "NM"); t1.add("1", "UM A")
    t2 = LookupTable("b.dbf", Path("b.dbf"), "ID_UNIDADE", "NM"); t2.add("2", "DOIS B")
    t3 = LookupTable("c.dbf", Path("c.dbf"), "ID_UNIDADE", "NM"); t3.add("2", "DOIS C"); t3.add("3", "TRES C")
    plan = Plan(DefFile("x", Path("x"), None, []), {"ID_UNIDADE": FieldPlan("ID_UNIDADE", t1, 1, [t2, t3])}, None, None, [], [])
    ann, dic = apply_plan(pd.DataFrame({"ID_UNIDADE": ["1", "2", "3", "9"]}), plan)
    assert ann["ID_UNIDADE_rotulo"].tolist() == ["UM A", "DOIS B", "TRES C", "[9] sem rótulo"]
    rows = sorted((r.tabela, r.codigos, r.rotulo) for r in dic.itertuples())
    assert rows == sorted([("a.csv", "1", "UM A"), ("b.dbf", "2", "DOIS B"), ("c.dbf", "3", "TRES C"), ("", "9", "[sem rótulo]")])


def test_lookup_dbf_with_blank_numeric_codes(tmp_path):
    """Finding 5: a blank integer code (pd.NA after read_dbf) became the code '<NA>' and a blank numeric code with decimals
    (NaN) raised on int(nan), rejecting the whole table."""
    write_dbf(tmp_path / "regionet.dbf", [("ID_REGIONA", "N", 4, 0), ("NM_REGIONA", "C", 30, 0)],
              [{"ID_REGIONA": 1, "NM_REGIONA": "PRIMEIRA"}, {"ID_REGIONA": None, "NM_REGIONA": "SEM CODIGO"},
               {"ID_REGIONA": 2, "NM_REGIONA": "SEGUNDA"}])
    t = load_lookup(tmp_path / "regionet.dbf", "ID_REGIONA", "NM_REGIONA")
    assert t.n_rows == 2 and t.lookup("<NA>") is None and t.lookup("1") == "PRIMEIRA" and t.lookup("0002") == "SEGUNDA"
    write_dbf(tmp_path / "paisnet.dbf", [("ID_PAIS", "N", 6, 1), ("NM_PAIS", "C", 30, 0)],
              [{"ID_PAIS": 1.0, "NM_PAIS": "BRASIL"}, {"ID_PAIS": None, "NM_PAIS": "SEM CODIGO"}])
    t = load_lookup(tmp_path / "paisnet.dbf", "ID_PAIS", "NM_PAIS")
    assert t.n_rows == 1 and t.lookup("1") == "BRASIL"
