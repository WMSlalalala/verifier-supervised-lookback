#!/bin/bash
# 全程仅用 GPU0，避让 GPU1 上可能的其他任务
cd /mnt/share/mwang49/guiodyssey
export HF_HOME=/mnt/share/mwang49/hf_cache
export CUDA_VISIBLE_DEVICES=0
PY=/home/mwang49/miniconda3/envs/Sticker12/bin/python
echo "### 生成多视角目录 K=3 ###"
MODEL=Qwen/Qwen2.5-7B-Instruct K=3 $PY gen_multiview.py || { echo "GEN_FAILED"; exit 1; }
echo "### 评估 NV=1（单视角对照）###"
MODEL=Qwen/Qwen2.5-14B-Instruct DIRF=directory_mv3.jsonl TAG=mv1 NV=1 $PY eval_mv.py || exit 1
echo "### 评估 NV=3（多视角）###"
MODEL=Qwen/Qwen2.5-14B-Instruct DIRF=directory_mv3.jsonl TAG=mv3 NV=3 $PY eval_mv.py || exit 1
echo "### MV DONE ###"
