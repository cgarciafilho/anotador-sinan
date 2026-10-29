"""Hand-written expectations read off the .cnv/.def files (tabelas/tab_sinannet), independent of the parser."""
from pathlib import Path

import pytest

from sinan_anotador.cnv import dbf_pattern_to_regex, def_files, find_cnv, parse_cnv, parse_def


def test_sexo(tab_dir):
    c = parse_cnv(tab_dir / "Sexo.cnv")
    assert c.width == 1
    assert [lab for _, lab in c.categories] == ["Em Branco", "Ignorado", "Masculino", "Feminino"]
    assert c.lookup("M") == "Masculino" and c.lookup("F") == "Feminino" and c.lookup("I") == "Ignorado"
    assert c.lookup("") == "Em Branco"
    assert c.lookup("X") is None


def test_sim_nao_catch_all_then_specific(tab_dir):
    c = parse_cnv(tab_dir / "Sim_nao.cnv")
    assert c.lookup("1") == "Sim" and c.lookup("2") == "Não"
    for code in ["0", "3", "9", ""]:
        assert c.lookup(code) == "Ign/Branco"
    assert c.lookup("10") is None


def test_escolaridade_two_spellings(tab_dir):
    c = parse_cnv(tab_dir / "Escolarnet.cnv")
    assert c.width == 2
    assert c.lookup("0") == "Analfabeto" and c.lookup("00") == "Analfabeto"
    assert c.lookup("1") == c.lookup("01") == "1ª a 4ª série incompleta do EF"
    assert c.lookup("8") == "Educação superior completa"
    assert c.lookup("10") == "Não se aplica"
    assert c.lookup("9") == c.lookup("09") == c.lookup("99") == c.lookup("") == "Ign/Branco"


def test_anos_last_line_wins(tab_dir):
    c = parse_cnv(tab_dir / "Anos.cnv")
    assert c.lookup("0000") == "IGN"
    assert c.lookup("1980") == "<1991"
    assert c.lookup("1991") == "1991"
    assert c.lookup("2010") == "2010"


def test_faixa_etaria_ranges(tab_dir):
    c = parse_cnv(tab_dir / "Fxidad10NET.cnv")
    assert c.width == 4
    assert c.lookup("1005") == c.lookup("2015") == c.lookup("3011") == "<1 Ano"
    assert c.lookup("4000") is None            # 4000 (0 anos) is in no range of this table
    assert c.lookup("4001") == "1-4" and c.lookup("4019") == "15-19" and c.lookup("4035") == "35-49"
    assert c.lookup("4080") == c.lookup("4120") == "80 e+"
    assert c.lookup("4600") is None and c.lookup("") is None


def test_municipios_ce_e_br(tab_dir):
    ce = parse_cnv(tab_dir / "Municce.cnv")
    assert ce.width == 6 and len(ce.categories) == 187
    assert ce.lookup("230440") == "230440 Fortaleza"
    assert ce.lookup("230010") == "230010 Abaiara"
    assert ce.lookup("292700") == "292700 Rio Real (BA)"
    assert ce.lookup("350000") is None
    br = parse_cnv(tab_dir / "Municbr.cnv")
    assert len(br.categories) == 5657
    assert br.lookup("150475") == "150475 Mojuí dos Campos"       # line with a trailing tab in the file
    assert br.lookup("999999") == "000000 Ignorado ou exterior"
    assert br.lookup("005000") == "000000 Ignorado ou exterior"
    assert br.lookup("ABCDEF") is None


def test_uf_codigo_letters_and_numbers(tab_dir):
    c = parse_cnv(tab_dir / "UFcodigo.cnv")
    assert c.lookup("23") == "23 Ceará" and c.lookup("CE") == "23 Ceará"


def test_raca_unicode_filename(tab_dir):
    p = find_cnv("RAÇA.CNV", tab_dir)
    assert p is not None and p.name == "Raça.cnv"
    c = parse_cnv(p)
    assert c.lookup("4") == "Parda" and c.lookup("0") == "Ign/Branco"


def test_trailing_comma_is_not_blank(tab_dir):
    c = parse_cnv(tab_dir / "nudosePB.cnv")       # lines like `6 doses   06, 6,6 ,`
    assert c.lookup("") == "não preenchido/Ign"
    assert c.lookup("6") == c.lookup("06") == "6 doses"
    assert c.lookup("0") == c.lookup("00") == "nenhuma dose"
    assert c.lookup("3") == "menor que 6" and c.lookup("20") == "maior que 6"
    br = parse_cnv(tab_dir / "Municbr.cnv")       # blank token in the middle of the list is a blank category
    assert br.lookup("") == "000000 Ignorado ou exterior"


def test_header_with_stray_comment(tab_dir):
    c = parse_cnv(tab_dir / "Modoentr.cnv")      # second line starts with ':' instead of ';'
    assert c.width == 1 and c.lookup("1") == "Caso Novo"


def test_header_with_extra_token(tmp_path):
    """rj_regsaudn.cnv and six other health-region tables of TAB_SINANNET write the header as "10  6   33X001": the third
    token is not the usual single letter and must not stop the parse."""
    p = tmp_path / "x_regsaudn.cnv"
    p.write_bytes(b"     2  6                                                  33X001    \r\n"
                  b"      1  33001 RJ Regiao A                                     330010\r\n"
                  b"      2  33002 RJ Regiao B                                     330020\r\n")
    c = parse_cnv(p)
    assert c.width == 6 and len(c.categories) == 2 and c.lookup("330020").startswith("33002 RJ Regiao B")


def test_all_cnv_parse(tab_dir):
    for p in tab_dir.glob("*.cnv"):
        c = parse_cnv(p)
        assert c.width > 0 and c.categories, p.name


def test_def_tuberculose(tab_dir):
    d = parse_def(tab_dir / "TuberculNET5_0.def")
    assert d.dbf_pattern.upper().endswith("TUBEN*.DBF")      # linha A do TabWin da SESA-CE (2026-10-29): nome real do export
    by_field = {}
    for ln in d.lines:
        by_field.setdefault(ln.field, []).append(ln)
    assert {ln.cnv.upper() for ln in by_field["CS_SEXO"]} == {"SEXO.CNV"}
    assert {ln.cnv.upper() for ln in by_field["SITUA_ENCE"]} == {"ENCERRA.CNV"}
    assert any(ln.cnv and ln.cnv.upper() == "MESES.CNV" and ln.start == 5 for ln in by_field["DT_NOTIFIC"])
    assert any(ln.lookup_dbf and ln.lookup_dbf.upper() == "OCUPANET.DBF" for ln in by_field["ID_OCUPA_N"])
    assert any(ln.kind == "I" and ln.cnv is None for ln in by_field["NU_COMU_EX"])


def test_all_defs_parse(tab_dir):
    for p in def_files(tab_dir):
        d = parse_def(p)
        assert d.dbf_pattern and d.lines, p.name


@pytest.mark.parametrize("pattern,name,ok", [
    (r"c:\SinanNet\BaseDBF\TUBE*.DB?", "TUBENET.DBF", True),
    (r"c:\SinanNet\BaseDBF\TUBE*.DB?", "tubenet.dbf", True),
    (r"c:\SinanNet\BaseDBF\TUBE*.DB?", "SIFGENET.DBF", False),
    (r"c:\SinanNet\BaseDBF\SIFG*.DB?", "SIFGENET.DBF", True),
])
def test_pattern(pattern, name, ok):
    assert bool(dbf_pattern_to_regex(pattern).match(name)) is ok
