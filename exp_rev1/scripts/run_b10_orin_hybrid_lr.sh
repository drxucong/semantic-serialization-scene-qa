#!/bin/bash
# B10 (Orin), added 2026-11-15 (amendments/A7_addendum1.md; exploratory): after the full-bank
# session has finished, the VLM with the reduced image (672 x 560) and the serialized text of the
# board's own states answers all 1328 confirmatory questions. Same condition and harness as
# run_b10_orin_fullbank.sh; results go into the folder of that session.
# usage: bash run_b10_orin_hybrid_lr.sh     (waits for out_e2e_full1328/FULLBANK_DONE)
cd ~/rev1
export B10_E2E_OUT=out_e2e_full1328
export B10_SERVER=~/rev1/llama.cpp-11fe021/build-cuda/bin/llama-server
O=$B10_E2E_OUT
until [ -f $O/FULLBANK_DONE ]; do sleep 30; done
log () { echo "$(date +%H:%M:%S) $*" >> $O/session.log; }
log "hybrid follow-up start; $(nvpmodel -q | head -1); $(free -m | sed -n 2p)"
python3 b10_orin_hybrid_full.py > $O/log_hybrid_prompts.txt 2>&1; log "hybrid prompts done (rc $?)"
python3 b10_board_bench.py --threads 6 --ngl 99 --mem-max none --out-root $O --name full-hyb-qwen2.5vl-3b-lr \
  --model models/Qwen2.5-VL-3B-Instruct-Q4_K_M.gguf --mmproj models/mmproj-Qwen2.5-VL-3B-Instruct-f16.gguf --pixel \
  --probe data/full_onboard_hybrid_lr.jsonl --laptop-key qwen2.5vl-3b > $O/log_full-hyb-qwen2.5vl-3b-lr.txt 2>&1
log "bench full-hyb-qwen2.5vl-3b-lr done"
echo done > $O/HYBRID_LR_DONE; log "hybrid (reduced image) on the full bank done"
