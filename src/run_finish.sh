#!/bin/bash
# 收尾三件事串行：A 端到端(14B) -> B 第二reader(7B) -> C 留出集(OCR->验证->目录->B/D/C2/门控)
cd /mnt/share/mwang49/guiodyssey
export HF_HOME=/mnt/share/mwang49/hf_cache; export PYTORCH_ALLOC_CONF=expandable_segments:True
PY=/home/mwang49/miniconda3/envs/Sticker12/bin/python; OCRPY=/home/mwang49/miniconda3/envs/cuhkx/bin/python
M14=Qwen/Qwen2.5-14B-Instruct; M7=Qwen/Qwen2.5-7B-Instruct; HEAD=2000
free_of(){ echo $((49140 - $(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits -i $1 | tr -d ' '))); }
run14(){ # 跨两卡；合计可用>=34000 才跑；失败重试（脚本内有断点续传）
  for try in $(seq 1 30); do
    while :; do f0=$(free_of 0); f1=$(free_of 1); a0=$((f0-HEAD)); a1=$((f1-HEAD)); [ $a0 -lt 0 ]&&a0=0; [ $a1 -lt 0 ]&&a1=0
      [ $((a0+a1)) -ge 34000 ] && break; sleep 60; done
    MM="{\"0\":\"$((a0/1024))GiB\",\"1\":\"$((a1/1024))GiB\"}"
    echo "### [14B] $* try=$try ($(date +%H:%M)) MAXMEM=$MM ###"
    if CUDA_VISIBLE_DEVICES=0,1 MAXMEM="$MM" MODEL=$M14 env "${@:1:$#-1}" $PY "${!#}"; then return 0; fi
    echo "RETRY14 $* try=$try"; sleep 120
  done; echo "FAIL14 $*"; return 1; }
run1(){ # 单卡，需>=NEED
  NEED=$1; shift
  for try in $(seq 1 30); do
    G=""; while [ -z "$G" ]; do for g in 1 0; do [ $(free_of $g) -ge $NEED ] && { G=$g; break; }; done; [ -z "$G" ] && sleep 60; done
    echo "### [GPU$G] $* try=$try ($(date +%H:%M)) ###"
    if CUDA_VISIBLE_DEVICES=$G env "${@:1:$#-1}" $PY "${!#}"; then return 0; fi
    echo "RETRY1 $* try=$try"; sleep 120
  done; echo "FAIL1 $*"; return 1; }
echo "===== STAGE A: 门控端到端（14B）====="
run14 CASES=long  eval_gate_e2e.py || exit 1
run14 CASES=short eval_gate_e2e.py || exit 1
echo "===== STAGE B: 第二 reader 7B on long ====="
run1 18000 MODEL=$M7 CASES=long MODE=B eval_long.py || exit 1
run1 18000 MODEL=$M7 CASES=long MODE=D eval_long.py || exit 1
run1 18000 MODEL=$M7 CASES=long K=2 eval_calib.py || exit 1
run1 18000 MODEL=$M7 CASES=long eval_gate_e2e.py || exit 1
echo "===== STAGE C: 留出集 ====="
while ! grep -q DL_DONE dl_holdout.log 2>/dev/null; do sleep 30; done

G=""; while [ -z "$G" ]; do for g in 1 0; do [ $(free_of $g) -ge 4000 ] && { G=$g; break; }; done; [ -z "$G" ] && sleep 60; done
CUDA_VISIBLE_DEVICES=$G $OCRPY ocr_shots.py || { echo "OCR_FAILED"; exit 1; }
$PY verify_holdout.py || exit 1
run1 18000 MODEL=$M7 gen_directory_holdout.py || exit 1
run14 CASES=holdout MODE=B eval_long.py || exit 1
run14 CASES=holdout MODE=D eval_long.py || exit 1
run14 CASES=holdout K=2 eval_calib.py || exit 1
run14 CASES=holdout eval_gate_e2e.py || exit 1
echo "===== 留出集固定 τ 分析 ====="; CASES=holdout $PY analyze_gate.py
echo "### FINISH DONE ###"
