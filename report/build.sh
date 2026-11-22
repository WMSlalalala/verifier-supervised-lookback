#!/bin/bash
cd "$(dirname "$0")" && pdflatex -interaction=nonstopmode main.tex >/dev/null && bibtex main >/dev/null; pdflatex -interaction=nonstopmode main.tex >/dev/null; pdflatex -interaction=nonstopmode main.tex | grep -E "^!|Output written"; grep -cE "Warning.*undefined" main.log
