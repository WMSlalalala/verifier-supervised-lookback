#!/bin/bash
# 外部测试集：等下载 -> OCR -> 验证 -> 目录 -> 用全部188训练(ext) -> 在新集上 定位/端到端 + 全历史/索引对照
cd /mnt/share/mwang49/guiodyssey; export HF_HOME=/mnt/share/mwang49/hf_cache; export PYTORCH_ALLOC_CONF=expandable_segments:True
PY=/home/mwang49/miniconda3/envs/Sticker12/bin/python; OCRPY=/home/mwang49/miniconda3/envs/cuhkx/bin/python
free_of(){ echo $((49140 - $(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits -i $1 | tr -d ' '))); }
pick(){ NEED=$1; while :; do for g in 1 0; do [ $(free_of $g) -ge $NEED ] && { echo $g; return; }; done; sleep 90; done; }
while ! grep -q DL_DONE dl_more.log 2>/dev/null; do sleep 60; done
echo "===== OCR ====="
G=$(pick 5000); CUDA_VISIBLE_DEVICES=$G OUT=/mnt/share/mwang49/guiodyssey/parse_more.jsonl $OCRPY ocr_shard.py || exit 1
cat parse_more.jsonl >> parse_odyssey.jsonl
echo "===== 验证 + 目录 ====="
$PY verify_more.py || exit 1
G=$(pick 18000); CUDA_VISIBLE_DEVICES=$G $PY gen_directory_more.py || exit 1
$PY build_scorer_more.py || exit 1
echo "===== 打分器：全部188训练，在新集上评 ====="
G=$(pick 26000); CUDA_VISIBLE_DEVICES=$G FOLD=ext $PY train_scorer.py || exit 1
echo "===== 未训练对照 ====="
G=$(pick 18000); CUDA_VISIBLE_DEVICES=$G SET=_more $PY score_untrained.py || exit 1
echo "===== 全历史 / 索引 对照（14B）====="
G=$(pick 34000); CUDA_VISIBLE_DEVICES=$G CASES=more MODE=B $PY eval_long.py || exit 1
G=$(pick 34000); CUDA_VISIBLE_DEVICES=$G CASES=more MODE=D $PY eval_long.py || exit 1
echo "===== 打分器端到端（单屏 + 带历史）====="
G=$(pick 34000); CUDA_VISIBLE_DEVICES=$G SRC=trained SET=_more $PY read_scorer.py || exit 1
G=$(pick 34000); CUDA_VISIBLE_DEVICES=$G SRC=trained SET=_more HIST=1 $PY read_scorer.py || exit 1
echo "### EXT DONE ###"
