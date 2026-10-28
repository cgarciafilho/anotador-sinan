"""Acceptance criterion of the `duplicidades` sheets (METODO.md, 2026-10-25), on synthetic DBFs with planted pairs."""
from __future__ import annotations

import datetime as dt
from collections import Counter

import pytest
from openpyxl import load_workbook

from sinan_anotador.cli import annotate_file
from sinan_anotador.cnv import parse_def
import pandas as pd

from sinan_anotador.duplicates import Profile, birth_one_component_off, build_tables, classify, load_ads, norm_name, similar
from synthetic_dups import make_synthetic_dups

AGRAVOS = {"TUBENET": "TuberculNET5_0", "HANSNET": "HansNET", "SIFGENET": "GestSifNET", "DENGNET": "DengueNET"}
KEY_OF_TYPE = {"erro_nome": "nasc_nome_sim", "nasc_1comp": "nome_nasc1"}


def read_sheet(path, name):
    wb = load_workbook(path, read_only=True)
    rows = list(wb[name].iter_rows(values_only=True))
    wb.close()
    header = rows[0]
    return [dict(zip(header, tuple(r) + (None,) * (len(header) - len(r)))) for r in rows[1:]]   # read-only mode trims empty cells


@pytest.fixture(scope="module", params=sorted(AGRAVOS))
def case(request, tab_dir, tmp_path_factory):
    stem = request.param
    tmp = tmp_path_factory.mktemp(stem)
    deffile = parse_def(tab_dir / f"{AGRAVOS[stem]}.def")
    dbf, truth = make_synthetic_dups(deffile, tab_dir, tmp / f"{stem}.DBF", stem, seed=sum(map(ord, stem)))
    ok, files = annotate_file(dbf, tab_dir, None, None, 1_048_575)
    assert ok, (tmp / f"{stem}_anotado.log.txt").read_text(encoding="utf-8")
    full = read_sheet(files[0], "duplicidades")
    short = read_sheet(files[0], "duplicidades_resumo")
    data = read_sheet(files[0], "dados")
    by_pair = {frozenset((r["NU_NOTIFIC_A"], r["NU_NOTIFIC_B"])): r for r in full}
    return dict(stem=stem, truth=truth, full=full, short=short, data=data, by_pair=by_pair, tmp=tmp, kind=truth["kind"])


def planted(case, *types):
    return [t for t in case["truth"]["truth"] if t["tipo"] in types]


def test_c1_padrao_finds_every_identical_identity(case):
    """C1: the Sinan NET key lists 100% of the planted pairs whose first/last name, birth and sex are identical."""
    for t in planted(case, "exata", "mae_branco", "homonimo", "julgado", "transferencia", "recidiva", "gest_dif", "gest_mesma"):
        r = case["by_pair"].get(frozenset((t["a"], t["b"])))
        assert r is not None, f"par plantado não listado: {t}"
        assert "padrao" in r["chaves"].split("+"), (t, r["chaves"])


def test_c2_additional_keys_recall_and_precision(case):
    """C2: each additional key finds >= 90% of its target type and <= 5% of its pairs link different planted people."""
    for tipo, key in KEY_OF_TYPE.items():
        tgt = planted(case, tipo)
        found = sum(1 for t in tgt if key in (case["by_pair"].get(frozenset((t["a"], t["b"])), {}).get("chaves") or "").split("+"))
        assert found >= 0.9 * len(tgt), (tipo, key, found, len(tgt))
    # nome_mae targets only the birth-date error: a letter changed in the name changes the full name too (METODO 2026-10-25,
    # correction to the pre-registered text, which listed the name typo as a nome_mae target by mistake)
    tgt = planted(case, "nasc_1comp")
    found = sum(1 for t in tgt if "nome_mae" in (case["by_pair"].get(frozenset((t["a"], t["b"])), {}).get("chaves") or "").split("+"))
    assert found >= 0.9 * len(tgt), ("nome_mae", found, len(tgt))
    person = case["truth"]["person_of"]
    homonyms = {frozenset((t["a"], t["b"])) for t in planted(case, "homonimo")}
    for key in ("nome_mae", "nome_nasc1", "nasc_nome_sim"):
        rows = [r for r in case["full"] if key in r["chaves"].split("+")]
        wrong = [r for r in rows if frozenset((r["NU_NOTIFIC_A"], r["NU_NOTIFIC_B"])) not in homonyms
                 and person.get(r["NU_NOTIFIC_A"], r["NU_NOTIFIC_A"]) != person.get(r["NU_NOTIFIC_B"], r["NU_NOTIFIC_B"])]
        assert len(wrong) <= 0.05 * max(len(rows), 1), (key, len(wrong), len(rows), wrong[:3])


def test_c3_labels(case):
    """C3: suggested labels per planted type (thresholds of METODO 2026-10-25)."""
    def rate(tipo):
        tgt = planted(case, tipo)
        if not tgt:
            return None
        ok = sum(1 for t in tgt if (case["by_pair"].get(frozenset((t["a"], t["b"])), {}).get("tipo_sugerido") or "").startswith(t["label"]))
        return ok / len(tgt)
    assert rate("homonimo") == 1.0, [case["by_pair"].get(frozenset((t["a"], t["b"])), {}).get("tipo_sugerido") for t in planted(case, "homonimo")]
    if case["kind"] in ("tb", "hans"):
        assert rate("transferencia") >= 0.9
        assert rate("recidiva") >= 0.9
        assert rate("exata") >= 0.9, [case["by_pair"].get(frozenset((t["a"], t["b"])), {}).get("tipo_sugerido") for t in planted(case, "exata")]
    if case["kind"] == "gest":
        assert rate("gest_dif") == 1.0
        assert rate("gest_mesma") == 1.0
    if case["kind"] == "agudo":
        assert rate("exata") == 1.0
        for t in planted(case, "exata"):
            r = case["by_pair"][frozenset((t["a"], t["b"]))]
            assert r["dias_entre_eventos"] is not None and r["campo_do_evento"] == "DT_SIN_PRI"


def test_c4_suggested_record_is_the_earlier_notification(case):
    """C4: the suggested record to keep is the earlier notification; tie -> notified by the municipality of residence."""
    for r in case["full"]:
        da, db = r["DT_NOTIFIC_A"], r["DT_NOTIFIC_B"]
        if da != db:
            earlier = r["NU_NOTIFIC_A"] if da < db else r["NU_NOTIFIC_B"]
            assert r["ficha_sugerida_manter"] == earlier, r
            assert r["motivo_ficha_sugerida"].startswith("notificação mais antiga")
        else:
            assert r["motivo_ficha_sugerida"].startswith("mesma data")


def test_c5_judged_pairs_flagged_and_no_record_removed(case):
    """C5: pairs with NDUPLIC_N = 1 are flagged 'já julgado'; the data sheet keeps every record."""
    for t in planted(case, "julgado"):
        assert case["by_pair"][frozenset((t["a"], t["b"]))]["ja_julgado_no_sinan"] == "sim"
    for t in planted(case, "exata"):
        assert case["by_pair"][frozenset((t["a"], t["b"]))]["ja_julgado_no_sinan"] == "não"
    assert len(case["data"]) == case["truth"]["n"]


def test_short_sheet_matches_full(case):
    """The short sheet has one row per pair, the same labels, and blank columns for the team's decision."""
    assert len(case["short"]) == len(case["full"])
    assert [r["tipo_sugerido"] for r in case["short"]] == [r["tipo_sugerido"] for r in case["full"]]
    assert all(r["decisao_da_equipe"] is None and r["observacao"] is None for r in case["short"])
    assert all(r["unidade_A"] for r in case["short"])
    assert all(r["ADS_notificacao_A"] and r["ADS_notificacao_B"] and r["ADS_residencia"] for r in case["short"]), "ADS em branco"
    assert list(case["short"][0].keys())[:4] == ["par", "ADS_notificacao_A", "ADS_notificacao_B", "ADS_residencia"]


def test_log_reports_pairs(case):
    log = (case["tmp"] / f"{case['stem']}_anotado.log.txt").read_text(encoding="utf-8")
    assert "Duplicidades suspeitas:" in log and "padrao" in log
    assert "Registros que nenhuma chave alcança: 0 " in log     # the synthetic base has name, birth and mother everywhere


@pytest.mark.parametrize("a,b,expected", [
    (dt.date(1980, 3, 4), dt.date(1980, 3, 5), True), (dt.date(1980, 3, 4), dt.date(1981, 3, 4), True),
    (dt.date(1980, 3, 4), dt.date(1980, 4, 3), True), (dt.date(1980, 3, 4), dt.date(1981, 4, 5), False),
    (dt.date(1980, 3, 4), dt.date(1980, 3, 4), False),
])
def test_birth_one_component_off(a, b, expected):
    assert birth_one_component_off(a, b) is expected


def test_norm_and_similar():
    assert norm_name(" José  da Silva-Araújo ") == "JOSE DA SILVA ARAUJO"
    assert similar("MARIA DA SILVA", "MARIA DA SYLVA") and not similar("MARIA DA SILVA", "JOANA PEREIRA")


def test_ads_table(tab_dir):
    ads = load_ads(tab_dir.parent / "regionalizacao_sesa_sr_ads.csv")
    assert len(ads) == 184 and len({v[0] for v in ads.values()}) == 22 and len({v[1] for v in ads.values()}) == 5
    assert ads["230440"] == ("Fortaleza", "Fortaleza") and ads["231290"][0] == "Sobral" and ads["230190"][0] == "Juazeiro do Norte"


def test_no_key_counts(tab_dir, tmp_path):
    """Records without name, birth or mother are counted in the log and still kept in the data sheet."""
    import datetime as dt
    import pandas as pd
    from sinan_anotador.duplicates import build_tables
    rows = [dict(NU_NOTIFIC="1", NM_PACIENT="ANA SILVA", NM_MAE_PAC="RITA", DT_NASC=dt.date(1990, 1, 1), CS_SEXO="F", DT_NOTIFIC=dt.date(2020, 1, 1)),
            dict(NU_NOTIFIC="2", NM_PACIENT="", NM_MAE_PAC="RITA", DT_NASC=dt.date(1990, 1, 1), CS_SEXO="F", DT_NOTIFIC=dt.date(2020, 1, 2)),
            dict(NU_NOTIFIC="3", NM_PACIENT="ANA SILVA", NM_MAE_PAC="", DT_NASC=None, CS_SEXO="F", DT_NOTIFIC=dt.date(2020, 1, 3)),
            dict(NU_NOTIFIC="4", NM_PACIENT="ANA", NM_MAE_PAC="RITA", DT_NASC=dt.date(1990, 1, 1), CS_SEXO="", DT_NOTIFIC=dt.date(2020, 1, 4))]
    df = pd.DataFrame(rows)
    full, short, st = build_tables(df, list(df.columns), "DengueNET")
    assert st["sem_chave"] == {"sem_nome": 1, "nome_de_uma_palavra": 1, "sem_nascimento": 1, "sem_sexo": 1, "sem_mae": 1, "fora_de_toda_chave": 2}


@pytest.mark.parametrize("days,expected", [(315, "mesma gestação?"), (316, "gestação diferente")])
def test_gestation_window_is_45_weeks(days, expected):
    """Syphilis in pregnancy: diagnoses up to 45 weeks (315 days) apart may be the same pregnancy (METODO 2026-10-26)."""
    prof = Profile("sifilis_gestante", "DT_DIAG")
    a = pd.Series({"DT_DIAG": pd.Timestamp("2024-01-01")})
    b = pd.Series({"DT_DIAG": pd.Timestamp("2024-01-01") + pd.Timedelta(days=days)})
    label, _ = classify(a, b, prof, False, "igual")
    assert label.startswith(expected), label


def test_gestation_shows_labels_not_codes():
    """CS_GESTANT appears as its gestante.cnv label: code 4 is 'idade gestacional ignorada', not a 4th trimester."""
    prof = Profile("sifilis_gestante", "DT_DIAG")
    a = pd.Series({"DT_DIAG": pd.Timestamp("2024-01-01"), "CS_GESTANT": "1", "CS_GESTANT_rotulo": "1º Trimestre"})
    b = pd.Series({"DT_DIAG": pd.Timestamp("2024-02-10"), "CS_GESTANT": "4", "CS_GESTANT_rotulo": "Idade gestacional Ignorada"})
    label, _ = classify(a, b, prof, False, "igual")
    assert label == ("mesma gestação? (40 dias entre diagnósticos, ≤ 45 semanas; "
                     "gestação: 1º trimestre / idade gestacional ignorada)"), label


def test_gestation_labels_in_the_sheet(case):
    """End to end: every 'mesma gestação?' pair names both pregnancy stages by their labels, never as bare codes."""
    if case["kind"] != "gest":
        pytest.skip("só sífilis em gestante")
    rows = [r for r in case["full"] if r["tipo_sugerido"].startswith("mesma gestação?")]
    assert rows
    for r in rows:
        assert "trimestres " not in r["tipo_sugerido"]
        stages = f"gestação: {r['CS_GESTANT_rotulo_A'].lower()} / {r['CS_GESTANT_rotulo_B'].lower()})"
        assert r["tipo_sugerido"].endswith(stages), r["tipo_sugerido"]


def test_ads_outside_ceara_falls_back_to_sinan_regional_or_blank(tab_dir, tmp_path, monkeypatch):
    """A base from another state (METODO 2026-10-28): nothing breaks, the ADS column shows the Sinan regional label when
    ID_REGIONA has a known code, stays empty when the code is unknown or blank (never "Ign/Branco"), the log counts the
    blank sides, and pairs without ADS sort last."""
    import synthetic_dups, dbf_writer
    sp = ["355030", "350950", "354340", "354870", "352590"]            # São Paulo, Campinas, Ribeirão Preto, Santos, Jundiaí
    regional = {"355030": "1350", "350950": "1350", "354340": "9999", "354870": "", "352590": ""}   # 1350 is in REGIONET; 9999 is not
    monkeypatch.setattr(synthetic_dups, "MUNS", sp)
    original = dbf_writer.write_dbf

    def with_regional(path, fields, records, **kw):
        names = {f[0] for f in fields}
        for r in records:
            if "ID_REGIONA" in names:
                r["ID_REGIONA"] = regional[r["ID_MUNICIP"]]
            if "ID_RG_RESI" in names:
                r["ID_RG_RESI"] = regional[r["ID_MN_RESI"]]
        return original(path, fields, records, **kw)
    monkeypatch.setattr(synthetic_dups, "write_dbf", with_regional)

    deffile = parse_def(tab_dir / "TuberculNET5_0.def")
    dbf, truth = synthetic_dups.make_synthetic_dups(deffile, tab_dir, tmp_path / "TUBENET.DBF", "TUBENET", seed=7)
    ok, files = annotate_file(dbf, tab_dir, None, None, 1_048_575)
    log = (tmp_path / "TUBENET_anotado.log.txt").read_text(encoding="utf-8")
    assert ok, log
    short = read_sheet(files[0], "duplicidades_resumo")
    full = read_sheet(files[0], "duplicidades")
    assert len(short) == len(full) == 80                                   # same pairs as a Ceará base
    values = {r[c] for r in short for c in ("ADS_notificacao_A", "ADS_notificacao_B", "ADS_residencia")}
    assert "Ign/Branco" not in values and not any(isinstance(v, str) and "sem rótulo" in v for v in values)
    assert "GVE XXVI SAO JOAO DA BOA VISTA" in values                     # code 1350: the Sinan regional name is used
    expected = {"355030": "GVE XXVI SAO JOAO DA BOA VISTA", "350950": "GVE XXVI SAO JOAO DA BOA VISTA"}
    for r in full:
        assert r["ADS_notificacao_A"] == expected.get(str(r["ID_MUNICIP_A"]))   # unknown (9999) and blank codes -> empty cell
    missing = sum(r[c] is None for r in full for c in ("ADS_notificacao_A", "ADS_notificacao_B"))
    assert missing > 0 and f"{missing} lados de par sem ADS" in log
    ads_a = [r["ADS_notificacao_A"] for r in short]
    first_none = ads_a.index(None)
    assert all(v is None for v in ads_a[first_none:])                      # pairs without ADS come last


@pytest.mark.parametrize("days,band", [(0, "mesmo dia"), (1, "1 a 7 dias"), (7, "1 a 7 dias"), (8, "8 a 30 dias"), (30, "8 a 30 dias"),
                                       (31, "31 a 90 dias"), (90, "31 a 90 dias"), (91, "91 a 365 dias"), (365, "91 a 365 dias"),
                                       (366, "mais de 365 dias")])
def test_acute_intervals_are_banded(days, band):
    prof = Profile("agudo", "DT_SIN_PRI")
    a = pd.Series({"DT_SIN_PRI": pd.Timestamp("2024-01-01")})
    b = pd.Series({"DT_SIN_PRI": pd.Timestamp("2024-01-01") + pd.Timedelta(days=days)})
    label, _ = classify(a, b, prof, False, "igual")
    assert label == f"mesma pessoa, {band} ({days} dias entre eventos, DT_SIN_PRI): duplicidade se for o mesmo evento", label


def test_acute_interval_beyond_base_span_is_a_date_error(tmp_path):
    """LEISHNET/LTANET (2026-10-28): pairs 17,399 to 23,443 days apart, i.e. a typo in one DT_SIN_PRI; above the base's
    own span of DT_NOTIFIC plus a year the pair is flagged for the dates, not banded as 'mesma pessoa'."""
    from sinan_anotador.duplicates import implausible_after
    rows = []
    for i, (notif, sin) in enumerate([("2020-03-01", "2020-02-20"), ("2023-05-10", "2023-05-01"), ("2024-01-15", "1960-01-10"),
                                     ("2024-02-01", "2024-01-25")]):
        rows.append({"NU_NOTIFIC": f"{i:07d}", "NM_PACIENT": "JOAO DA SILVA", "NM_MAE_PAC": "MARIA DA SILVA",
                     "DT_NASC": pd.Timestamp("1990-05-05"), "CS_SEXO": "M", "DT_NOTIFIC": pd.Timestamp(notif),
                     "DT_SIN_PRI": pd.Timestamp(sin), "ID_MUNICIP": "230440", "ID_MN_RESI": "230440", "ID_UNIDADE": "1"})
    df = pd.DataFrame(rows)
    assert implausible_after(df) == (pd.Timestamp("2024-02-01") - pd.Timestamp("2020-03-01")).days + 366
    full, short, st = build_tables(df, list(df.columns), "DengueNET")
    labels = full["tipo_sugerido"].tolist()
    assert any(l.startswith("data implausível? (") and "conferir as datas" in l for l in labels), labels
    assert any(l.startswith("mesma pessoa, ") for l in labels), labels
    assert st["max_days"] == implausible_after(df)
    assert "data implausível?" in st["by_label"]


def test_blank_names_raise_a_warning_in_the_log():
    """MENINNET.DBF (2026-10-28): NM_PACIENT present but blank in every record -> 0 pairs and an AVISO, not silence."""
    df = pd.DataFrame({"NU_NOTIFIC": ["1", "2"], "NM_PACIENT": ["", None], "DT_NASC": [pd.Timestamp("2000-01-01")] * 2,
                       "CS_SEXO": ["F", "F"], "DT_NOTIFIC": [pd.Timestamp("2024-01-01")] * 2})
    log: list[str] = []
    full, short, st = build_tables(df, list(df.columns), "MeningeNET", log)
    assert st["pairs"] == 0 and st["sem_chave"]["sem_nome"] == 2
    assert any(l.startswith("AVISO: NM_PACIENT em branco em 2 de 2 registros") for l in log), log
