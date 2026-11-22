#!/bin/bash
cd /mnt/share/mwang49/guiodyssey
export HF_HOME=/mnt/share/mwang49/hf_cache
export MODEL=Qwen/Qwen2.5-14B-Instruct
PY=/home/mwang49/miniconda3/envs/Sticker12/bin/python
echo "### STAGE 1: oracle directory upper bound ###"
$PY oracle_directory.py
echo "### STAGE 2: BM25+LLM hybrid baseline ###"
$PY hybrid_baseline.py
echo "### ALL DONE ###"
