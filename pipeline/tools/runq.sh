#!/bin/bash
# runq.sh: whisper jobs in a fixed order (one at a time). Each line of runq.txt: <vNN> <job>  job = orig | v2 | spine
SP=$(dirname "$0"); cd $SP
while true; do
  if [ -s runq_pri.txt ]; then line=$(head -n1 runq_pri.txt); sed -i 1d runq_pri.txt; else line=$(head -n1 runq.txt 2>/dev/null); [ -n "$line" ] && sed -i 1d runq.txt; fi; [ -z "$line" ] && { sleep 10; continue; }
  set -- $line; v=$1; job=$2; cd $SP/$v
  until [ -s src/a16.wav ] && grep -q FETCHED fetch.log 2>/dev/null; do sleep 10; done
  case $job in
    orig) python3 tx/run.py src/a16.wav tx/orig.json > tx/log.txt 2>&1 ;;
    v2) python3 tx/v2.py > tx/v2.txt 2>&1 ;;
    spine) python3 tx/run.py build/s16.wav build/spine_tx.json > build/tx.log 2>&1 && echo TX_OK >> build.log ;;
  esac
  echo "$v $job done" >> $SP/runq.log; cd $SP
done
