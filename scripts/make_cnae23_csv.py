"""Build `tabelas/tab_sinannet/cnaenet_cnae23.csv` (CNAE 2.3 classes and subclasses, columns `CODIGO,NOME,NIVEL`) so the lookup
chain of the CNAE fields of the occupational-health forms (`cnae`, `cnae_prin` -> `cnaenet.dbf` in the .def) answers for CNAE 2.x
codes as well as for the CNAE 1.0 classes that TabWin's CNAENET.DBF holds (580 five-digit codes). The two versions share no
five-digit code (checked in docs/METODO.md, 2026-11-04), so both tables sit in the same chain; `lookup.find_lookup_files` picks
`cnaenet_*.csv` up as a complement of `cnaenet.dbf`.

Sources (the IBGE/CONCLA site was not reachable from the session that built the file; see METODO):
  --oca   l10n_br_fiscal.cnae.csv of OCA/l10n-brazil: columns id,code,name,version,internal_type,parent_id:id; codes written
          `86.10-1` (class) and `8610-1/01` (subclass); every line version 2.3.
  --extra a plain code,name CSV without header (fireho/govbr2txt `readable/cnaes.csv`): used only for subclasses whose class has
          no subclass at all in the OCA copy (9900-8/00 in practice). A general rule, not a hand-written line.
Codes are stored as digits only (`86101`, `8610101`), which is how the Sinan NET export writes them.

Usage: python scripts/make_cnae23_csv.py --oca <oca csv> [--extra <code,name csv>] [-o output csv]
"""
from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path

OUT_DEFAULT = Path(__file__).resolve().parent.parent / "tabelas" / "tab_sinannet" / "cnaenet_cnae23.csv"


def digits(code: str) -> str:
    return re.sub(r"\D", "", code)


def clean(name: str) -> str:
    return " ".join(name.split())


def read_oca(path: Path) -> tuple[dict[str, str], dict[str, str], set[str]]:
    """(classes, subclasses, versions seen) from the OCA file. A class is a 5-digit code written with a dot (`86.10-1`); a subclass
    has 7 digits. Sections, divisions and groups are skipped."""
    classes: dict[str, str] = {}
    subclasses: dict[str, str] = {}
    versions: set[str] = set()
    with path.open(encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            versions.add(r.get("version", ""))
            d = digits(r["code"])
            if len(d) == 5 and "." in r["code"]:
                classes[d] = clean(r["name"])
            elif len(d) == 7:
                subclasses[d] = clean(r["name"])
    return classes, subclasses, versions


def read_extra(path: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    with path.open(encoding="utf-8", newline="") as f:
        for row in csv.reader(f):
            if len(row) < 2:
                continue
            d = digits(row[0])
            if len(d) == 7:
                out[d] = clean(row[1])
    return out


def build(oca: Path, extra: Path | None) -> tuple[list[tuple[str, str, str]], list[str]]:
    classes, subclasses, versions = read_oca(oca)
    notes = [f"OCA: {len(classes)} classes, {len(subclasses)} subclasses, version(s) {sorted(versions)}"]
    orphan = [s for s in subclasses if s[:5] not in classes]
    if orphan:
        raise SystemExit(f"subclasses whose first 5 digits are not a class: {orphan[:5]}")
    without = sorted(c for c in classes if not any(s.startswith(c) for s in subclasses))
    notes.append(f"classes without subclass in OCA: {without}")
    added: list[str] = []
    if extra is not None:
        ex = read_extra(extra)
        for s, n in sorted(ex.items()):
            if s[:5] in without and s not in subclasses:
                subclasses[s] = n
                added.append(s)
        notes.append(f"subclasses taken from --extra for those classes: {added}")
        still = [c for c in without if not any(s.startswith(c) for s in subclasses)]
        notes.append(f"classes still without subclass: {still}")
    rows = [(c, n, "classe") for c, n in classes.items()] + [(s, n, "subclasse") for s, n in subclasses.items()]
    rows.sort(key=lambda r: (r[0][:5], len(r[0]), r[0]))
    return rows, notes


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--oca", required=True, type=Path)
    ap.add_argument("--extra", type=Path)
    ap.add_argument("-o", "--output", type=Path, default=OUT_DEFAULT)
    a = ap.parse_args(argv)
    rows, notes = build(a.oca, a.extra)
    with a.output.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["CODIGO", "NOME", "NIVEL"])
        w.writerows(rows)
    n_cl = sum(1 for r in rows if r[2] == "classe")
    for n in notes:
        print(n)
    print(f"{a.output}: {len(rows)} rows ({n_cl} classes, {len(rows) - n_cl} subclasses)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
