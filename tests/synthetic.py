"""Synthetic Sinan NET DBF with known truth, built from a .def (no real data; names and codes are drawn at random).

For every field that the .def ties to an available category table the generator draws, per record, a code from a
category line (80%), a blank (10%) or a code outside every table (10%), and records the expected label. The expected
label is computed here with a small independent rule (last category line whose code list covers the code; blank line
label or 'Ign/Branco' for blanks; '[code] sem rótulo' outside), not with the package's lookup.
"""
from __future__ import annotations

import datetime as dt
import random
import re
from collections import Counter
from pathlib import Path

from dbf_writer import write_dbf
from sinan_anotador.annotate import AGE_FIELD, build_plan
from sinan_anotador.cnv import Cnv, DefFile
from sinan_anotador.lookup import LookupTable

FIRST = ["ANA", "JOSÉ", "MARIA", "JOÃO", "ANTÔNIO", "FRANCISCA", "SEBASTIÃO", "CONCEIÇÃO", "LUÍS", "ÚRSULA"]
LAST = ["DA SILVA", "DE SOUSA", "ARAÚJO", "GONÇALVES", "ASSUNÇÃO", "FERREIRA", "DOS ANJOS", "MACÊDO"]


def covers(token: str, code: str) -> bool:
    token = token.strip()
    if token == "":
        return code == ""
    if re.fullmatch(r"\d+-\d+", token) and code.isdigit():
        a, b = token.split("-")
        return int(a) <= int(code) <= int(b)
    if token.isdigit() and code.isdigit():
        return int(token) == int(code)
    return token == code


def expected_label(code: str, tables: list) -> str:
    """Independent re-implementation of the TabWin rule: within a table the last covering line wins; tables are
    tried in order (CE then BR for municipalities); blank -> table blank line or Ign/Branco; else '[code] sem rótulo'.
    External lookup tables (unidanet.dbf) are plain code -> name maps: exact code, tried in chain order."""
    if isinstance(tables[0], LookupTable):
        if code == "":
            return "Ign/Branco"
        for t in tables:
            lab = t._exact.get(code)
            if lab is not None:
                return lab
        return f"[{code}] sem rótulo"
    if code == "":
        # blank: the main table's own blank line (an empty token that is not just a trailing comma), last one wins;
        # else the criterion-3 default. Fallback tables are not consulted for blanks.
        found = None
        for codes, label in tables[0].categories:
            toks = [t.strip() for t in codes.split(",")]
            if len(toks) > 1 and toks[-1] == "" and any(toks[:-1]):
                toks = toks[:-1]
            if "" in toks:
                found = label
        return found if found is not None else "Ign/Branco"
    for t in tables:
        found = None
        for codes, label in t.categories:
            if any(covers(tok, code) for tok in codes.split(",")):
                found = label
        if found is not None:
            # municipality (Munic??.cnv) and UF (UFcodigo.cnv) labels drop the leading code: "230650 Itapiúna" -> "Itapiúna"
            if re.match(r"^munic[a-z]{2}\.cnv$", t.name.lower()) or t.name.lower() in ("ufcodigo.cnv", "ufccodig.cnv"):
                parts = found.split(None, 1)
                if len(parts) == 2 and parts[0].isdigit() and len(parts[0]) >= 2:
                    found = parts[1]
            return found
    return f"[{code}] sem rótulo"


def code_from_line(codes: str, rng: random.Random, width: int) -> str | None:
    toks = [t.strip() for t in codes.split(",") if t.strip()]
    if not toks:
        return None
    # only codes that fit the DBF field width (a C(1) field cannot hold "12" from a `00-99` range)
    toks = [t for t in toks if not re.fullmatch(r"\d+-\d+", t) and len(t) <= width
            or re.fullmatch(r"\d+-\d+", t) and int(t.split("-")[0]) <= 10 ** width - 1]
    if not toks:
        return None
    tok = rng.choice(toks)
    if re.fullmatch(r"\d+-\d+", tok):
        a, b = tok.split("-")
        hi = min(int(b), int(a) + 50, 10 ** width - 1)
        n = rng.randint(int(a), hi)
        return str(n).zfill(min(len(a), width))
    return tok


def outside_code(tables: list, width: int, rng: random.Random) -> str:
    for cand in ["Z" * max(1, width), "ZZ"[:max(1, width)], "9" * max(1, width), "X"]:
        if expected_label(cand, tables).endswith("sem rótulo"):
            return cand
    raise RuntimeError("no outside code found")


def make_synthetic(deffile: DefFile, tab_dir: Path, out: Path, n: int = 300, seed: int = 1, encoding: str = "cp850",
                   years=(2019, 2020, 2021)) -> tuple[Path, dict]:
    rng = random.Random(seed)
    fields_def = sorted(deffile.fields)
    types = {f: ("D" if f.startswith("DT_") else "N" if f == AGE_FIELD else "C") for f in fields_def}
    plan = build_plan(deffile, fields_def, types, tab_dir)
    spec: list[tuple[str, str, int, int]] = [("NU_NOTIFIC", "C", 7, 0), ("NM_PACIENT", "C", 30, 0)]
    for f in fields_def:
        if f in ("NU_NOTIFIC", "NM_PACIENT"):
            continue
        if types[f] == "D":
            spec.append((f, "D", 8, 0))
        elif f == AGE_FIELD:
            spec.append((f, "N", 4, 0))
        elif f in plan.fields and isinstance(plan.fields[f].cnv, LookupTable):
            spec.append((f, "C", max((len(c) for c in list(plan.fields[f].cnv._exact)[:500]), default=7), 0))
        elif f in plan.fields:
            spec.append((f, "C", max(plan.fields[f].cnv.width, 1), 0))
        else:
            spec.append((f, "C", 7, 0))
    widths = {s[0]: s[2] for s in spec}
    truth: dict[str, Counter] = {}
    truth_age: Counter = Counter()
    truth_dates: list = []
    records = []
    for i in range(n):
        rec = {"NU_NOTIFIC": f"{i + 1:07d}", "NM_PACIENT": f"{rng.choice(FIRST)} {rng.choice(LAST)}"}
        deferred: list[tuple[str, str]] = []
        for f in fields_def:
            if f in rec:
                continue
            if types[f] == "D":
                if rng.random() < 0.1:
                    rec[f] = None
                else:
                    rec[f] = dt.date(rng.choice(years), rng.randint(1, 12), rng.randint(1, 28))
                if f == "DT_NOTIFIC":
                    truth_dates.append(rec[f])
                continue
            if f == AGE_FIELD:
                r = rng.random()
                if r < 0.1:
                    code = ""
                elif r < 0.2:
                    code = rng.choice(["9999", "4600", "1"])      # N(4): leading zeros do not survive the DBF
                else:
                    code = str(rng.choice([rng.randint(4000, 4110), rng.randint(3000, 3011), rng.randint(2000, 2030),
                                           rng.randint(1000, 1024)]))
                rec[f] = int(code) if code else None
                tables = [plan.age_band] if plan.age_band else []
                lab = expected_label(code, tables) if tables else None
                n_code = int(code) if code else None
                anos = (n_code - 4000 if n_code is not None and 4000 <= n_code <= 4999
                        else 0 if n_code is not None and 1000 <= n_code <= 3999 else None)
                truth_age[(lab, anos)] += 1
                continue
            fp = plan.fields.get(f)
            if fp is None:
                rec[f] = rng.choice(["", "1", "ABC"])
                continue
            tables = [fp.cnv, *fp.fallbacks]
            r = rng.random()
            if r < 0.1:
                code = ""
            elif r < 0.2:
                code = outside_code(tables, widths[f], rng)
            elif isinstance(fp.cnv, LookupTable):
                pool = [c for c in list(fp.cnv._exact)[:200] + [c for t in fp.fallbacks for c in list(t._exact)[:50]]
                        if len(c) <= widths[f]]
                code = rng.choice(pool) if pool else ""
            else:
                codes, _ = rng.choice(fp.cnv.categories)
                code = code_from_line(codes, rng, widths[f]) or ""
            rec[f] = code
            if fp.switch is not None:
                deferred.append((f, code))      # the table depends on another field's value: resolved once the record is complete
            else:
                truth.setdefault(f, Counter())[expected_label(code, tables)] += 1
        for f, code in deferred:
            fp = plan.fields[f]
            sw_col, by_code = fp.switch
            table = by_code.get(str(rec.get(sw_col) or "").strip(), fp.cnv)
            truth.setdefault(f, Counter())[expected_label(code, [table, *fp.fallbacks])] += 1
        records.append(rec)
    write_dbf(out, spec, records, encoding=encoding)
    return out, {"truth": truth, "truth_age": truth_age, "dates": truth_dates, "n": n, "plan": plan,
                 "labeled_fields": sorted(plan.fields), "records": records, "spec": spec}
