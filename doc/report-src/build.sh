#!/usr/bin/env bash
# Build doc/report-src/main.pdf (the published copy is doc/Final-Report.pdf).
# The bibliography is inline, so no BibTeX pass is needed.
set -e
cd "$(dirname "$0")"
if command -v tectonic >/dev/null 2>&1; then
  tectonic main.tex
else
  pdflatex -interaction=nonstopmode main.tex && pdflatex -interaction=nonstopmode main.tex
fi
