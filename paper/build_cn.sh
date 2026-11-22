#!/bin/bash
cd "$(dirname "$0")" && xelatex -interaction=nonstopmode main_cn.tex >/dev/null && bibtex main_cn >/dev/null; xelatex -interaction=nonstopmode main_cn.tex >/dev/null; xelatex -interaction=nonstopmode main_cn.tex | grep -E "^!|Output written"; grep -E "Warning.*(undefined|multiply)" main_cn.log | head
