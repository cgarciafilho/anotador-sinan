"""Command line: `python -m sinan_anotador.cli ARQUIVO.DBF [...]` writes `<nome>_anotado.xlsx` and `<nome>_anotado.log.txt`
next to each input (or in --saida). Messages to the user are in Portuguese."""
from __future__ import annotations

import argparse
import datetime as dt
import sys
import time
import traceback
from pathlib import Path

import pandas as pd

from . import __version__
from .annotate import apply_plan, build_plan, detect_def, field_table, tab_dir_default
from .names import resolve_names
from .dbf import read_dbf
from .duplicates import KEYS, build_tables, load_ads
from .excel import DEFAULT_MAX_DATA_ROWS, write_xlsx


class Log:
    def __init__(self):
        self.lines: list[str] = []

    def __call__(self, msg: str = ""):
        print(msg)
        self.lines.append(msg)

    def write(self, path: Path):
        path.write_text("\n".join(self.lines) + "\n", encoding="utf-8")


def expand_inputs(paths: list[str]) -> list[Path]:
    out: list[Path] = []
    for p in paths:
        q = Path(p)
        if q.is_dir():
            out.extend(sorted(x for x in q.iterdir() if x.suffix.lower() == ".dbf"))
        else:
            out.append(q)
    return out


def annotate_file(dbf_path: Path, tab_dir: Path, out_dir: Path | None, encoding: str | None,
                  max_data_rows: int, long_names: bool = True, csv_dir: Path | None = None,
                  duplicates: bool = True) -> tuple[bool, list[Path]]:
    log = Log()
    t0 = time.time()
    out_dir = out_dir or dbf_path.parent
    out_dir.mkdir(parents=True, exist_ok=True)
    base = out_dir / f"{dbf_path.stem}_anotado"
    log_path = out_dir / f"{dbf_path.stem}_anotado.log.txt"
    ok = False
    files: list[Path] = []
    try:
        log(f"anotador SINAN {__version__} — {dt.datetime.now():%d/%m/%Y %H:%M:%S}")
        log(f"Arquivo de entrada: {dbf_path}")
        log(f"Tabelas TabWin: {tab_dir}")
        df, info = read_dbf(dbf_path, encoding=encoding)
        t_read = time.time()
        log(f"Registros lidos: {info.n_records_read} (cabeçalho declara {info.n_records_header}); campos: {len(info.fields)}"
            f" — leitura em {t_read - t0:.1f} s")
        log(f"Codificação do texto: {info.encoding_note}")
        for n in info.notes:
            log(f"  {n}")
        deffile, notes = detect_def(dbf_path.name, list(df.columns), tab_dir)
        for n in notes:
            log(n)
        plan = None
        if deffile is None:
            annotated, dictionary = df, pd.DataFrame(columns=["campo", "tabela", "codigos", "rotulo", "uso"])
            n_lab = 0
        else:
            plan = build_plan(deffile, list(df.columns), info.field_types, tab_dir)
            annotated, dictionary = apply_plan(df, plan)
            n_lab = len(plan.fields) + (1 if plan.age_band is not None else 0)
            log(f"Campos rotulados: {n_lab} de {len(df.columns)}"
                + (f" (idade em anos em {plan.age_field}_anos)" if plan.age_field else "")
                + f" — anotação em {time.time() - t_read:.1f} s")
            outside = [c for c in df.columns if c.upper() not in deffile.fields]
            if outside:
                log(f"  Campos do DBF que o .def não descreve ({len(outside)}), copiados sem rótulo: {', '.join(outside)}")
            for name, t in plan.lookups.items():
                log(f"  Tabela externa {t.name}: {t.n_rows} códigos" + (f" ({'; '.join(t.notes)})" if t.notes else ""))
            for fld, cov in plan.coverage.items():
                parts = ", ".join(f"{name} {n} ({k} códigos)" for name, (n, k) in cov["by_table"].items() if n)
                miss_n, miss_k = cov["missing"]
                pct = f"{100 * miss_n / cov['filled']:.1f}%" if cov["filled"] else "-"
                log(f"  Cobertura {fld}: {cov['filled']} registros preenchidos; rotulados por {parts or 'nenhuma tabela'}; "
                    f"sem rótulo {miss_n} ({pct}; {miss_k} códigos distintos)")
            for w in plan.warnings:
                log(f"  AVISO {w}")
            absent = [s.split(":")[0] for s in plan.skipped if s.endswith("não no DBF")]
            others = [s for s in plan.skipped if not s.endswith("não no DBF")]
            if absent:
                log(f"  Campos do .def ausentes no DBF ({len(absent)}): {', '.join(absent)}")
            if others:
                log(f"  Campos sem rótulo por desenho ({len(others)}):")
                for s in others:
                    log(f"    - {s}")
        preferred = {f: fp.cnv.name for f, fp in plan.fields.items()} if plan else {}
        names = resolve_names(list(df.columns), deffile, tab_dir, preferred, csv_dir)
        headers, fields_df = field_table(list(annotated.columns), list(df.columns), info.field_types, plan, names)
        n_named = sum(1 for c in df.columns if names[c].name)
        by_src = {}
        for c in df.columns:
            if names[c].source:
                by_src[names[c].source] = by_src.get(names[c].source, 0) + 1
        log(f"Nomes por extenso: {n_named} de {len(df.columns)} campos ("
            + "; ".join(f"{k}: {v}" for k, v in sorted(by_src.items(), key=lambda kv: -kv[1])) + ")"
            + ("" if long_names else " — cabeçalho mantido com o nome curto (--sem-nome-extenso)"))
        unnamed = [c for c in df.columns if not names[c].name]
        if unnamed:
            log(f"  Sem nome por extenso ({len(unnamed)}): {', '.join(unnamed)}")
        extra = None
        if duplicates:
            t_dup = time.time()
            dup_log: list[str] = []
            ads_path = next((p for p in (tab_dir.parent / "regionalizacao_sesa_sr_ads.csv", tab_dir / "regionalizacao_sesa_sr_ads.csv")
                             if p.is_file()), None)
            ads = load_ads(ads_path) if ads_path else {}
            dup_full, dup_short, st = build_tables(annotated, list(df.columns), deffile.name if deffile else None, dup_log, ads)
            extra = {"duplicidades": dup_full, "duplicidades_resumo": dup_short}
            log(f"Duplicidades suspeitas: {st['pairs']} pares (perfil {st['profile']}; "
                + ", ".join(f"{k} {st['by_key'][k]}" for k in KEYS) + f"; já julgados no Sinan {st['judged']}) — em {time.time() - t_dup:.1f} s")
            for lab, k in sorted(st["by_label"].items(), key=lambda kv: -kv[1]):
                log(f"  {k:>6}  {lab}")
            sk = st.get("sem_chave", {})
            if sk:
                log(f"  Registros que nenhuma chave alcança: {sk['fora_de_toda_chave']} (sem nome {sk['sem_nome']}; sem nascimento e sem mãe). "
                    f"Alcance parcial: sem data de nascimento {sk['sem_nascimento']} (só nome+mãe); sem sexo {sk['sem_sexo']} (chave padrão e "
                    f"nascimento ficam com sexo em branco); sem nome da mãe {sk['sem_mae']} (sem nome+mãe); nome de uma palavra {sk['nome_de_uma_palavra']} (sem chave padrão)")
            log(f"  ADS por município: {ads_path.name + f' ({len(ads)} municípios)' if ads_path else 'tabela não encontrada; usa a regional do Sinan'}"
                + (f"; {st.get('ads_missing', 0)} lados de par sem ADS" if st.get('ads_missing') else ""))
            for n in dup_log:
                log(f"  {n}")
        t_ann = time.time()
        files, notes = write_xlsx(annotated, dictionary, base, max_data_rows=max_data_rows,
                                  headers=headers if long_names else None, fields=fields_df, extra=extra)
        for n in notes:
            log(n)
        log(f"Gravação do xlsx em {time.time() - t_ann:.1f} s")
        for f in files:
            log(f"Gravado: {f} ({f.stat().st_size / 1e6:.1f} MB)")
        log(f"Linhas de dados gravadas: {len(annotated)} = registros lidos: {len(df)} -> "
            + ("OK" if len(annotated) == len(df) else "DIFERENTE (avise o suporte)"))
        log(f"Tempo: {time.time() - t0:.1f} s")
        log("RESULTADO: OK")
        ok = True
    except Exception:
        log("RESULTADO: FALHA")
        log(traceback.format_exc())
    log.write(log_path)
    return ok, files


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="sinan_anotador",
                                 description="Anota DBF do Sinan NET com os rótulos do TabWin e grava xlsx.")
    ap.add_argument("entradas", nargs="+", help="arquivos .DBF (ou pastas com .DBF)")
    ap.add_argument("--tab", help="pasta com os .def/.cnv do TabWin (padrão: tabelas/tab_sinannet ou tab_sinannet)")
    ap.add_argument("--saida", help="pasta de saída (padrão: ao lado de cada DBF)")
    ap.add_argument("--codificacao", help="força a codificação do texto (cp850, cp1252, latin-1); padrão: detectar")
    ap.add_argument("--sem-nome-extenso", action="store_true",
                    help="cabeçalho só com o nome do campo (padrão: 'Nome por extenso (CAMPO)')")
    ap.add_argument("--dicionarios", help="pasta com CSVs de dicionário (variavel, nome_campo) para os nomes por extenso "
                                          "(padrão: pasta 'dicionarios' ao lado das tabelas TabWin)")
    ap.add_argument("--sem-duplicidades", action="store_true", help="não gera as abas de duplicidades suspeitas")
    ap.add_argument("--max-linhas", type=int, default=DEFAULT_MAX_DATA_ROWS,
                    help="máximo de linhas de dados por aba antes de dividir por ano (padrão: limite do Excel)")
    a = ap.parse_args(argv)
    tab_dir = Path(a.tab) if a.tab else tab_dir_default()
    if tab_dir is None or not tab_dir.is_dir():
        print("ERRO: pasta das tabelas TabWin (.def/.cnv) não encontrada; use --tab", file=sys.stderr)
        return 2
    inputs = expand_inputs(a.entradas)
    if not inputs:
        print("ERRO: nenhum arquivo .DBF informado", file=sys.stderr)
        return 2
    failures = 0
    for p in inputs:
        if not p.is_file():
            print(f"ERRO: arquivo não encontrado: {p}", file=sys.stderr)
            failures += 1
            continue
        ok, _ = annotate_file(p, tab_dir, Path(a.saida) if a.saida else None, a.codificacao, a.max_linhas,
                              long_names=not a.sem_nome_extenso, csv_dir=Path(a.dicionarios) if a.dicionarios else None,
                              duplicates=not a.sem_duplicidades)
        failures += 0 if ok else 1
        print()
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
