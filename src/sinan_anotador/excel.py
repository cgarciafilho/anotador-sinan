"""Writing the annotated table to xlsx (streamed with openpyxl write-only mode) with the Excel row limit handled."""
from __future__ import annotations

import datetime as dt
from pathlib import Path

import pandas as pd
from openpyxl import Workbook
from openpyxl.cell import WriteOnlyCell

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
    if v is None:
        return None
    if isinstance(v, float) and v != v:
        return None
    if v is pd.NA or v is pd.NaT:
        return None
    if isinstance(v, (pd.Timestamp,)):
        return v.to_pydatetime()
    return v


def _write_sheet(wb: Workbook, title: str, df: pd.DataFrame, headers: dict[str, str] | None = None):
    ws = wb.create_sheet(title)
    ws.append([headers.get(c, c) if headers else c for c in df.columns])
    date_cols = {i for i, c in enumerate(df.columns)
                 if df[c].map(lambda v: isinstance(v, (dt.date, dt.datetime))).any()}
    for row in df.itertuples(index=False, name=None):
        cells = []
        for i, v in enumerate(row):
            v = _cell_value(v)
            if i in date_cols and isinstance(v, (dt.date, dt.datetime)):
                c = WriteOnlyCell(ws, value=v)
                c.number_format = DATE_FORMAT
                cells.append(c)
            else:
                cells.append(v)
        ws.append(cells)
    return ws


def write_workbook(path: Path, data: pd.DataFrame, dictionary: pd.DataFrame, headers: dict[str, str] | None = None,
                   fields: pd.DataFrame | None = None, extra: dict[str, pd.DataFrame] | None = None) -> Path:
    wb = Workbook(write_only=True)
    _write_sheet(wb, "dados", data, headers)
    for title, sheet in (extra or {}).items():        # e.g. duplicidades, duplicidades_resumo
        _write_sheet(wb, title, sheet)
    if fields is not None:
        _write_sheet(wb, "campos", fields)
    _write_sheet(wb, "dicionario", dictionary)
    wb.save(str(path))
    return path


def write_xlsx(data: pd.DataFrame, dictionary: pd.DataFrame, out_base: Path,
               max_data_rows: int = DEFAULT_MAX_DATA_ROWS, headers: dict[str, str] | None = None,
               fields: pd.DataFrame | None = None, extra: dict[str, pd.DataFrame] | None = None) -> tuple[list[Path], list[str]]:
    """Write `<out_base>.xlsx`, or one file per notification year (`<out_base>_<ano>.xlsx`) when the table exceeds
    `max_data_rows`; a single year above the limit is split into numbered parts. Returns (files, notes in Portuguese)."""
    out_base = Path(out_base)
    notes: list[str] = []
    if len(data) <= max_data_rows:
        p = out_base.with_suffix(".xlsx")
        write_workbook(p, data, dictionary, headers, fields, extra)
        return [p], notes
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
            write_workbook(p, part, dictionary, headers, fields, extra)   # pairs cross years: the whole sheet goes in each file
            files.append(p)
            notes.append(f"  {p.name}: {len(part)} registros")
        else:
            n = 0
            for start in range(0, len(part), max_data_rows):
                n += 1
                chunk = part.iloc[start:start + max_data_rows]
                p = out_base.with_name(f"{out_base.name}_{tag}_parte{n}.xlsx")
                write_workbook(p, chunk, dictionary, headers, fields, extra)
                files.append(p)
                notes.append(f"  {p.name}: {len(chunk)} registros (ano {tag} acima do limite, dividido)")
    return files, notes
