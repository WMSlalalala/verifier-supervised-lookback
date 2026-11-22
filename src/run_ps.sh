#!/bin/bash
cd /mnt/share/mwang49/guiodyssey
export HF_HOME=/mnt/share/mwang49/hf_cache
export CUDA_VISIBLE_DEVICES=0
PY=/home/mwang49/miniconda3/envs/Sticker12/bin/python
echo "### 逐屏打分 on r0 目录（对照 r0 单阶段 45.8%）###"
MODEL=Qwen/Qwen2.5-14B-Instruct DIRF=directory_r0.jsonl TAG=ps_r0 NV=1 $PY eval_perscreen.py || exit 1
echo "### 逐屏打分 on 多视角目录 NV=3（对照 mv3 单阶段 39.0%）###"
MODEL=Qwen/Qwen2.5-14B-Instruct DIRF=directory_mv3.jsonl TAG=ps_mv3 NV=3 $PY eval_perscreen.py || exit 1
echo "### PS DONE ###"
