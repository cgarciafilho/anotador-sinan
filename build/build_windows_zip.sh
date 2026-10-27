#!/bin/bash
# Builds anotador_sinan_v<version>.zip: Windows embeddable Python 3.13.5 + win_amd64 wheels of pandas/numpy/openpyxl/dbfread +
# src/sinan_anotador + tabelas/ + anotar.bat + LEIA-ME.txt + LICENSE. The version comes from src/sinan_anotador/__init__.py.
# Needs: curl, a Linux Python 3 with pip (only to download wheels), network to python.org and PyPI.
# Usage: build/build_windows_zip.sh [out_dir]   (default: build/dist). The zip is not committed (.gitignore).
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(dirname "$HERE")"
OUT="${1:-$HERE/dist}"
PY_VER=3.13.5
EMB="python-${PY_VER}-embed-amd64.zip"
EMB_SHA256=7d2650fd9d1b9d002d4a315d5f354247fd6a44f30517c7ef577b08f57a0fb6d9
VERSION="$(sed -n 's/^__version__ = "\(.*\)"/\1/p' "$ROOT/src/sinan_anotador/__init__.py")"
[ -n "$VERSION" ] || { echo "ERRO: __version__ não encontrada em src/sinan_anotador/__init__.py" >&2; exit 1; }
STAGE="$OUT/anotador_sinan_v$VERSION"
PIP="${PIP:-python3 -m pip}"

mkdir -p "$OUT" "$HERE/wheels"
cd "$HERE"
# The embeddable zip comes from python.org. Some networks (the cloud session of 2026-10-22) block that host: put the
# file in build/ by hand, or set SEM_PYTHON=1 to assemble everything else into anotador_sinan_v<version>_SEM_PYTHON.zip for checking.
if [ ! -f "$EMB" ] && [ "${SEM_PYTHON:-0}" != "1" ]; then
    curl -sSL -o "$EMB" "https://www.python.org/ftp/python/${PY_VER}/${EMB}" || {
        echo "ERRO: não consegui baixar $EMB de python.org; copie o arquivo para $HERE ou rode com SEM_PYTHON=1" >&2; exit 1; }
fi
if [ "${SEM_PYTHON:-0}" = "1" ] && [ ! -f "$EMB" ]; then
    STAGE="${STAGE}_SEM_PYTHON"
    echo "AVISO: montando sem o Python embeddable (SEM_PYTHON=1); o zip NÃO roda no Windows, serve só para conferência" >&2
else
    echo "$EMB_SHA256  $EMB" | sha256sum -c
fi

rm -rf "$STAGE" && mkdir -p "$STAGE/python" "$STAGE/app"
if [ -f "$EMB" ]; then
    python3 -m zipfile -e "$EMB" "$STAGE/python"
fi
# The ._pth file fixes sys.path for the embeddable interpreter (which then ignores PYTHONPATH, i.e. runs isolated):
# the standard library zip, python\, the wheels in Lib\site-packages and our code in ..\app.
printf 'python313.zip\n.\nLib\\site-packages\n..\\app\n\n# Uncomment to run site.main() automatically\nimport site\n' > "$STAGE/python/python313._pth"

# wheels for Windows x64 / CPython 3.13, downloaded on Linux; versions pinned for reproducibility
$PIP download -q --dest "$HERE/wheels" --platform win_amd64 --only-binary=:all: --python-version 3.13 \
    --implementation cp "pandas==3.0.6" "numpy==2.5.4" "openpyxl==3.1.5" "dbfread==2.0.7" \
    "python-dateutil" "tzdata" "et-xmlfile"
$PIP install -q --no-deps --no-index --find-links "$HERE/wheels" --target "$STAGE/python/Lib/site-packages" \
    --platform win_amd64 --only-binary=:all: --python-version 3.13 --implementation cp \
    pandas numpy openpyxl dbfread python-dateutil tzdata et-xmlfile six 2>/dev/null || \
$PIP install -q --no-index --find-links "$HERE/wheels" --target "$STAGE/python/Lib/site-packages" \
    --platform win_amd64 --only-binary=:all: --python-version 3.13 --implementation cp \
    pandas numpy openpyxl dbfread

cp -r "$ROOT/src/sinan_anotador" "$STAGE/app/"
find "$STAGE/app" -name __pycache__ -type d -exec rm -rf {} +
mkdir -p "$STAGE/app/tab_sinannet"
cp "$ROOT"/tabelas/tab_sinannet/*.def "$ROOT"/tabelas/tab_sinannet/*.cnv "$STAGE/app/tab_sinannet/"
# external lookup tables (unidanet.dbf etc., or CSV equivalents), when present
for f in "$ROOT"/tabelas/tab_sinannet/*.dbf "$ROOT"/tabelas/tab_sinannet/*.DBF "$ROOT"/tabelas/tab_sinannet/*.csv; do
    [ -f "$f" ] && cp "$f" "$STAGE/app/tab_sinannet/"
done
# SESA-CE regionalisation (municipality -> ADS/SR), read by the duplicates sheets from the folder above tab_sinannet
cp "$ROOT/tabelas/regionalizacao_sesa_sr_ads.csv" "$STAGE/app/"
if [ -d "$ROOT/tabelas/dicionarios" ]; then
    mkdir -p "$STAGE/app/dicionarios" && cp "$ROOT"/tabelas/dicionarios/*.csv "$STAGE/app/dicionarios/" 2>/dev/null || true
fi
cp "$HERE/anotar.bat" "$HERE/LEIA-ME.txt" "$STAGE/"
cp "$ROOT/LICENSE" "$STAGE/LICENSE.txt"
sed -i "s/@VERSAO@/$VERSION/g" "$STAGE/LEIA-ME.txt"
# the .bat, the README and the licence must be readable by Windows: CRLF line endings
sed -i 's/\r$//; s/$/\r/' "$STAGE/anotar.bat" "$STAGE/LEIA-ME.txt" "$STAGE/LICENSE.txt"

ZIP="$OUT/$(basename "$STAGE").zip"
rm -f "$ZIP"
python3 - "$STAGE" "$ZIP" <<'PY'
import os, sys, zipfile
stage, out = sys.argv[1], sys.argv[2]
base = os.path.basename(stage)
with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as z:
    for root, _, files in os.walk(stage):
        for f in sorted(files):
            p = os.path.join(root, f)
            z.write(p, os.path.join(base, os.path.relpath(p, stage)))
print(out, os.path.getsize(out), "bytes")
PY
sha256sum "$ZIP"
echo "--- top-level contents ---"
python3 -m zipfile -l "$ZIP" | awk '{print $1}' | awk -F/ 'NF>=3{print $1"/"$2"/"$3} NF<3{print $0}' | sort -u | head -40
