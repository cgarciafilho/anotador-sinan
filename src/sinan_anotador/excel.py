"""Writing the annotated table to xlsx (streamed with openpyxl write-only mode) with the Excel row limit handled."""
from __future__ import annotations

import datetime as dt
from pathlib import Path

import pandas as pd
from openpyxl import Workbook
from openpyxl.cell import WriteOnlyCell
from openpyxl.cell.cell import ILLEGAL_CHARACTERS_RE

EXCEL_MAX_ROWS = 1_048_576          # rows per sheet, header included
DEFAULT_MAX_DATA_ROWS = EXCEL_MAX_ROWS - 1
DATE_FORMAT = "DD/MM/YYYY"


def year_of_record(df: pd.DataFrame) -> pd.Series | None:
    """Notification year: NU_ANO when present, else the year of DT_NOTIFIC."""
    if "NU_ANO" in df.columns:
        y = pd.to_numeric(df["NU_ANO"], errors="coerce")
        if y.notna().any():
            return y.astype("Int64")
    if "DT_NOTIFIC" in df.columns:
        return df["DT_NOTIFIC"].map(lambda v: v.year if isinstance(v, (dt.date, dt.datetime)) else None).astype("Int64")
    return None


def _cell_value(v):
    """Value as openpyxl accepts it: None for missing, datetime for Timestamp, text without control characters.
    Returns (value, cleaned): `cleaned` is True when control characters were removed from a string."""
    if v is None:
        return None, False
    if isinstance(v, float) and v != v:
        return None, False
    if v is pd.NA or v is pd.NaT:
        return None, False
    if isinstance(v, (pd.Timestamp,)):
        return v.to_pydatetime(), False
    if isinstance(v, str) and ILLEGAL_CHARACTERS_RE.search(v):
        # Sinan DBFs carry stray control characters (\x00 padding, \x1a, ...) mostly in memo/observation fields; openpyxl
        # refuses them (IllegalCharacterError) and the whole run was lost at the last step. Tab, LF and CR are kept.
        return ILLEGAL_CHARACTERS_RE.sub("", v), True
    return v, False


def _write_sheet(wb: Workbook, title: str, df: pd.DataFrame, headers: dict[str, str] | None = None,
                 cleaned: dict[str, int] | None = None):
    """Append `df` as sheet `title`. `cleaned`, when given, accumulates per column the cells whose control characters were
    removed (key: "<sheet>.<column>")."""
    ws = wb.create_sheet(title)
    ws.append([headers.get(c, c) if headers else c for c in df.columns])
    date_cols = {i for i, c in enumerate(df.columns)
                 if df[c].map(lambda v: isinstance(v, (dt.date, dt.datetime))).any()}
    colnames = list(df.columns)
    for row in df.itertuples(index=False, name=None):
        cells = []
        for i, v in enumerate(row):
            v, was_cleaned = _cell_value(v)
            if was_cleaned and cleaned is not None:
                key = f"{title}.{colnames[i]}"
                cleaned[key] = cleaned.get(key, 0) + 1
            if i in date_cols and isinstance(v, (dt.date, dt.datetime)):
                c = WriteOnlyCell(ws, value=v)
                c.number_format = DATE_FORMAT
                cells.append(c)
            else:
                cells.append(v)
        ws.append(cells)
    return ws


def write_workbook(path: Path, data: pd.DataFrame, dictionary: pd.DataFrame, headers: dict[str, str] | None = None,
                   fields: pd.DataFrame | None = None, extra: dict[str, pd.DataFrame] | None = None,
                   cleaned: dict[str, int] | None = None) -> Path:
    wb = Workbook(write_only=True)
    _write_sheet(wb, "dados", data, headers, cleaned)
    for title, sheet in (extra or {}).items():        # e.g. duplicidades, duplicidades_resumo
        _write_sheet(wb, title, sheet, None, cleaned)
    if fields is not None:
        _write_sheet(wb, "campos", fields, None, cleaned)
    _write_sheet(wb, "dicionario", dictionary, None, cleaned)
    wb.save(str(path))
    return path


def cleaned_note(cleaned: dict[str, int]) -> str | None:
    """Log line (Portuguese) summarising the cells whose control characters were removed, or None when there were none."""
    if not cleaned:
        return None
    total = sum(cleaned.values())
    by_col = sorted(cleaned.items(), key=lambda kv: (-kv[1], kv[0]))
    where = ", ".join(f"{k} ({n})" for k, n in by_col[:10]) + (f", … ({len(by_col)} colunas)" if len(by_col) > 10 else "")
    return (f"AVISO: {total} células continham caracteres de controle (código 0–31, exceto tabulação e quebra de linha), "
            f"que o Excel não aceita; foram removidos ao gravar — {where}")


def write_xlsx(data: pd.DataFrame, dictionary: pd.DataFrame, out_base: Path,
               max_data_rows: int = DEFAULT_MAX_DATA_ROWS, headers: dict[str, str] | None = None,
               fields: pd.DataFrame | None = None, extra: dict[str, pd.DataFrame] | None = None) -> tuple[list[Path], list[str]]:
    """Write `<out_base>.xlsx`, or one file per notification year (`<out_base>_<ano>.xlsx`) when the table exceeds
    `max_data_rows`; a single year above the limit is split into numbered parts. Returns (files, notes in Portuguese)."""
    out_base = Path(out_base)
    notes: list[str] = []
    cleaned: dict[str, int] = {}      # cells with control characters removed, per "<sheet>.<column>"; see _cell_value
    if len(data) <= max_data_rows:
        p = out_base.with_suffix(".xlsx")
        write_workbook(p, data, dictionary, headers, fields, extra, cleaned)
        note = cleaned_note(cleaned)
        return [p], notes + ([note] if note else [])
    notes.append(f"AVISO: {len(data)} registros excedem o limite do Excel de {max_data_rows} linhas de dados por aba; "
                 f"a saída foi dividida por ano de notificação")
    years = year_of_record(data)
    if years is None:
        notes.append("AVISO: sem NU_ANO nem DT_NOTIFIC para dividir por ano; dividido em partes de tamanho fixo")
        years = pd.Series([0] * len(data), index=data.index, dtype="Int64")
    files: list[Path] = []
    for year, idx in sorted(years.fillna(-1).groupby(years.fillna(-1)).groups.items(), key=lambda kv: kv[0]):
        part = data.loc[idx]
        tag = f"{int(year)}" if year >= 0 else "sem_ano"
        if len(part) <= max_data_rows:
            p = out_base.with_name(f"{out_base.name}_{tag}.xlsx")
            write_workbook(p, part, dictionary, headers, fields, extra, cleaned)   # pairs cross years: the whole sheet goes in each file
            files.append(p)
            notes.append(f"  {p.name}: {len(part)} registros")
        else:
            n = 0
            for start in range(0, len(part), max_data_rows):
                n += 1
                chunk = part.iloc[start:start + max_data_rows]
                p = out_base.with_name(f"{out_base.name}_{tag}_parte{n}.xlsx")
                write_workbook(p, chunk, dictionary, headers, fields, extra, cleaned)
                files.append(p)
                notes.append(f"  {p.name}: {len(chunk)} registros (ano {tag} acima do limite, dividido)")
    note = cleaned_note(cleaned)     # sheets repeated in every file (duplicidades, campos, dicionario) are counted per file
    if note:
        notes.append(note)
    return files, notes
