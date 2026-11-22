#!/bin/bash
# Point the scripts at your own data directory and Python interpreters.
# The scripts were run with absolute paths on the author's machine; this rewrites them in place.
#
#   ./configure.sh /path/to/your/guiodyssey /path/to/python /path/to/ocr-python
#
# DATA_DIR must contain: shots/ (GUI-Odyssey screenshots), annotations/ (its JSON),
# plus the files shipped in data/ and results/ of this repo.
set -e
DATA=${1:?usage: ./configure.sh DATA_DIR [PYTHON] [OCR_PYTHON]}
PY=${2:-$(command -v python3)}
OCRPY=${3:-$PY}
cd "$(dirname "$0")/src"
sed -i "s|/mnt/share/mwang49/guiodyssey|${DATA}|g" *.py *.sh
sed -i "s|/home/mwang49/miniconda3/envs/Sticker12/bin/python|${PY}|g" *.sh
sed -i "s|/home/mwang49/miniconda3/envs/cuhkx/bin/python|${OCRPY}|g" *.sh
echo "src/ now points at ${DATA}"
echo "  python:     ${PY}"
echo "  ocr python: ${OCRPY}"
