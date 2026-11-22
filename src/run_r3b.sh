#!/bin/bash
# 全程仅用 GPU0，避让 GPU1 上的 EEG 训练任务
cd /mnt/share/mwang49/guiodyssey
export HF_HOME=/mnt/share/mwang49/hf_cache
export CUDA_VISIBLE_DEVICES=0
PY=/home/mwang49/miniconda3/envs/Sticker12/bin/python
echo "### r3 生成（续传）###"
$PY gen_directory_r3.py || { echo "GEN_FAILED"; exit 1; }
echo "### r3 评估 ###"
MODEL=Qwen/Qwen2.5-14B-Instruct DIRF=directory_r3.jsonl TAG=r3 $PY eval_r1.py || exit 1
echo "### oracle 修正指标重算 ###"
MODEL=Qwen/Qwen2.5-14B-Instruct $PY oracle_fixed.py || exit 1
echo "### ALL DONE ###"
