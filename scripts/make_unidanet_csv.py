#!/usr/bin/env python3
"""Build `tabelas/tab_sinannet/unidanet.csv` (ID_UNIDADE, NM_UNIDADE) from the public CNES establishment table.

Input: `tbEstabelecimentoAAAAMM.csv` from `ftp.datasus.gov.br/cnes/BASE_DE_DADOS_CNES_AAAAMM.ZIP` (plain or .gz; `;`-separated,
latin-1, quoted). Name = NO_FANTASIA, or NO_RAZAO_SOCIAL when the fantasy name is empty. Every establishment ever registered
is kept (active or not), so codes of closed units still get a label.

With `--medir`, also measures the pre-registered acceptance criteria (METODO 2026-10-24) against the TabWin DBF tables in the
same folder: coverage of UNIDANET ∪ UNIDINVEST codes, name agreement on a seeded sample, the control codes, and the file size.

Usage: make_unidanet_csv.py <tbEstabelecimento.csv[.gz]> [--out tabelas/tab_sinannet/unidanet.csv] [--medir] [--gzip]
"""
from __future__ import annotations

import argparse
import csv
import gzip
import io
import random
import sys
import unicodedata
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE / "src"))


def open_text(path: Path):
    raw = gzip.open(path, "rb") if path.name.lower().endswith(".gz") else open(path, "rb")
    return io.TextIOWrapper(raw, encoding="latin-1", newline="")


def read_cnes(path: Path) -> dict[str, str]:
    units: dict[str, str] = {}
    n = n_blank = 0
    with open_text(path) as fh:
        rd = csv.DictReader(fh, delimiter=";")
        cols = {c.upper(): c for c in rd.fieldnames or []}
        code_c, fant_c, razao_c = cols.get("CO_CNES"), cols.get("NO_FANTASIA"), cols.get("NO_RAZAO_SOCIAL")
        if not code_c or not (fant_c or razao_c):
            sys.exit(f"colunas CO_CNES/NO_FANTASIA/NO_RAZAO_SOCIAL não encontradas em {path.name}: {rd.fieldnames[:10]}")
        for r in rd:
            n += 1
            code = (r.get(code_c) or "").strip()
            if not code:
                continue
            code = code.zfill(7) if code.isdigit() else code
            name = " ".join(((fant_c and r.get(fant_c)) or "").split()) or " ".join(((razao_c and r.get(razao_c)) or "").split())
            if not name:
                n_blank += 1
                continue
            units.setdefault(code, name)
    print(f"{path.name}: {n} linhas, {len(units)} códigos com nome, {n_blank} sem nome")
    return units


def write_csv(units: dict[str, str], out: Path, use_gzip: bool) -> Path:
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")        # quotes only when the name carries a comma or a quote
    w.writerow(["ID_UNIDADE", "NM_UNIDADE"])
    for c, n in sorted(units.items()):
        w.writerow([c, n])
    body = buf.getvalue().encode("utf-8")
    if use_gzip:
        out = out.with_name(out.name + ".gz") if not out.name.endswith(".gz") else out
        out.write_bytes(gzip.compress(body, compresslevel=9))
    else:
        out.write_bytes(body)
    print(f"gravado {out} ({out.stat().st_size / 1e6:.1f} MB, {len(units)} códigos)")
    return out


def norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s.upper())
    return " ".join("".join(ch for ch in s if not unicodedata.combining(ch)).split())


def measure(units: dict[str, str], tab_dir: Path, out: Path):
    from sinan_anotador.lookup import load_lookup
    ua = load_lookup(tab_dir / "UNIDANET.DBF", "ID_UNIDADE", "NM_UNIDADE")
    ui = load_lookup(tab_dir / "UNIDINVEST.DBF", "ID_UNIDADE", "NM_UNIDADE")
    tab = {}
    for t in (ua, ui):
        for c, n in t._exact.items():
            tab.setdefault(c, n)
    covered = [c for c in tab if c in units]
    cov = len(covered) / len(tab)
    print(f"[medido] 1. cobertura: {len(covered)}/{len(tab)} códigos de UNIDANET∪UNIDINVEST (2021) estão no CNES = {cov:.2%}"
          f" -> {'APROVADO' if cov >= 0.99 else 'REPROVADO'} (critério ≥ 99%)")
    missing = [c for c in tab if c not in units]
    print(f"   códigos de 2021 ausentes do CNES: {len(missing)}; exemplos: {[(c, tab[c]) for c in missing[:5]]}")
    rng = random.Random(20261024)
    sample = rng.sample(covered, 200)
    same = [c for c in sample if norm(tab[c]) == norm(units[c])]
    print(f"[medido] 2. nomes iguais (normalizados) em 200 sorteados: {len(same)} = {len(same) / 2:.0f}%"
          f" -> {'APROVADO' if len(same) >= 180 else 'REPROVADO'} (critério ≥ 90%)")
    diff = [c for c in sample if c not in same]
    for c in diff[:8]:
        print(f"   {c}: TabWin 2021 = {tab[c]!r} | CNES = {units[c]!r}")
    only_ui = [c for c in ui._exact if c not in ua._exact]
    ctrl = rng.sample(only_ui, 2000)
    hit = sum(1 for c in ctrl if c in units)
    print(f"[medido] 3. controles: 2561492 -> {units.get('2561492')!r}; 2000 códigos só de UNIDINVEST: {hit} rotulados pelo CNES"
          f" (os demais seguem pelo DBF na cadeia) -> {'APROVADO' if units.get('2561492') and hit > 0 else 'REPROVADO'}")
    size = out.stat().st_size / 1e6
    print(f"[medido] 5. tamanho: {size:.1f} MB -> {'cabe no git como .csv' if size < 50 else 'acima de 50 MB: usar .csv.gz'}")
    print(f"   códigos no CNES e não nas tabelas de 2021 (unidades novas ou nunca notificadoras): {sum(1 for c in units if c not in tab)}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("source")
    ap.add_argument("--out", default=str(HERE / "tabelas" / "tab_sinannet" / "unidanet.csv"))
    ap.add_argument("--medir", action="store_true")
    ap.add_argument("--gzip", action="store_true")
    a = ap.parse_args()
    units = read_cnes(Path(a.source))
    out = write_csv(units, Path(a.out), a.gzip)
    if a.medir:
        measure(units, Path(a.out).parent, out)


if __name__ == "__main__":
    main()
