#!/bin/bash
# Amendment A8 (2026-11-16): two less answer-aligned texts on the second nuScenes bank.
# D1 (ranges in meters, no band words) and the object-list scene graph as relation triples,
# read by Qwen2.5 3B and 7B (Ollama), on the perceived states of the arm "s" of A6.
# Short runs (a few minutes each); resume-safe. Deletes nothing.
# usage (Git Bash, from anywhere): bash scripts/rev1/run_a8_nusc_alignment.sh
PROJ="/c/Users/drxuc/Desktop/phd/publications/llm navigation/Conference/NIPS2026/lvcworld"
cd "$PROJ" || exit 1
PY="$PROJ/env/lvcworld/Scripts/python.exe"
export PYTHONUTF8=1
OUT=exp_rev1/c2_nusc
LOG=$OUT/a8.log
QA=outputs/nusc_ext2/qa_nusc2.jsonl
ST=outputs/nusc_ext2/states_nusc2_rfdetr_u1224.json
echo "[A8] start $(date '+%F %T')" >> $LOG
for M in 3b 7b; do
  "$PY" scripts/paper/run_serializer_dladder.py --mode d1 --qa $QA --states $ST --bank-format repo --model qwen2.5:$M --out $OUT/d1_$M >> $LOG 2>&1 || { echo "[E] d1_$M FAILED" >> $LOG; exit 1; }
  echo "[A8] d1_$M done $(date +%T)" >> $LOG
  "$PY" scripts/rev1/b4_scenegraph.py --mode sg_triples --qa $QA --states $ST --model qwen2.5:$M --out $OUT/sg_triples_$M >> $LOG 2>&1 || { echo "[E] sg_triples_$M FAILED" >> $LOG; exit 1; }
  echo "[A8] sg_triples_$M done $(date +%T)" >> $LOG
  ollama stop qwen2.5:$M > /dev/null 2>&1
done
echo done > $OUT/A8_COMPLETE.marker
echo "[A8] complete $(date '+%F %T')" >> $LOG
