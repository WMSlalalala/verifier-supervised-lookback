#!/bin/bash
cd /mnt/share/mwang49/guiodyssey
export HF_HOME=/mnt/share/mwang49/hf_cache
PY=/home/mwang49/miniconda3/envs/Sticker12/bin/python
rm -f directory_r3.jsonl
echo "### r3 生成：允许条目包含具体值 ###"
$PY gen_directory_r3.py || { echo "GEN_FAILED"; exit 1; }
echo "### r3 评估 ###"
MODEL=Qwen/Qwen2.5-14B-Instruct DIRF=directory_r3.jsonl TAG=r3 $PY eval_r1.py || exit 1
echo "### R3 DONE ###"
