"""External lookup tables referenced by .def lines of the form `<T><label>, <CODE_FIELD>, <NAME_FIELD>, <file.dbf>`
(unidanet.dbf for health units by CNES code, ocupanet.dbf for CBO, regionet.dbf, paisnet.dbf, distrnet.dbf, bairrnet.dbf,
agravnet.dbf). TabWin ships them as DBF; a CSV with the same stem (`unidanet.csv` or `unidanet.csv.gz`, columns
<CODE_FIELD>,<NAME_FIELD> or `codigo,nome`, or simply the first two columns) is accepted too and wins over the DBF, so a table
built from the public CNES files (`scripts/make_unidanet_csv.py`) can replace the 2021 snapshot while the DBF complements it.

A LookupTable quacks like a Cnv for `annotate.label_for`: `.name`, `.width` (0 = never cut the code), `.lookup(code)`.
"""
from __future__ import annotations

import csv
import gzip
from dataclasses import dataclass, field
from pathlib import Path

from .cnv import find_cnv


@dataclass
class LookupTable:
    name: str
    path: Path
    code_field: str
    name_field: str
    width: int = 0
    n_rows: int = 0
    _exact: dict[str, str] = field(default_factory=dict, repr=False)
    _numeric: dict[int, str] = field(default_factory=dict, repr=False)
    notes: list[str] = field(default_factory=list)

    @property
    def categories(self) -> list[tuple[str, str]]:     # not written to the dictionary sheet in full (can be huge)
        return []

    def add(self, code: str, label: str):
        code = code.strip()
        label = " ".join(label.split())
        if not code or not label:
            return
        self._exact.setdefault(code, label)
        if code.isdigit():
            self._numeric.setdefault(int(code), label)
        self.n_rows += 1

    def lookup(self, code: str) -> str | None:
        if code == "":
            return None
        lab = self._exact.get(code)
        if lab is None and code.isdigit():
            lab = self._numeric.get(int(code))
        return lab


def find_lookup_files(name: str, tab_dir: Path) -> list[Path]:
    """All files on disk for a `.def` table name, best first: `unidanet.csv`, then `unidanet.csv.gz`, then `unidanet.dbf`
    (case-insensitive). A CSV is a table we built or updated ourselves (e.g. from the public CNES files), so it beats the DBF
    that TabWin ships; the DBF stays as a complement for codes the CSV lacks (see `annotate.lookup_chain`)."""
    stem = Path(name).stem
    found: list[Path] = []
    for cand in (stem + ".csv", stem + ".csv.gz", name):
        p = find_cnv(cand, tab_dir)
        if p is not None and p not in found:
            found.append(p)
    return found


def find_lookup_file(name: str, tab_dir: Path) -> Path | None:
    """The best file for a `.def` table name (see `find_lookup_files`), or None."""
    files = find_lookup_files(name, tab_dir)
    return files[0] if files else None


def _pick_columns(columns: list[str], code_field: str, name_field: str, notes: list[str]) -> tuple[str, str]:
    up = {c.upper(): c for c in columns}
    code = up.get(code_field.upper()) or up.get("CODIGO") or up.get("CO_CNES") or up.get("COD")
    name = up.get(name_field.upper()) or up.get("NOME") or up.get("NO_FANTASIA") or up.get("DESCRICAO")
    if code is None or name is None:
        if len(columns) == 2:        # a bare two-column table (code, name) is unambiguous
            code, name = columns
            notes.append(f"colunas {code_field}/{name_field} não encontradas; usadas {code} e {name}")
        else:
            missing = [f for f, c in ((code_field, code), (name_field, name)) if c is None]
            raise ValueError(f"sem a coluna {', '.join(missing)} (colunas: {', '.join(columns[:8])}"
                             f"{', ...' if len(columns) > 8 else ''})")
    return code, name


_CACHE: dict[tuple, LookupTable] = {}


def load_lookup(path: Path, code_field: str, name_field: str) -> LookupTable:
    """Parse a lookup table; results are cached per (path, mtime, columns) for the life of the process."""
    path = Path(path)
    key = (str(path.resolve()), path.stat().st_mtime_ns, code_field.upper(), name_field.upper())
    if key not in _CACHE:
        _CACHE[key] = _load_lookup(path, code_field, name_field)
    return _CACHE[key]


def _load_lookup(path: Path, code_field: str, name_field: str) -> LookupTable:
    table = LookupTable(name=path.name, path=path, code_field=code_field, name_field=name_field)
    if path.suffix.lower() == ".dbf":
        from .dbf import read_dbf
        df, info = read_dbf(path)
        code_col, name_col = _pick_columns(list(df.columns), code_field, name_field, table.notes)
        table.notes.append(f"{info.encoding_note}")
        for c, n in zip(df[code_col].tolist(), df[name_col].tolist()):
            if c is None or n is None:
                continue
            table.add(str(c if not isinstance(c, float) else int(c)), str(n))
    else:
        raw = gzip.decompress(path.read_bytes()) if path.name.lower().endswith(".gz") else path.read_bytes()
        try:
            text = raw.decode("utf-8-sig")
        except UnicodeDecodeError:
            text = raw.decode("latin-1")
        rows = list(csv.DictReader(text.splitlines(), delimiter=";" if text.split("\n", 1)[0].count(";") > text.split("\n", 1)[0].count(",") else ","))
        if not rows:
            raise ValueError(f"{path.name}: CSV vazio")
        code_col, name_col = _pick_columns([c for c in rows[0].keys() if c], code_field, name_field, table.notes)
        for r in rows:
            table.add(r.get(code_col) or "", r.get(name_col) or "")
    if table.n_rows == 0:
        raise ValueError("tabela vazia")
    return table
