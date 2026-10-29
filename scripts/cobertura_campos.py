"""Mede, por `.def`, quantos campos de categoria têm a tabela `.cnv` presente em `tabelas/tab_sinannet/`.

Complementa `tabelas_ausentes.py` (que lista as tabelas que faltam): aqui a unidade é o campo, porque é o campo que sai
rotulado ou não no xlsx. Mesma lógica de `annotate.build_plan`: só linhas de categoria contam (agrupamentos de ano/mês/UF,
tabelas de município e a faixa etária ficam de fora). Um campo com mais de uma tabela conta uma vez, presente se todas as
tabelas que o `.def` cita existem. Uso:

    python scripts/cobertura_campos.py [--tab PASTA] [--saida ARQUIVO.txt]

Saída: uma linha por `.def` (campos com tabela de categoria, presentes, ausentes, cobertura) e o total. É medida de
dicionário, não de base real: a cobertura observada numa base depende de quais campos o DBF exportado traz.
"""
from __future__ import annotations

import argparse
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from sinan_anotador.annotate import AGE_FIELD, GROUPING_CNV_RE, MUNICIPALITY_CNV_RE, UF_CNV_RE, tab_dir_default  # noqa: E402
from sinan_anotador.cnv import def_files, find_cnv, parse_def  # noqa: E402


def measure(tab: Path) -> list[tuple[str, int, int, list[str]]]:
    rows = []
    for p in def_files(tab):
        d = parse_def(p)
        fields: dict[str, bool] = {}
        missing_fields: dict[str, set[str]] = defaultdict(set)
        for ln in d.lines:
            if not ln.cnv or ln.field == AGE_FIELD or MUNICIPALITY_CNV_RE.match(ln.cnv):
                continue
            if GROUPING_CNV_RE.match(ln.cnv) and not UF_CNV_RE.match(ln.cnv):
                continue
            ok = find_cnv(ln.cnv, tab) is not None
            fields[ln.field] = fields.get(ln.field, True) and ok
            if not ok:
                missing_fields[ln.field].add(ln.cnv)
        total = len(fields)
        present = sum(1 for v in fields.values() if v)
        rows.append((d.name, total, present, sorted(missing_fields)))
    return rows


def report(tab: Path) -> str:
    rows = measure(tab)
    out = [f"Cobertura de dicionário por .def em {tab}", "",
           f"{'.def':22s} {'campos':>6s} {'presentes':>9s} {'ausentes':>8s} {'cobertura':>9s}  campos sem tabela"]
    t_tot = t_pres = 0
    for name, total, present, missing in rows:
        t_tot += total
        t_pres += present
        pct = f"{100 * present / total:5.1f}%" if total else "   —  "
        out.append(f"{name:22s} {total:6d} {present:9d} {total - present:8d} {pct:>9s}  {', '.join(missing)}")
    full = sum(1 for _, t, p, _ in rows if t == p)
    out += ["", f"TOTAL ({len(rows)} .def): {t_tot} campos de categoria, {t_pres} com tabela "
            f"({100 * t_pres / t_tot:.1f}%), {t_tot - t_pres} sem; {full} .def com cobertura completa"]
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
