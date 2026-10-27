"""Synthetic DBF with planted duplicate pairs of known type (METODO 2026-10-25, acceptance criterion of `duplicidades`).

Background: unique people (unique last token in the name, so no accidental pairs). Planted on top, per type:
  exata        same identity, second notification days later (TB/leprosy: same unit, same entry, same treatment)
  erro_nome    one letter changed in the first name (last name kept)          -> nasc_nome_sim (+ nome_mae)
  nasc_1comp   date of birth with one component changed or day/month swapped -> nome_nasc1 (+ nome_mae)
  mae_branco   mother's name blank in one record                              -> padrao only
  homonimo     same name, birth and sex; different mother and municipality   -> padrao; label "homônimo?"
  transferencia (TB/leprosy) unit differs, closure/entry "transferência"     -> label "duplo registro por transferência"
  recidiva      (TB/leprosy) entry recidiva, months after the closure         -> label "recidiva/reingresso"
  gest_dif / gest_mesma (gestante): diagnoses > 315 / <= 315 days (45 weeks) apart
  julgado      exact duplicate with NDUPLIC_N = 1 in one record               -> section "já julgado"
"""
from __future__ import annotations

import datetime as dt
import random
from pathlib import Path

from dbf_writer import write_dbf
from synthetic import FIRST, LAST, make_synthetic

MOTHERS = ["RITA", "JOANA", "TEREZA", "LUZIA", "RAIMUNDA", "ANTÔNIA", "SOCORRO", "FÁTIMA"]
UNITS = ["2529068", "2561492", "2374471", "6677657", "2611570"]
MUNS = ["230440", "230650", "231290", "230190", "230370"]
EXTRA_FIELDS = [("NM_MAE_PAC", "C", 30, 0), ("DT_NASC", "D", 8, 0), ("NDUPLIC_N", "C", 1, 0), ("IN_VINCULA", "C", 1, 0)]
PER_TYPE = 10


def letters(n: int) -> str:
    s = ""
    n += 1
    while n:
        n, r = divmod(n - 1, 26)
        s = chr(65 + r) + s
    return s


def make_synthetic_dups(deffile, tab_dir: Path, out: Path, stem: str, n_background: int = 200, seed: int = 11,
                        encoding: str = "cp850") -> tuple[Path, dict]:
    kind = {"TUBENET": "tb", "HANSNET": "hans", "SIFGENET": "gest"}.get(stem, "agudo")
    rng = random.Random(seed)
    tmp = out.with_name(out.stem + "_bg.DBF")
    _, base = make_synthetic(deffile, tab_dir, tmp, n=n_background, seed=seed, encoding=encoding)
    spec = list(base["spec"])
    names = {s[0] for s in spec}
    for f in EXTRA_FIELDS:
        if f[0] not in names:
            spec.append(f)
    if kind == "hans":
        for f in [("TPALTA_N", "C", 1, 0), ("DTALTA_N", "D", 8, 0)]:
            if f[0] not in names:
                spec.append(f)
    fields = {s[0] for s in spec}
    records = []
    for k, rec in enumerate(base["records"]):
        rec = dict(rec)
        rec["NM_PACIENT"] = f"{rng.choice(FIRST)} {rng.choice(LAST)} {letters(k)}"
        rec["NM_MAE_PAC"] = f"{rng.choice(MOTHERS)} {rng.choice(LAST)}"
        rec["DT_NASC"] = dt.date(rng.randint(1940, 2015), rng.randint(1, 12), rng.randint(1, 28))
        rec["CS_SEXO"] = rng.choice(["M", "F"]) if kind != "gest" else "F"
        rec["NDUPLIC_N"] = ""
        rec["IN_VINCULA"] = ""
        if "ID_UNIDADE" in fields:
            rec["ID_UNIDADE"] = rng.choice(UNITS)
        if "ID_MUNICIP" in fields:
            rec["ID_MUNICIP"] = rng.choice(MUNS)
        if "ID_MN_RESI" in fields:
            rec["ID_MN_RESI"] = rec.get("ID_MUNICIP") if rng.random() < 0.7 else rng.choice(MUNS)
        rec["DT_NOTIFIC"] = dt.date(rng.choice([2019, 2020, 2021]), rng.randint(1, 12), rng.randint(1, 28))
        diag = rec["DT_NOTIFIC"] - dt.timedelta(days=rng.randint(0, 20))
        if kind == "tb":
            rec.update(DT_DIAG=diag, DT_INIC_TR=diag + dt.timedelta(days=rng.randint(0, 5)), TRATAMENTO="1", SITUA_ENCE="1",
                       DT_ENCERRA=diag + dt.timedelta(days=rng.randint(180, 240)))
        elif kind == "hans":
            rec.update(DT_DIAG=diag, DTINICTRAT=diag + dt.timedelta(days=rng.randint(0, 5)), MODOENTR="1", TPALTA_N="1",
                       DTALTA_N=diag + dt.timedelta(days=rng.randint(180, 400)))
        elif kind == "gest":
            rec.update(DT_DIAG=diag, CS_GESTANT=rng.choice(["1", "2", "3"]), CLASSI_FIN="1")
        else:
            rec["DT_SIN_PRI"] = diag
        records.append(rec)
    n0 = len(records)
    truth: list[dict] = []
    counter = [n0]

    def clone(src: dict, **changes) -> dict:
        counter[0] += 1
        rec = dict(src)
        rec["NU_NOTIFIC"] = f"{counter[0]:07d}"
        rec["DT_NOTIFIC"] = src["DT_NOTIFIC"] + dt.timedelta(days=rng.randint(1, 10))
        rec.update(changes)
        records.append(rec)
        return rec

    def plant(tipo, src, b, keys, label_prefix, nduplic=None):
        if nduplic:
            b["NDUPLIC_N"] = nduplic
        truth.append({"tipo": tipo, "a": src["NU_NOTIFIC"], "b": b["NU_NOTIFIC"], "keys": set(keys), "label": label_prefix})

    pool = rng.sample(records[:n0], 9 * PER_TYPE)
    lab_exact = {"tb": "duplicidade verdadeira?", "hans": "duplicidade verdadeira?", "gest": "mesma gestação?",
                 "agudo": "mesma pessoa,"}[kind]
    it = iter(pool)
    for _ in range(PER_TYPE):                                   # exata
        src = next(it)
        plant("exata", src, clone(src), {"padrao", "nome_mae"}, lab_exact)
    for _ in range(PER_TYPE):                                   # erro_nome: change one letter of the first name
        src = next(it)
        first, rest = src["NM_PACIENT"].split(" ", 1)
        pos = rng.randrange(1, len(first))
        new = first[:pos] + ("X" if first[pos] != "X" else "Y") + first[pos + 1:]
        plant("erro_nome", src, clone(src, NM_PACIENT=f"{new} {rest}"), {"nasc_nome_sim", "nome_mae"}, lab_exact)
    for _ in range(PER_TYPE):                                   # nasc_1comp
        src = next(it)
        d = src["DT_NASC"]
        mode = rng.choice(["dia", "mes", "ano", "troca"])
        if mode == "dia":
            nd = d.replace(day=d.day + 1 if d.day < 28 else d.day - 1)
        elif mode == "mes":
            nd = d.replace(month=d.month + 1 if d.month < 12 else d.month - 1)
        elif mode == "ano":
            nd = d.replace(year=d.year + 1)
        else:
            nd = d.replace(day=d.month, month=d.day) if d.month <= 28 and d.day <= 12 and d.day != d.month else d.replace(year=d.year - 1)
        plant("nasc_1comp", src, clone(src, DT_NASC=nd), {"nome_nasc1", "nome_mae"}, lab_exact)
    for _ in range(PER_TYPE):                                   # mae_branco
        src = next(it)
        plant("mae_branco", src, clone(src, NM_MAE_PAC=""), {"padrao"}, lab_exact)
    for k in range(PER_TYPE):                                   # homonimo
        src = next(it)
        other_mother = f"{rng.choice([m for m in MOTHERS if not src['NM_MAE_PAC'].startswith(m)])} {rng.choice(LAST)}"
        other_mun = rng.choice([m for m in MUNS if m != src.get("ID_MUNICIP")])
        changes = dict(NM_MAE_PAC=other_mother)
        if "ID_MUNICIP" in fields:
            changes.update(ID_MUNICIP=other_mun, ID_MN_RESI=other_mun)
        if kind == "tb":
            changes.update(DT_DIAG=src["DT_DIAG"] + dt.timedelta(days=rng.randint(30, 300)))
        b = clone(src, **changes)
        plant("homonimo", src, b, {"padrao"}, "homônimo?", nduplic="1" if k % 2 == 0 else None)
    for _ in range(PER_TYPE):                                   # julgado: exact duplicate already marked "não listar"
        src = next(it)
        plant("julgado", src, clone(src, NDUPLIC_N="1"), {"padrao", "nome_mae"}, lab_exact)
    if kind in ("tb", "hans"):
        for _ in range(PER_TYPE):                               # transferencia
            src = next(it)
            unit = rng.choice([u for u in UNITS if u != src["ID_UNIDADE"]])
            end = src["DT_DIAG"] + dt.timedelta(days=rng.randint(30, 120))
            if kind == "tb":
                src.update(SITUA_ENCE="5", DT_ENCERRA=end)
                b = clone(src, ID_UNIDADE=unit, TRATAMENTO="5", SITUA_ENCE="1", DT_INIC_TR=end + dt.timedelta(days=rng.randint(0, 30)),
                          DT_ENCERRA=end + dt.timedelta(days=150), DT_NOTIFIC=end + dt.timedelta(days=rng.randint(0, 30)))
            else:
                src.update(TPALTA_N="3", DTALTA_N=end)
                b = clone(src, ID_UNIDADE=unit, MODOENTR="3", TPALTA_N="1", DTINICTRAT=end + dt.timedelta(days=rng.randint(0, 30)),
                          DTALTA_N=end + dt.timedelta(days=300), DT_NOTIFIC=end + dt.timedelta(days=rng.randint(0, 30)))
            plant("transferencia", src, b, {"padrao", "nome_mae"}, "duplo registro por transferência")
        for _ in range(PER_TYPE):                               # recidiva
            src = next(it)
            end = src["DT_ENCERRA"] if kind == "tb" else src["DTALTA_N"]
            new_diag = end + dt.timedelta(days=rng.randint(200, 600))
            if kind == "tb":
                b = clone(src, TRATAMENTO="2", DT_DIAG=new_diag, DT_INIC_TR=new_diag, DT_ENCERRA=None, DT_NOTIFIC=new_diag,
                          ID_UNIDADE=rng.choice(UNITS))
            else:
                b = clone(src, MODOENTR="6", DT_DIAG=new_diag, DTINICTRAT=new_diag, DTALTA_N=None, DT_NOTIFIC=new_diag,
                          ID_UNIDADE=rng.choice(UNITS))
            plant("recidiva", src, b, {"padrao", "nome_mae"}, "recidiva/reingresso")
    elif kind == "gest":
        for _ in range(PER_TYPE):                               # gest_dif
            src = next(it)
            nd = src["DT_DIAG"] + dt.timedelta(days=rng.randint(400, 800))
            plant("gest_dif", src, clone(src, DT_DIAG=nd, DT_NOTIFIC=nd + dt.timedelta(days=2)), {"padrao", "nome_mae"}, "gestação diferente")
        for _ in range(PER_TYPE):                               # gest_mesma
            src = next(it)
            nd = src["DT_DIAG"] + dt.timedelta(days=rng.randint(10, 200))
            plant("gest_mesma", src, clone(src, DT_DIAG=nd, DT_NOTIFIC=nd + dt.timedelta(days=2)), {"padrao", "nome_mae"}, "mesma gestação?")
    rng.shuffle(records)
    write_dbf(out, spec, records, encoding=encoding)
    tmp.unlink(missing_ok=True)
    planted_ids = {t["a"] for t in truth} | {t["b"] for t in truth}
    return out, {"truth": truth, "n": len(records), "kind": kind, "planted_ids": planted_ids,
                 "person_of": {**{t["a"]: t["a"] for t in truth}, **{t["b"]: t["a"] for t in truth}}}
