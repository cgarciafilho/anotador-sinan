"""docs/MANUAL.md describes what duplicates.py does. These tests fail when the code changes and the manual does not:
every label `classify()` can emit, every reason `_keep()` can give, every key, every column of the two sheets, every
field each profile reads and every numeric constant must appear in the manual (METODO.md, 2026-10-28)."""
from __future__ import annotations

import ast
import datetime as dt
import re
from pathlib import Path

import pandas as pd

from sinan_anotador import duplicates
from sinan_anotador.duplicates import KEYS, build_tables, detect_profile

ROOT = Path(__file__).resolve().parents[1]
MANUAL = (ROOT / "docs" / "MANUAL.md").read_text(encoding="utf-8")
SOURCE = (ROOT / "src" / "sinan_anotador" / "duplicates.py").read_text(encoding="utf-8")


def _returned_strings(func_name: str, position: int) -> list[str]:
    """Literal segments of the string in `position` of every `return (…, …)` inside the function (f-strings contribute
    their constant parts)."""
    tree = ast.parse(SOURCE)
    fn = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == func_name)
    out: list[str] = []
    for node in ast.walk(fn):
        if not isinstance(node, ast.Return) or not isinstance(node.value, ast.Tuple):
            continue
        el = node.value.elts[position]
        if isinstance(el, ast.Constant) and isinstance(el.value, str):
            out.append(el.value)
        elif isinstance(el, ast.JoinedStr):
            out.extend(v.value for v in el.values if isinstance(v, ast.Constant) and isinstance(v.value, str))
    return out


def test_every_suggested_label_is_in_the_manual():
    segments = [s for s in _returned_strings("classify", 0) if len(s.strip()) >= 4]
    assert segments, "classify() returned no literal labels; the extractor is broken"
    missing = [s for s in segments if s not in MANUAL]
    assert not missing, f"tipo_sugerido não descrito no manual: {missing}"


def test_every_keep_reason_is_in_the_manual():
    reasons = _returned_strings("_keep", 1)
    assert reasons
    missing = [s for s in reasons if s not in MANUAL]
    assert not missing, f"motivo_ficha_sugerida não descrito no manual: {missing}"


def test_keys_and_constants_are_in_the_manual():
    for k in KEYS:
        assert f"`{k}`" in MANUAL, k
    weeks, rem = divmod(duplicates.GESTATION_WINDOW_DAYS, 7)
    assert rem == 0
    for text in (f"{duplicates.GESTATION_WINDOW_DAYS} dias", f"{weeks} semanas", f"{duplicates.TRANSFER_GAP_DAYS} dias",
                 f"{duplicates.SIMILARITY:.2f}".replace(".", ","), f"{duplicates.MAX_BLOCK} registros"):
        assert text in MANUAL, text


def test_profile_fields_and_codes_are_in_the_manual():
    cases = {
        "tb": ("TuberculNET5_0", ["TRATAMENTO", "SITUA_ENCE", "DT_INIC_TR", "DT_ENCERRA", "DT_DIAG"]),
        "hans": ("HansNET", ["MODOENTR", "TPALTA_N", "DTINICTRAT", "DTALTA_N", "DT_DIAG"]),
        "sifilis_gestante": ("GestSifNET", ["DT_DIAG", "CS_GESTANT"]),
        "aids": ("AidsNET", ["DT_DIAG"]),
        "agudo": ("DengueNET", ["DT_SIN_PRI"]),
    }
    for kind, (stem, cols) in cases.items():
        prof = detect_profile(stem, cols)
        assert prof.kind == kind
        assert f"`{kind}`" in MANUAL, kind
        for f in (prof.event, prof.entry, prof.closure, prof.start, prof.end):
            if f:
                assert f"`{f}`" in MANUAL, f"{kind}: campo {f} não citado no manual"
        for codes in (prof.entry_transfer, prof.entry_reentry, prof.close_transfer):
            for c in codes:
                assert f"`{c}`" in MANUAL, f"{kind}: código {c} não citado no manual"


def test_sheet_columns_are_in_the_manual():
    rec = {"NU_NOTIFIC": "1", "DT_NOTIFIC": dt.date(2025, 1, 1), "NM_PACIENT": "ANA MARIA SILVA", "DT_NASC": dt.date(1990, 1, 1),
           "CS_SEXO": "F", "NM_MAE_PAC": "RITA SILVA", "ID_MUNICIP": "230440", "ID_UNIDADE": "1", "ID_MN_RESI": "230440",
           "NDUPLIC_N": "", "IN_VINCULA": "", "DT_SIN_PRI": dt.date(2024, 12, 30)}
    df = pd.DataFrame([rec, {**rec, "NU_NOTIFIC": "2", "DT_NOTIFIC": dt.date(2025, 1, 3)}])
    full, short, stats = build_tables(df, list(df.columns), "DengueNET")
    assert stats["pairs"] == 1
    side = re.compile(r"^[A-Z][A-Z0-9_]*(_rotulo)?_[AB]$")   # DBF fields side by side: described generically
    for col in list(full.columns) + list(short.columns):
        if side.match(col):
            continue
        assert f"`{col}`" in MANUAL, f"coluna {col} não descrita no manual"


def test_manual_ships_in_the_zip_and_is_linked():
    build = (ROOT / "build" / "build_windows_zip.sh").read_text(encoding="utf-8")
    assert "MANUAL.md" in build
    assert "MANUAL.md" in (ROOT / "build" / "LEIA-ME.txt").read_text(encoding="utf-8")
    assert "docs/MANUAL.md" in (ROOT / "README.md").read_text(encoding="utf-8")
