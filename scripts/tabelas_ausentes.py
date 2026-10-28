"""Lista as tabelas .cnv e .dbf que os .def do TabWin citam e `tabelas/tab_sinannet/` não tem.

Mesma lógica de `annotate.build_plan`: só linhas de categoria contam (agrupamentos de ano/mês/UF e tabelas de município
ficam de fora, porque o programa não as usa para rotular). Uso:

    python scripts/tabelas_ausentes.py [--tab PASTA] [--saida ARQUIVO.txt]

Saída: lista única (ordem alfabética, com quantos .def citam cada tabela), depois a lista por .def com os campos afetados,
e os .dbf externos ausentes. Nomes como estão nos .def; o TabWin procura sem distinguir maiúsculas.
"""
from __future__ import annotations

import argparse
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from sinan_anotador.annotate import AGE_FIELD, GROUPING_CNV_RE, MUNICIPALITY_CNV_RE, UF_CNV_RE, tab_dir_default  # noqa: E402
from sinan_anotador.cnv import find_cnv, parse_def  # noqa: E402
from sinan_anotador.lookup import find_lookup_files  # noqa: E402


def sweep(tab: Path):
    by_def: dict[str, dict[str, set[str]]] = defaultdict(lambda: defaultdict(set))
    dbf_by_def: dict[str, dict[str, set[str]]] = defaultdict(lambda: defaultdict(set))
    for p in sorted(tab.glob("*.def"), key=lambda p: p.name.lower()):
        d = parse_def(p)
        for ln in d.lines:
            if ln.cnv:
                if find_cnv(ln.cnv, tab) or ln.field == AGE_FIELD or MUNICIPALITY_CNV_RE.match(ln.cnv):
                    continue
                if GROUPING_CNV_RE.match(ln.cnv) and not UF_CNV_RE.match(ln.cnv):
                    continue
                by_def[d.name][ln.cnv].add(ln.field)
            elif ln.lookup_dbf and not find_lookup_files(ln.lookup_dbf, tab):
                dbf_by_def[d.name][ln.lookup_dbf].add(ln.field)
    return by_def, dbf_by_def


def report(tab: Path) -> str:
    by_def, dbf_by_def = sweep(tab)
    cited: dict[str, set[str]] = defaultdict(set)      # upper name -> defs
    spelling: dict[str, str] = {}
    for dn, m in by_def.items():
        for c in m:
            cited[c.upper()].add(dn)
            spelling.setdefault(c.upper(), c)
    out = [f"Tabelas citadas nos .def de {tab} e ausentes — {len(cited)} .cnv distintas, {len(by_def)} de "
           f"{len(list(tab.glob('*.def')))} .def afetados", "",
           "== Lista única (nome, nº de .def que a citam) =="]
    for k in sorted(cited, key=lambda k: (-len(cited[k]), k)):
        out.append(f"  {spelling[k]:28s} {len(cited[k]):3d}  {', '.join(sorted(cited[k]))}")
    out += ["", "== Por .def (tabela: campos afetados) =="]
    for dn in sorted(by_def, key=str.lower):
        out.append(f"\n{dn} ({len(by_def[dn])})")
        for c in sorted(by_def[dn], key=str.lower):
            out.append(f"  {c:28s} {', '.join(sorted(by_def[dn][c]))}")
    out += ["", "== .dbf externos ausentes =="]
    for dn in sorted(dbf_by_def, key=str.lower):
        for c, f in sorted(dbf_by_def[dn].items()):
            out.append(f"  {dn:18s} {c:18s} {', '.join(sorted(f))}")
    return "\n".join(out) + "\n"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--tab", help="pasta com os .def/.cnv (padrão: tabelas/tab_sinannet)")
    ap.add_argument("--saida", help="arquivo de saída (padrão: imprime)")
    a = ap.parse_args(argv)
    tab = Path(a.tab) if a.tab else tab_dir_default(ROOT / "src")
    text = report(tab)
    if a.saida:
        Path(a.saida).write_text(text, encoding="utf-8")
        print(f"gravado: {a.saida}")
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
