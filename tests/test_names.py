from pathlib import Path

from sinan_anotador.cnv import parse_def
from sinan_anotador.names import (SOURCE_DEF, SOURCE_FORM, SOURCE_OTHER_DEF, FieldName, clean_def_label,
                                  labels_from_def, resolve_names)


def test_clean_def_label():
    assert clean_def_label("Ano da Notific", "DT_NOTIFIC") == "Data Notific"
    assert clean_def_label("Ano Diagnóstico", "DT_DIAG") == "Data Diagnóstico"
    assert clean_def_label("Mes da Notific", "DT_NOTIFIC") is None
    assert clean_def_label("Mun Resid CE", "ID_MN_RESI") == "Mun Resid"
    assert clean_def_label("Fx Etaria SINAN", "NU_IDADE_N") is None
    assert clean_def_label("UF Residência", "ID_MN_RESI") is None           # grouping on a municipality code
    assert clean_def_label("UF transferência", "UF_TRANSF") == "UF transferência"
    assert clean_def_label("Reg Metr Aten Atu", "ID_MUNIC_A") is None
    assert clean_def_label("Situação Encerra.", "SITUA_ENCE") == "Situação Encerra."


def test_labels_from_tb_def(tab_dir):
    d = parse_def(tab_dir / "TuberculNET5_0.def")
    lab = labels_from_def(d, {"ID_MUNIC_A": "MUNICCE.CNV"})
    assert lab["SITUA_ENCE"] == "Situação Encerra."
    assert lab["TRATAMENTO"] == "Tipo de entrada"
    assert lab["ID_MUNIC_A"] == "Mun Notif Atu"        # 5.0 wording ("Mun Atend Atu" in the old .def)
    assert lab["DT_INIC_TR"] == "Data Ini Trat Atu"
    assert lab["UF_TRANSF"] == "UF transferência"


def test_resolve_names_sources(tab_dir, tmp_path):
    """Fallback sources (form table, own .def, other .def) with no CSV dictionaries available."""
    d = parse_def(tab_dir / "GestSifNET.def")
    cols = ["NU_NOTIFIC", "CS_SEXO", "TPEVIDENCI", "ID_MN_RESI", "DT_NOTIFIC", "NM_PACIENT", "XPTO", "TRATAMENTO"]
    r = resolve_names(cols, d, tab_dir, {"ID_MN_RESI": "MUNICCE.CNV"}, csv_dir=tmp_path / "nenhum")
    assert r["NU_NOTIFIC"].name == "Número da notificação" and r["NU_NOTIFIC"].source == SOURCE_FORM
    assert r["CS_SEXO"].name == "Sexo" and r["CS_SEXO"].source == SOURCE_FORM and r["CS_SEXO"].def_label == "Sexo"
    assert r["TPEVIDENCI"].name == "Classificacao clínica" and r["TPEVIDENCI"].source == SOURCE_DEF
    assert r["ID_MN_RESI"].name == "Município de residência" and r["ID_MN_RESI"].def_label == "Mun Resid CE"
    assert r["DT_NOTIFIC"].name == "Data da notificação"
    assert r["NM_PACIENT"].name == "Nome do paciente"
    assert r["XPTO"].name is None and r["XPTO"].header() == "XPTO" and r["XPTO"].header("_rotulo") == "XPTO_rotulo"
    # a field the chosen .def does not describe gets a name from another .def; the same name can mean something else
    # there (TRATAMENTO is a date in leptospirosis, "tipo de entrada" in TB), which is why `campos` records the source
    assert r["TRATAMENTO"].name and r["TRATAMENTO"].source == SOURCE_OTHER_DEF


def test_header_format():
    fn = FieldName("CS_SEXO", "Sexo", SOURCE_FORM)
    assert fn.header() == "Sexo (CS_SEXO)"
    assert fn.header("_rotulo") == "Sexo — rótulo (CS_SEXO_rotulo)"
    assert FieldName("NU_IDADE_N", "Idade", SOURCE_FORM).header("_anos") == "Idade em anos (NU_IDADE_N_anos)"


def test_csv_dictionaries_prefer_the_disease(tab_dir):
    """tabelas/dicionarios: the disease's own CSV wins; def_tabwin rows are skipped; others fill the rest."""
    from sinan_anotador.names import load_csv_dictionaries
    folder = tab_dir.parent / "dicionarios"
    tb = load_csv_dictionaries(folder, "TuberculNET5_0")
    lv = load_csv_dictionaries(folder, "LeishvisNET")
    assert tb["TRATAMENTO"] == ("Tipo de Entrada", "dicionario_tuberculose.csv")
    assert lv["TRATAMENTO"] == ("Data do início do tratamento", "dicionario_lv.csv")
    assert tb["SITUA_ENCE"][0].lower().startswith("situação de encerramento")
    assert "DT_DIAG" not in tb or tb["DT_DIAG"][0] != "Ano Diagnóstico"      # def_tabwin rows are not dictionary names
    r = resolve_names(["DT_DIAG", "SITUA_ENCE", "TRATAMENTO", "CS_SEXO"], parse_def(tab_dir / "TuberculNET5_0.def"), tab_dir)
    assert r["DT_DIAG"].name == "Data do diagnóstico"
    assert r["SITUA_ENCE"].source == "dicionário CSV (dicionario_tuberculose.csv)"
    assert r["TRATAMENTO"].name == "Tipo de Entrada"


def test_form_table_beats_foreign_csv(tab_dir):
    d = parse_def(tab_dir / "GestSifNET.def")          # no CSV of its own in tabelas/dicionarios
    r = resolve_names(["ID_REGIONA", "SEM_NOT", "CLASSI_FIN", "CS_SEXO"], d, tab_dir)
    assert r["ID_REGIONA"].name == "Regional de saúde de notificação" and r["ID_REGIONA"].source == SOURCE_FORM
    assert r["SEM_NOT"].name == "Semana epidemiológica da notificação"
    assert r["CLASSI_FIN"].name == "Classificação final" and r["CLASSI_FIN"].source.startswith("dicionário CSV")
    tb = resolve_names(["CS_SEXO", "ID_REGIONA"], parse_def(tab_dir / "TuberculNET5_0.def"), tab_dir)
    assert tb["CS_SEXO"].source == "dicionário CSV (dicionario_tuberculose.csv)"      # own CSV wins over the form table
