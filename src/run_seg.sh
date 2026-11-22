#!/bin/bash
cd /mnt/share/mwang49/guiodyssey
export HF_HOME=/mnt/share/mwang49/hf_cache
PY=/home/mwang49/miniconda3/envs/Sticker12/bin/python
# 等 r2 主评估结束
while ! grep -q "R2 EVAL DONE" r2run.log 2>/dev/null; do
  grep -qE "GEN_FAILED|Traceback" r2run.log 2>/dev/null && { echo "SEG_ABORT: r2 主评估失败"; exit 1; }
  sleep 20
done
echo "### 分段消融: 仅左段(内容特征) ###"
MODEL=Qwen/Qwen2.5-14B-Instruct DIRF=directory_r2.jsonl TAG=r2left SEG=left $PY eval_seg.py || exit 1
echo "### 分段消融: 仅右段(字段名) ###"
MODEL=Qwen/Qwen2.5-14B-Instruct DIRF=directory_r2.jsonl TAG=r2right SEG=right $PY eval_seg.py || exit 1
echo "### SEG ABLATION DONE ###"
