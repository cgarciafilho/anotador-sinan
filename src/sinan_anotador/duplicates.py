"""Suspected duplicate notifications: pairs of records that may be the same person, with the key that linked them, the
suggested label (never a decision) and the rule behind it. Definitions: docs/duplicidades_definicoes_manuais.md;
acceptance criterion: METODO.md 2026-10-25.

Keys (names without accents or punctuation, upper case):
  padrao        first + last name + date of birth + sex  — the Sinan NET duplicate report (the simple alternative to beat)
  nome_mae      full name + mother's name (both filled), any date of birth
  nome_nasc1    full name + sex, date of birth differing in one component (day, month or year) or with day/month swapped
  nasc_nome_sim same date of birth + sex, similar name (difflib ratio >= 0.85) — typing error in the name
"""
from __future__ import annotations

import datetime as dt
import re
import unicodedata
from dataclasses import dataclass, field
from difflib import SequenceMatcher
from itertools import combinations

import pandas as pd

SIMILARITY = 0.85
MAX_BLOCK = 50                   # above this many records with the same key, only consecutive records (by date) are paired
GESTATION_WINDOW_DAYS = 45 * 7   # diagnoses more than 45 weeks apart are different pregnancies (METODO 2026-10-26; SES-DF uses 12 months)
TRANSFER_GAP_DAYS = 60           # a treatment that restarts within this many days of the previous closure is "the same treatment"
KEYS = ("padrao", "nome_mae", "nome_nasc1", "nasc_nome_sim")
# acute profile: the days between the two event dates are reported in bands (the sheet keeps the exact number); one log
# line per distinct value made the LEISHNET log 425 lines long (2026-10-28)
INTERVAL_BANDS = ((0, "mesmo dia"), (7, "1 a 7 dias"), (30, "8 a 30 dias"), (90, "31 a 90 dias"), (365, "91 a 365 dias"))
INTERVAL_BAND_LAST = "mais de 365 dias"
IMPLAUSIBLE_MARGIN_DAYS = 366   # an interval longer than the base's own span of notification dates plus this is a typo in a date

RULE_MNR_P23 = "MS, Sinan Normas e Rotinas 2007, p. 23"
RULE_MNR_P24 = "MS, Sinan Normas e Rotinas 2007, p. 24"
RULE_MNR_P26 = "MS, Sinan Normas e Rotinas 2007, p. 26 (homônimos)"
RULE_TB = "MS, Caderno de análise TB 2019, p. 7–9"
RULE_HANS = "MS, Roteiro Sinan Net Hanseníase 2026, p. 28–30"
RULE_SESDF = "SES-DF, NT 10/2020, p. 6 (janela de 45 semanas)"

# TB (Cuabtrfa2.cnv / encerra.cnv) and leprosy (Modoentr.cnv / TPALTA_N dictionary) codes
TB_ENTRY_TRANSFER, TB_ENTRY_REENTRY = {"5"}, {"2", "3"}          # transferência; recidiva, reingresso após abandono
TB_CLOSE_TRANSFER = {"5"}
HANS_ENTRY_TRANSFER, HANS_ENTRY_REENTRY = {"2", "3", "4", "5"}, {"6", "7"}
HANS_CLOSE_TRANSFER = {"2", "3", "4", "5", "9"}


@dataclass
class Profile:
    """Which fields play which role for the agravo."""
    kind: str                              # tb | hans | sifilis_gestante | aids | agudo
    event: str | None                      # date that places the event (first symptoms, diagnosis, accident...)
    entry: str | None = None               # type/mode of entry (TB TRATAMENTO, leprosy MODOENTR)
    closure: str | None = None             # closure/discharge type (TB SITUA_ENCE, leprosy TPALTA_N)
    start: str | None = None               # treatment start date
    end: str | None = None                 # treatment end date
    entry_transfer: set = field(default_factory=set)
    entry_reentry: set = field(default_factory=set)
    close_transfer: set = field(default_factory=set)
    rule: str = RULE_MNR_P23


def detect_profile(def_stem: str | None, columns: list[str]) -> Profile:
    cols = {c.upper() for c in columns}
    stem = (def_stem or "").lower()

    def first(*names):
        return next((n for n in names if n in cols), None)

    if "tubercul" in stem or {"TRATAMENTO", "SITUA_ENCE", "DT_INIC_TR"} <= cols:
        return Profile("tb", first("DT_DIAG", "DT_NOTIFIC"), "TRATAMENTO", "SITUA_ENCE", first("DT_INIC_TR"),
                       first("DT_ENCERRA"), TB_ENTRY_TRANSFER, TB_ENTRY_REENTRY, TB_CLOSE_TRANSFER, RULE_TB)
    if "hans" in stem or {"MODOENTR", "DTINICTRAT"} <= cols:
        return Profile("hans", first("DT_DIAG", "DT_NOTIFIC"), "MODOENTR", first("TPALTA_N", "TIPOALTA_N"),
                       first("DTINICTRAT"), first("DTALTA_N"), HANS_ENTRY_TRANSFER, HANS_ENTRY_REENTRY, HANS_CLOSE_TRANSFER,
                       RULE_HANS)
    if "gestsif" in stem:
        return Profile("sifilis_gestante", first("DT_DIAG", "DT_NOTIFIC"), rule=RULE_SESDF)
    if stem.startswith("aids") or stem.startswith("hiv"):
        return Profile("aids", first("DT_DIAG", "DT_NOTIFIC"), rule=RULE_MNR_P24)
    return Profile("agudo", first("DT_SIN_PRI", "DT_ACID", "DT_OCOR", "DT_DIAG", "DT_NOTIFIC"), rule=RULE_MNR_P23)


# ---------------------------------------------------------------- normalisation
def norm_name(v) -> str:
    if v is None or (isinstance(v, float) and v != v):
        return ""
    s = unicodedata.normalize("NFKD", str(v)).encode("ascii", "ignore").decode().upper()
    s = re.sub(r"[^A-Z ]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def to_date(v) -> dt.date | None:
    if v is None or v is pd.NaT or (isinstance(v, float) and v != v):
        return None
    if isinstance(v, pd.Timestamp):
        return v.date()
    if isinstance(v, dt.datetime):
        return v.date()
    if isinstance(v, dt.date):
        return v
    return None


def code(v) -> str:
    if v is None or (isinstance(v, float) and v != v) or v is pd.NA:
        return ""
    s = str(v).strip()
    return s[:-2] if s.endswith(".0") else s


def birth_one_component_off(a: dt.date, b: dt.date) -> bool:
    """Exactly one of day/month/year differs, or day and month are swapped."""
    if a == b:
        return False
    diff = (a.day != b.day) + (a.month != b.month) + (a.year != b.year)
    if diff == 1:
        return True
    return a.year == b.year and a.day == b.month and a.month == b.day


def similar(a: str, b: str) -> bool:
    if not a or not b or a == b:
        return False
    m = SequenceMatcher(None, a, b)
    return m.real_quick_ratio() >= SIMILARITY and m.quick_ratio() >= SIMILARITY and m.ratio() >= SIMILARITY


# ---------------------------------------------------------------- pairing
def _pairs_in_block(idx: list[int], order: dict[int, tuple]) -> list[tuple[int, int]]:
    if len(idx) <= MAX_BLOCK:
        return [(i, j) for i, j in combinations(idx, 2)]
    s = sorted(idx, key=lambda i: order[i])
    return list(zip(s, s[1:]))


def find_pairs(df: pd.DataFrame, log: list[str] | None = None, stats: dict | None = None) -> dict[tuple[int, int], set[str]]:
    """Index pairs (i < j, positional) -> set of key names that linked them. Needs NM_PACIENT, DT_NASC, CS_SEXO; NM_MAE_PAC
    is optional (nome_mae is skipped without it). `stats`, when given, receives the records no key can reach."""
    log = log if log is not None else []
    n = len(df)
    nome = [norm_name(v) for v in df["NM_PACIENT"]] if "NM_PACIENT" in df else [""] * n
    mae = [norm_name(v) for v in df["NM_MAE_PAC"]] if "NM_MAE_PAC" in df else [""] * n
    nasc = [to_date(v) for v in df["DT_NASC"]] if "DT_NASC" in df else [None] * n
    sexo = [code(v).upper()[:1] for v in df["CS_SEXO"]] if "CS_SEXO" in df else [""] * n
    notif = [to_date(v) for v in df["DT_NOTIFIC"]] if "DT_NOTIFIC" in df else [None] * n
    order = {i: (notif[i] or dt.date.max, i) for i in range(n)}
    pairs: dict[tuple[int, int], set[str]] = {}
    if stats is not None:   # records no key can reach, by cause (a record may count in more than one cause)
        no_name = sum(1 for i in range(n) if not nome[i])
        one_token = sum(1 for i in range(n) if len(nome[i].split()) == 1)
        no_birth = sum(1 for i in range(n) if nome[i] and nasc[i] is None)
        no_sex = sum(1 for i in range(n) if nome[i] and not sexo[i])
        no_mother = sum(1 for i in range(n) if nome[i] and not mae[i])
        unreachable = sum(1 for i in range(n) if not nome[i] or (nasc[i] is None and not mae[i]))
        stats["sem_chave"] = {"sem_nome": no_name, "nome_de_uma_palavra": one_token, "sem_nascimento": no_birth, "sem_sexo": no_sex,
                              "sem_mae": no_mother, "fora_de_toda_chave": unreachable}
        if n and no_name * 2 >= n:
            # MENINNET.DBF (2026-10-28): NM_PACIENT present but blank in all 5,902 records; every key needs the name
            log.append(f"AVISO: NM_PACIENT em branco em {no_name} de {n} registros; sem o nome nenhuma chave de duplicidade "
                       f"funciona. Confira se o DBF foi exportado sem os dados de identificação do paciente")

    def add(i, j, key):
        if i == j:
            return
        a, b = (i, j) if i < j else (j, i)
        pairs.setdefault((a, b), set()).add(key)

    # padrao: first + last name + birth + sex
    blocks: dict[tuple, list[int]] = {}
    for i in range(n):
        toks = nome[i].split()
        if len(toks) < 2 or nasc[i] is None:
            continue
        blocks.setdefault((toks[0], toks[-1], nasc[i], sexo[i]), []).append(i)
    big = 0
    for idx in blocks.values():
        if len(idx) > 1:
            big += len(idx) > MAX_BLOCK
            for i, j in _pairs_in_block(idx, order):
                add(i, j, "padrao")
    if big:
        log.append(f"AVISO: {big} grupos com mais de {MAX_BLOCK} registros na chave padrao; neles só registros consecutivos por data foram pareados")

    # nome_mae: full name + mother's name
    if "NM_MAE_PAC" in df:
        blocks = {}
        for i in range(n):
            if nome[i] and mae[i]:
                blocks.setdefault((nome[i], mae[i]), []).append(i)
        for idx in blocks.values():
            if len(idx) > 1:
                for i, j in _pairs_in_block(idx, order):
                    add(i, j, "nome_mae")

    # nome_nasc1: full name + sex, birth one component off
    blocks = {}
    for i in range(n):
        if nome[i] and nasc[i] is not None:
            blocks.setdefault((nome[i], sexo[i]), []).append(i)
    for idx in blocks.values():
        if 1 < len(idx) <= MAX_BLOCK:
            for i, j in combinations(idx, 2):
                if birth_one_component_off(nasc[i], nasc[j]):
                    add(i, j, "nome_nasc1")

    # nasc_nome_sim: same birth + sex, similar full name (sharing the first or the last token, to keep it cheap)
    blocks = {}
    for i in range(n):
        if nome[i] and nasc[i] is not None:
            blocks.setdefault((nasc[i], sexo[i]), []).append(i)
    for idx in blocks.values():
        if 1 < len(idx) <= MAX_BLOCK:
            for i, j in combinations(idx, 2):
                if nome[i] == nome[j]:
                    continue
                ti, tj = nome[i].split(), nome[j].split()
                if (ti[0] == tj[0] or ti[-1] == tj[-1]) and similar(nome[i], nome[j]):
                    add(i, j, "nasc_nome_sim")
    return pairs


# ---------------------------------------------------------------- classification
def _overlap(a_start, a_end, b_start, b_end) -> bool | None:
    """Do two treatment intervals overlap? None when neither start is known."""
    if a_start is None or b_start is None:
        return None
    if b_start < a_start:
        a_start, a_end, b_start, b_end = b_start, b_end, a_start, a_end
    return a_end is None or (b_start - a_end).days <= TRANSFER_GAP_DAYS


def _gestation(row: pd.Series) -> str:
    """CS_GESTANT as its gestante.cnv label ("1º trimestre", "idade gestacional ignorada"), never the bare code."""
    label = code(row.get("CS_GESTANT_rotulo"))
    if label:
        return label.lower()
    c = code(row.get("CS_GESTANT"))
    return f"código {c}" if c else "em branco"


def _days(a: dt.date | None, b: dt.date | None) -> int | None:
    return None if a is None or b is None else abs((b - a).days)


def interval_band(days: int) -> str:
    for hi, name in INTERVAL_BANDS:
        if days <= hi:
            return name
    return INTERVAL_BAND_LAST


def implausible_after(df: pd.DataFrame) -> int | None:
    """Days beyond which an interval between two event dates cannot be real: the span of DT_NOTIFIC in the base plus
    IMPLAUSIBLE_MARGIN_DAYS (symptoms may precede the first notification by months, not by decades)."""
    if "DT_NOTIFIC" not in df.columns:
        return None
    dates = [d for d in (to_date(v) for v in df["DT_NOTIFIC"]) if d is not None]
    if not dates:
        return None
    return (max(dates) - min(dates)).days + IMPLAUSIBLE_MARGIN_DAYS


def classify(a: pd.Series, b: pd.Series, prof: Profile, same_unit: bool, mother: str,
             max_days: int | None = None) -> tuple[str, str]:
    """(suggested label, rule). `mother` is 'igual', 'diferente' or '' (not comparable). `max_days` (acute profile): an
    interval above it is flagged as a date error instead of being banded (see implausible_after)."""
    if mother == "diferente":
        return "homônimo? (nome da mãe diferente)", RULE_MNR_P26
    ev_a, ev_b = to_date(a.get(prof.event)) if prof.event else None, to_date(b.get(prof.event)) if prof.event else None
    days = _days(ev_a, ev_b)
    if prof.kind in ("tb", "hans"):
        ent_a, ent_b = code(a.get(prof.entry)), code(b.get(prof.entry))
        clo_a = code(a.get(prof.closure)) if prof.closure else ""
        s_a = to_date(a.get(prof.start)) if prof.start else None
        s_b = to_date(b.get(prof.start)) if prof.start else None
        e_a = to_date(a.get(prof.end)) if prof.end else None
        e_b = to_date(b.get(prof.end)) if prof.end else None
        ov = _overlap(s_a or ev_a, e_a, s_b or ev_b, e_b)
        if ent_b in prof.entry_reentry:
            return "recidiva/reingresso (tratamentos diferentes; não listar)", prof.rule
        if ov is False:
            return "recidiva/reingresso? (tratamentos não se sobrepõem; não listar)", prof.rule
        if same_unit and ent_a == ent_b:
            return "duplicidade verdadeira? (mesma unidade, mesma entrada, mesmo tratamento)", prof.rule
        if not same_unit and (clo_a in prof.close_transfer or ent_b in prof.entry_transfer):
            return "duplo registro por transferência (vincular)", prof.rule
        if not same_unit:
            return "duplo registro: transferência? (sem saída/entrada 'transferência' registrada)", prof.rule
        return "mesma unidade, mesmo período, entrada diferente: conferir", prof.rule
    if prof.kind == "sifilis_gestante":
        if days is None:
            return "mesma pessoa; sem data de diagnóstico para comparar", prof.rule
        if days > GESTATION_WINDOW_DAYS:
            return f"gestação diferente ({days} dias entre diagnósticos, > 45 semanas)", prof.rule
        return f"mesma gestação? ({days} dias entre diagnósticos, ≤ 45 semanas; gestação: {_gestation(a)} / {_gestation(b)})", prof.rule
    if prof.kind == "aids":
        return "possível duplicidade (qualquer período)", prof.rule
    if days is None:
        return "mesma pessoa; sem data do evento para comparar", prof.rule
    if max_days is not None and days > max_days:
        return (f"data implausível? ({days} dias entre eventos, {prof.event}; maior que o período coberto pela base: "
                f"conferir as datas)"), prof.rule
    return f"mesma pessoa, {interval_band(days)} ({days} dias entre eventos, {prof.event}): duplicidade se for o mesmo evento", prof.rule


def _completeness(row: pd.Series, columns: list[str]) -> int:
    return sum(1 for c in columns if code(row.get(c)) != "")


def _mother_status(a, b) -> str:
    ma, mb = norm_name(a.get("NM_MAE_PAC")), norm_name(b.get("NM_MAE_PAC"))
    if not ma or not mb:
        return ""
    if ma == mb or similar(ma, mb):
        return "igual"
    return "diferente"


def _keep(a: pd.Series, b: pd.Series) -> tuple[str, str]:
    """Which record the MS rule keeps: the earlier notification; tie -> the one notified by the municipality of residence."""
    da, db = to_date(a.get("DT_NOTIFIC")), to_date(b.get("DT_NOTIFIC"))
    if da is not None and db is not None and da != db:
        return ("A" if da < db else "B"), "notificação mais antiga"
    ra = code(a.get("ID_MUNICIP")) and code(a.get("ID_MUNICIP")) == code(a.get("ID_MN_RESI"))
    rb = code(b.get("ID_MUNICIP")) and code(b.get("ID_MUNICIP")) == code(b.get("ID_MN_RESI"))
    if ra != rb:
        return ("A" if ra else "B"), "mesma data; notificada pelo município de residência"
    return "A", "mesma data; sem desempate pela residência (primeira na ordem do arquivo)"


def load_ads(path) -> dict[str, tuple[str, str]]:
    """Municipality (6-digit IBGE code) -> (ADS, SR) from the SESA-CE regionalisation list (tabelas/regionalizacao_sesa_sr_ads.csv,
    built from the SESA sheet of 2022-03-02; 184 municipalities, 22 ADS, 5 SR). Empty dict when the file is missing."""
    import csv
    out: dict[str, tuple[str, str]] = {}
    try:
        with open(path, encoding="utf-8", newline="") as fh:
            for row in csv.DictReader(fh):
                out[row["cod6"].strip()] = (row["ads"].strip(), row["sr"].strip())
    except (OSError, KeyError):
        return {}
    return out


def _ads(row, col: str, ads: dict[str, tuple[str, str]]):
    """ADS of the municipality in `col`; falls back to the Sinan regional label (ID_REGIONA/ID_RG_RESI) when the table lacks it
    (a base from another state). None when the regional code is blank or has no label: the blank label ("Ign/Branco") is not a
    regional (METODO 2026-10-28)."""
    c = code(row.get(col))[:6]
    if c in ads:
        return ads[c][0]
    reg = {"ID_MUNICIP": "ID_REGIONA", "ID_MN_RESI": "ID_RG_RESI"}.get(col)
    if not reg or not code(row.get(reg)):
        return None
    v = _value(row, f"{reg}_rotulo")
    return v if isinstance(v, str) and not v.endswith("sem rótulo") else None


ID_FIELDS = ["NU_NOTIFIC", "DT_NOTIFIC", "NM_PACIENT", "DT_NASC", "CS_SEXO", "NM_MAE_PAC", "ID_MUNICIP", "ID_UNIDADE",
             "ID_MN_RESI", "NDUPLIC_N", "IN_VINCULA"]


def _value(row, col):
    v = row.get(col)
    return None if v is None or v is pd.NA or (isinstance(v, float) and v != v) else v


def build_tables(df: pd.DataFrame, raw_columns: list[str], def_stem: str | None, log: list[str] | None = None,
                 ads: dict[str, tuple[str, str]] | None = None) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    """Return (complete sheet, short sheet, stats). `df` is the annotated table (with `_rotulo` columns); `ads` maps the
    municipality code to (ADS, SR) so the short sheet can be split by the regional that follows the case."""
    log = log if log is not None else []
    ads = ads or {}
    prof = detect_profile(def_stem, raw_columns)
    stats: dict = {}
    pairs = find_pairs(df, log, stats)
    side_fields = [c for c in ID_FIELDS if c in df.columns]
    for c in [prof.event, prof.entry, prof.closure, prof.start, prof.end, "CS_GESTANT" if prof.kind == "sifilis_gestante" else None]:
        if c and c in df.columns and c not in side_fields:
            side_fields.append(c)
    rows, short = [], []
    max_days = implausible_after(df) if prof.kind == "agudo" else None
    stats.update({"pairs": len(pairs), "by_key": {k: 0 for k in KEYS}, "by_label": {}, "judged": 0, "profile": prof.kind,
                  "max_days": max_days})
    ordered = sorted(pairs.items(), key=lambda kv: (to_date(df.iloc[kv[0][0]].get("DT_NOTIFIC")) or dt.date.max, kv[0]))
    for n, ((i, j), keys) in enumerate(ordered, 1):
        a, b = df.iloc[i], df.iloc[j]
        da, db = to_date(a.get("DT_NOTIFIC")), to_date(b.get("DT_NOTIFIC"))
        if da is not None and db is not None and db < da:
            a, b, i, j = b, a, j, i
        same_unit = code(a.get("ID_UNIDADE")) != "" and code(a.get("ID_UNIDADE")) == code(b.get("ID_UNIDADE"))
        same_mun = code(a.get("ID_MUNICIP")) != "" and code(a.get("ID_MUNICIP")) == code(b.get("ID_MUNICIP"))
        mother = _mother_status(a, b)
        label, rule = classify(a, b, prof, same_unit, mother, max_days)
        judged = any(code(r.get(f)) in {"1", "2"} for r in (a, b) for f in ("NDUPLIC_N",)) or \
            any(code(r.get("IN_VINCULA")) == "1" for r in (a, b))
        keep, why = _keep(a, b)
        ev_a, ev_b = (to_date(a.get(prof.event)), to_date(b.get(prof.event))) if prof.event else (None, None)
        days = _days(ev_a, ev_b)
        for k in keys:
            stats["by_key"][k] += 1
        stats["by_label"][label.split(" (")[0]] = stats["by_label"].get(label.split(" (")[0], 0) + 1
        stats["judged"] += judged
        keep_row = a if keep == "A" else b
        ads_na, ads_nb = _ads(a, "ID_MUNICIP", ads), _ads(b, "ID_MUNICIP", ads)
        ads_ra, ads_rb = _ads(a, "ID_MN_RESI", ads), _ads(b, "ID_MN_RESI", ads)
        ads_res = ads_ra if ads_ra == ads_rb or ads_rb is None else (f"{ads_ra} / {ads_rb}" if ads_ra else ads_rb)
        stats["ads_missing"] = stats.get("ads_missing", 0) + (ads_na is None) + (ads_nb is None)
        rec = {"par": n, "chaves": "+".join(k for k in KEYS if k in keys), "tipo_sugerido": label, "regra": rule,
               "ja_julgado_no_sinan": "sim" if judged else "não",
               "ADS_notificacao_A": ads_na, "ADS_notificacao_B": ads_nb, "ADS_residencia_A": ads_ra, "ADS_residencia_B": ads_rb,
               "dias_entre_eventos": days, "campo_do_evento": prof.event or "",
               "mesma_unidade": "sim" if same_unit else "não", "mesmo_municipio_notif": "sim" if same_mun else "não",
               "nome_da_mae": mother or "não comparável",
               "ficha_sugerida_manter": _value(keep_row, "NU_NOTIFIC"), "motivo_ficha_sugerida": f"{why} ({RULE_MNR_P24})",
               "completude_A": _completeness(a, raw_columns), "completude_B": _completeness(b, raw_columns)}
        for side, r in (("A", a), ("B", b)):
            for c in side_fields:
                rec[f"{c}_{side}"] = _value(r, c)
                if f"{c}_rotulo" in df.columns:
                    rec[f"{c}_rotulo_{side}"] = _value(r, f"{c}_rotulo")
        rows.append(rec)

        def place(r):
            u = _value(r, "ID_UNIDADE_rotulo") or _value(r, "ID_UNIDADE")
            m = _value(r, "ID_MUNICIP_rotulo") or _value(r, "ID_MUNICIP")
            return u, m
        ua, ma_ = place(a)
        ub, mb_ = place(b)
        short.append({"par": n, "ADS_notificacao_A": ads_na, "ADS_notificacao_B": ads_nb, "ADS_residencia": ads_res,
                      "tipo_sugerido": label, "ja_julgado_no_sinan": "sim" if judged else "não",
                      "dias_entre_eventos": days, "paciente": _value(a, "NM_PACIENT"), "nascimento": _value(a, "DT_NASC"),
                      "notificacao_A": _value(a, "NU_NOTIFIC"), "data_A": _value(a, "DT_NOTIFIC"), "unidade_A": ua, "municipio_A": ma_,
                      "notificacao_B": _value(b, "NU_NOTIFIC"), "data_B": _value(b, "DT_NOTIFIC"), "unidade_B": ub, "municipio_B": mb_,
                      "ficha_sugerida_manter": _value(keep_row, "NU_NOTIFIC"), "decisao_da_equipe": None, "observacao": None})
    full_cols = list(rows[0].keys()) if rows else ["par", "chaves", "tipo_sugerido", "regra"]
    short_cols = list(short[0].keys()) if short else ["par", "tipo_sugerido"]
    full_df, short_df = pd.DataFrame(rows, columns=full_cols), pd.DataFrame(short, columns=short_cols)
    if rows:   # grouped by the ADS that digitised the first notification, then by date: the order a regional reads it in
        order = sorted(range(len(rows)), key=lambda k: (rows[k]["ADS_notificacao_A"] or "~", to_date(rows[k]["DT_NOTIFIC_A"]) or dt.date.max, k))
        full_df, short_df = full_df.iloc[order].reset_index(drop=True), short_df.iloc[order].reset_index(drop=True)
    return full_df, short_df, stats
