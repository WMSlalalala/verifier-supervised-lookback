#!/bin/bash
cd /mnt/share/mwang49/guiodyssey
export HF_HOME=/mnt/share/mwang49/hf_cache
PY=/home/mwang49/miniconda3/envs/Sticker12/bin/python
rm -f writer_lora/adapter_model.safetensors directory_r1.jsonl
echo "### STAGE A: train writer (DPO, LoRA) ###"
MODEL=Qwen/Qwen2.5-7B-Instruct EPOCHS=3 BS=2 LR=1e-4 $PY train_writer.py || exit 1
echo "### STAGE B: rebuild directory with trained writer ###"
MODEL=Qwen/Qwen2.5-7B-Instruct $PY gen_directory_r1.py || exit 1
echo "### STAGE C: evaluate r1 directory ###"
MODEL=Qwen/Qwen2.5-14B-Instruct DIRF=directory_r1.jsonl TAG=r1 $PY eval_r1.py || exit 1
echo "### CLOSELOOP DONE ###"
