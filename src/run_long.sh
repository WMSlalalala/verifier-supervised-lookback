#!/bin/bash
# 长轨迹全流程：等下载 -> OCR -> 验证 case -> 补生成 r0 目录 -> 评估 B(全历史) 与 D(目录)。全程 GPU0。
cd /mnt/share/mwang49/guiodyssey
export HF_HOME=/mnt/share/mwang49/hf_cache
export CUDA_VISIBLE_DEVICES=0
PY=/home/mwang49/miniconda3/envs/Sticker12/bin/python
OCRPY=/home/mwang49/miniconda3/envs/cuhkx/bin/python
while ! grep -q DL_DONE dl_long.log 2>/dev/null; do sleep 30; done
echo "### STAGE 1: OCR ###"
$OCRPY ocr_shots.py || { echo "OCR_FAILED"; exit 1; }
echo "### STAGE 2: 验证 case ###"
$PY verify_long.py || exit 1
echo "### STAGE 3: 补生成 r0 目录 ###"
$PY gen_directory_long.py || exit 1
echo "### STAGE 4: 评估 B 全历史 ###"
MODEL=Qwen/Qwen2.5-14B-Instruct MODE=B $PY eval_long.py || exit 1
echo "### STAGE 5: 评估 D 目录 ###"
MODEL=Qwen/Qwen2.5-14B-Instruct MODE=D $PY eval_long.py || exit 1
echo "### LONG DONE ###"
