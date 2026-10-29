"""Build `tabelas/tab_sinannet/agravnet.csv` (CID-10 codes and names) from the 22 chapter `.cnv` files of the TabWin package of
the SIM (`OBITOS_CID10_TAB.zip` from DATASUS: `tabdo/CID10_01.CNV` … `CID10_22.cnv`, width 4, 3-character categories and
4-character subcategories, label prefixed with the code).

Why: the `.def` files of the occupational-health forms label CID fields (CID_ACID, DIAG_ESP, DIAG_CONF, CID_LESAO) through
`agravnet.dbf`, but the AGRAVNET.DBF that ships with TAB_SINANNET has the codes in ID_AGRAVO and no name column. The lookup
chain prefers a CSV with the same stem (`lookup.find_lookup_files`), so this file answers for those fields. Columns `CODIGO,NOME`
match the generic fallbacks of `lookup._pick_columns`.

Usage: python scripts/make_agravnet_csv.py <folder with CID10_NN.cnv> [output csv]
"""
from __future__ import annotations

import csv
import re
import sys
from pathlib import Path

RE_CHAPTER = re.compile(r"^CID10_(\d{2})\.cnv$", re.IGNORECASE)
# `        2  A000 Cólera devida a Vibrio cholerae 01, biótipo cholerae      A000,` : order, label (code first), code tokens.
# The header (`N 3693 4 L`) is the SIM's, not Sinan's, so the file is parsed here rather than with `cnv.parse_cnv`.
# `@A021`, `&A090-`, `#O935`: the SIM marks codes not valid as underlying cause, added after the 1996 edition, or maternal.
RE_LINE = re.compile(r"^\s*\d+\s+[@&#]?([A-Z]\d{2}\d?)-?\s+(\S.*)$")


def parse_chapter(path: Path) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    for line in path.read_text(encoding="cp1252").splitlines()[1:]:
        m = RE_LINE.match(line.rstrip())
        if not m:
            continue
        code, rest = m.group(1).upper(), m.group(2)
        # the label is followed by the code list, which here is the same code again (`... álcool    X45 ,`); a long label
        # may leave a single space before it, so the trailing code is removed by value, not by column
        rest, n = re.subn(r"\s+" + re.escape(code) + r"\s*,?\s*$", "", rest)
        if n == 0:
            rest = re.sub(r"\s{2,}[A-Z0-9 ,]+$", "", rest)
        name = " ".join(rest.split())
        if name:
            out.append((code, name))
    return out


def main(src: Path, out: Path) -> int:
    files = sorted((p for p in src.iterdir() if RE_CHAPTER.match(p.name)), key=lambda p: p.name.upper())
    if len(files) != 22:
        sys.exit(f"esperados 22 arquivos CID10_NN.cnv em {src}; achados {len(files)}")
    rows: dict[str, str] = {}
    declared = 0
    for p in files:
        declared += int(p.read_text(encoding="cp1252").splitlines()[0].split()[1])
        for code, name in parse_chapter(p):
            rows.setdefault(code, name)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["CODIGO", "NOME"])
        for code, name in rows.items():
            w.writerow([code, name])
    n3 = sum(1 for c in rows if len(c) == 3)
    print(f"{out}: {len(rows)} códigos ({n3} categorias de 3, {len(rows) - n3} de 4) de {len(files)} capítulos; "
          f"{declared} linhas declaradas nos cabeçalhos")
    return 0


if __name__ == "__main__":
    src = Path(sys.argv[1])
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else Path(__file__).resolve().parents[1] / "tabelas" / "tab_sinannet" / "agravnet.csv"
    sys.exit(main(src, out))
