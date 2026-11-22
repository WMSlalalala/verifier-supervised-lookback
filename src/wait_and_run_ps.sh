#!/bin/bash
# 等 GPU0 腾出 >=32GB 再跑逐屏打分实验，避让其他任务
cd /mnt/share/mwang49/guiodyssey
NEED=32000          # MiB
MAXWAIT=14400       # 最多等 4 小时
t=0
while [ $t -lt $MAXWAIT ]; do
  used=$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits -i 0 2>/dev/null | tr -d ' ')
  total=$(nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits -i 0 2>/dev/null | tr -d ' ')
  free=$((total - used))
  if [ "$free" -ge "$NEED" ]; then
    echo "[$(date +%H:%M)] GPU0 空闲 ${free}MiB >= ${NEED}MiB，启动实验"
    exec ./run_ps.sh
  fi
  [ $((t % 600)) -eq 0 ] && echo "[$(date +%H:%M)] 等待中: GPU0 空闲 ${free}MiB / 需要 ${NEED}MiB"
  sleep 60; t=$((t+60))
done
echo "WAIT_TIMEOUT: 等待 4 小时后 GPU0 仍不足，未启动"
