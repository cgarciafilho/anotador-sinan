import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tests"))

import pytest  # noqa: E402


@pytest.fixture(scope="session")
def tab_dir() -> Path:
    return ROOT / "tabelas" / "tab_sinannet"
