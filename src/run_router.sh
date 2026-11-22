#!/bin/bash
# 用 GPU1（GPU0 上有 Agent_sec 训练）
cd /mnt/share/mwang49/guiodyssey
export HF_HOME=/mnt/share/mwang49/hf_cache
export CUDA_VISIBLE_DEVICES=1
PY=/home/mwang49/miniconda3/envs/Sticker12/bin/python
echo "### 逐屏打分+记录路由信号 (多视角目录) ###"
MODEL=Qwen/Qwen2.5-14B-Instruct DIRF=directory_mv3.jsonl TAG=router_mv3 NV=3 $PY eval_router.py || exit 1
echo "### ROUTER DONE ###"
