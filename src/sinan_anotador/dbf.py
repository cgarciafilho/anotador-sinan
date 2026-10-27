"""Reading a Sinan NET DBF export into a pandas DataFrame.

Sinan NET writes dBase III files. Text is in a DOS/Windows single-byte code page: the previous project read the real
bases with cp850 by default (the de-identification script of the previous analysis project), with cp1252 as the alternative. We read
every text field as latin-1 (a lossless byte -> char map), then pick cp850 or cp1252 by scoring Portuguese letters on
the non-ASCII bytes and re-decode only the strings that need it.
"""
from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd
from dbfread import DBF
from dbfread.field_parser import FieldParser

PORTUGUESE = set("áàâãéêíóôõúüçÁÀÂÃÉÊÍÓÔÕÚÜÇºª°")
CANDIDATES = ("cp850", "cp1252")


class LenientFieldParser(FieldParser):
    """Invalid dates or numbers in a record become None instead of aborting the whole file."""

    def parseD(self, field, data):
        try:
            return super().parseD(field, data)
        except (ValueError, TypeError):
            return None

    def parseN(self, field, data):
        try:
            return super().parseN(field, data)
        except (ValueError, TypeError):
            return None

    def parseF(self, field, data):
        try:
            return super().parseF(field, data)
        except (ValueError, TypeError):
            return None

    def parseL(self, field, data):
        try:
            return super().parseL(field, data)
        except (ValueError, TypeError):
            return None


@dataclass
class DbfField:
    name: str
    type: str      # C, N, D, L, F, M, ...
    length: int
    decimals: int


@dataclass
class DbfInfo:
    path: Path
    fields: list[DbfField]
    n_records_header: int
    n_records_read: int
    encoding: str
    encoding_note: str
    notes: list[str] = field(default_factory=list)

    @property
    def field_types(self) -> dict[str, str]:
        return {f.name: f.type for f in self.fields}


def _score(text: str) -> tuple[int, int]:
    good = sum(1 for ch in text if ch in PORTUGUESE)
    bad = sum(1 for ch in text if ord(ch) > 127 and ch not in PORTUGUESE)
    return good, bad


def detect_encoding(samples: list[str]) -> tuple[str, str]:
    """samples: latin-1 decoded strings. Returns (encoding, note in Portuguese)."""
    raw = "".join(s for s in samples if any(ord(ch) > 127 for ch in s))
    if not raw:
        return "cp850", "texto só com caracteres ASCII; codificação irrelevante (cp850 assumido)"
    data = raw.encode("latin-1")
    scores = {}
    for enc in CANDIDATES:
        good, bad = _score(data.decode(enc, errors="replace"))
        scores[enc] = (good, -bad)
    best = max(CANDIDATES, key=lambda e: scores[e])   # tie -> first candidate, cp850
    desc = "; ".join(f"{e}: {scores[e][0]} letras do português, {-scores[e][1]} estranhas" for e in CANDIDATES)
    return best, f"codificação escolhida {best} ({desc})"


def _recode(series: pd.Series, encoding: str) -> pd.Series:
    if encoding == "latin-1":
        return series

    def fix(v):
        if isinstance(v, str) and any(ord(ch) > 127 for ch in v):
            return v.encode("latin-1").decode(encoding, errors="replace")
        return v

    uniques = series.dropna().unique()
    mapping = {u: fix(u) for u in uniques if isinstance(u, str) and any(ord(ch) > 127 for ch in u)}
    return series.map(lambda v: mapping.get(v, v)) if mapping else series


def read_dbf(path: str | Path, encoding: str | None = None, max_sample: int = 20000) -> tuple[pd.DataFrame, DbfInfo]:
    """Read a DBF. `encoding=None` detects cp850 vs cp1252; otherwise the given code page is used as is."""
    path = Path(path)
    table = DBF(str(path), encoding="latin-1", char_decode_errors="replace", parserclass=LenientFieldParser,
                ignore_missing_memofile=True, load=False)
    fields = [DbfField(f.name, f.type, f.length, f.decimal_count) for f in table.fields]
    names = [f.name for f in fields]
    records = [tuple(rec[n] for n in names) for rec in table]
    df = pd.DataFrame.from_records(records, columns=names) if records else pd.DataFrame(columns=names)
    # integer N fields come back as float with NaN for blanks; keep them as nullable integers
    for f in fields:
        if f.type == "N" and f.decimals == 0 and f.name in df.columns:
            try:
                df[f.name] = pd.to_numeric(df[f.name], errors="coerce").astype("Int64")
            except (TypeError, ValueError):
                pass
    # strip text (dbfread strips trailing spaces; leading ones are not data in Sinan)
    text_cols = [f.name for f in fields if f.type == "C"]
    for c in text_cols:
        df[c] = df[c].map(lambda v: v.strip() if isinstance(v, str) else v)
    if encoding is None:
        samples: list[str] = []
        for c in text_cols:
            samples.extend(v for v in df[c].head(max_sample).tolist() if isinstance(v, str))
        encoding, note = detect_encoding(samples)
    else:
        note = f"codificação fixada pelo usuário: {encoding}"
    for c in text_cols:
        df[c] = _recode(df[c], encoding)
    info = DbfInfo(path=path, fields=fields, n_records_header=table.header.numrecords, n_records_read=len(df),
                   encoding=encoding, encoding_note=note)
    if info.n_records_header != info.n_records_read:
        info.notes.append(f"o cabeçalho do DBF declara {info.n_records_header} registros e {info.n_records_read} "
                          f"foram lidos (a diferença são registros marcados como apagados no DBF)")
    return df, info


def is_date(v) -> bool:
    return isinstance(v, (dt.date, dt.datetime))
