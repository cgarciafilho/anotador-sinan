"""Minimal dBase III writer in pure Python, for synthetic test files (no new dependency).

Field spec: (name, type, length, decimals). Types: C (text, cp850 by default), N (int/float or None), D (date or None),
L (bool or None). Values are padded/justified the way dBase expects; None becomes blanks.
"""
from __future__ import annotations

import datetime as dt
import struct
from pathlib import Path


def write_dbf(path: Path, fields: list[tuple[str, str, int, int]], records: list[dict], encoding: str = "cp850",
              deleted: set[int] | None = None) -> Path:
    deleted = deleted or set()
    rec_len = 1 + sum(f[2] for f in fields)
    hdr_len = 32 + 32 * len(fields) + 1
    today = dt.date.today()
    with open(path, "wb") as fh:
        fh.write(struct.pack("<BBBBIHH20x", 0x03, today.year - 1900, today.month, today.day, len(records), hdr_len, rec_len))
        for name, ftype, length, dec in fields:
            fh.write(struct.pack("<11sc4xBB14x", name.encode("ascii"), ftype.encode("ascii"), length, dec))
        fh.write(b"\r")
        for i, rec in enumerate(records):
            fh.write(b"*" if i in deleted else b" ")
            for name, ftype, length, dec in fields:
                fh.write(_encode(rec.get(name), ftype, length, dec, encoding))
        fh.write(b"\x1a")
    return path


def _encode(v, ftype: str, length: int, dec: int, encoding: str) -> bytes:
    if ftype == "C":
        s = "" if v is None else str(v)
        b = s.encode(encoding, errors="replace")[:length]
        return b.ljust(length, b" ")
    if ftype == "N":
        if v is None or v == "":
            return b" " * length
        if isinstance(v, str):
            s = v
        elif dec:
            s = f"{float(v):.{dec}f}"
        else:
            s = str(int(v))
        return s.encode("ascii")[-length:].rjust(length, b" ")
    if ftype == "D":
        if v is None or v == "":
            return b" " * 8
        if isinstance(v, str):
            return v.encode("ascii").ljust(8, b" ")[:8]
        return v.strftime("%Y%m%d").encode("ascii")
    if ftype == "L":
        if v is None:
            return b"?"
        return b"T" if v else b"F"
    raise ValueError(f"tipo não suportado: {ftype}")
