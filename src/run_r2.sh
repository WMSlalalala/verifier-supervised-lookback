#!/bin/bash
cd /mnt/share/mwang49/guiodyssey
export HF_HOME=/mnt/share/mwang49/hf_cache
PY=/home/mwang49/miniconda3/envs/Sticker12/bin/python
# 等生成完
while ! grep -q GEN_DONE r2gen.log 2>/dev/null; do
  grep -qE "Traceback|CUDA out of memory|Killed" r2gen.log 2>/dev/null && { echo "GEN_FAILED"; exit 1; }
  sleep 20
done
echo "### r2 生成完成，开始评估 ###"
MODEL=Qwen/Qwen2.5-14B-Instruct DIRF=directory_r2.jsonl TAG=r2 $PY eval_r1.py || exit 1
echo "### R2 EVAL DONE ###"
