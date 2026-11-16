#!/bin/bash
# B10 (Orin), 2026-11-16 (amendments/A7_addendum3.md): the 338 questions of the full-image VLM
# run that failed, and the 100 questions before them, answered again with the reload rule of
# b10_board_bench_guard.py (restart the server after a degenerate output, ask once more).
# Question file: data/full_onboard_rerun.jsonl (written by run_b10_orin_vlfull_rerun.sh).
# usage: bash run_b10_orin_vlfull_guard.sh    (writes out_e2e_full1328/full-qwen2.5vl-3b-guard/)
cd ~/rev1
export B10_SERVER=~/rev1/llama.cpp-11fe021/build-cuda/bin/llama-server
O=out_e2e_full1328
log () { echo "$(date +%H:%M:%S) $*" >> $O/session.log; }
log "full-image run with the reload rule start; $(nvpmodel -q | head -1); $(free -m | sed -n 2p)"
test "$(wc -l < data/full_onboard_rerun.jsonl)" = 438 || { log "question file missing"; exit 1; }
python3 b10_board_bench_guard.py --name full-qwen2.5vl-3b-guard --probe data/full_onboard_rerun.jsonl --out-root $O > $O/log_full-qwen2.5vl-3b-guard.txt 2>&1
log "bench full-qwen2.5vl-3b-guard done (rc $?)"
echo done > $O/VLFULL_GUARD_DONE; log "full-image run with the reload rule done"
