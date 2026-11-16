#!/bin/bash
# B10 (Orin), added 2026-11-15: the whole confirmatory bank (1328 questions) on the board.
# One session, same condition and harness as run_b10_orin_e2e.sh (25 W mode, desktop running,
# llama.cpp 11fe021, all layers on the GPU). Order: the serialized system first (one-pass
# detector pair on all frames, serializer, readers), then the VLM with the image and the
# serialized text on the 50 probe questions, then the VLM on the whole bank at reduced and at
# full resolution.
# usage: bash run_b10_orin_fullbank.sh        (writes ~/rev1/out_e2e_full1328/; out_e2e_fullbank/ is an aborted first start in which only 87 frames were perceived because the camera intrinsics of the other recordings were not yet on the board)
cd ~/rev1
export B10_E2E_OUT=out_e2e_full1328
export B10_SERVER=~/rev1/llama.cpp-11fe021/build-cuda/bin/llama-server
O=$B10_E2E_OUT; mkdir -p $O
log () { echo "$(date +%H:%M:%S) $*" >> $O/session.log; }
log "start; gdm $(systemctl is-active gdm 2>/dev/null); $(nvpmodel -q | head -1); $(free -m | sed -n 2p)"
python3 b10_orin_fullbank.py perceive > $O/log_perceive.txt 2>&1; log "perceive done (rc $?)"
python3 b10_orin_fullbank.py prompts  > $O/log_prompts.txt 2>&1;  log "prompts done (rc $?)"
bench () { python3 b10_board_bench.py --threads 6 --ngl 99 --mem-max none --out-root $O "$@" > "$O/log_$2.txt" 2>&1; log "bench $2 done"; }
VL="--model models/Qwen2.5-VL-3B-Instruct-Q4_K_M.gguf --mmproj models/mmproj-Qwen2.5-VL-3B-Instruct-f16.gguf --pixel"
bench --name full-qwen2.5-3b   --model models/qwen2.5-3b-q4km.gguf   --probe data/full_onboard.jsonl --laptop-key light1-3b
bench --name full-qwen2.5-1.5b --model models/qwen2.5-1.5b-q4km.gguf --probe data/full_onboard.jsonl --laptop-key light1-3b
bench --name full-qwen2.5-7b   --model models/qwen2.5-7b-q4km.gguf   --probe data/full_onboard.jsonl --laptop-key light1-7b
bench --name hyb-qwen2.5vl-3b    $VL --probe data/probe50_hybrid.jsonl    --laptop-key qwen2.5vl-3b
bench --name hyb-qwen2.5vl-3b-lr $VL --probe data/probe50_hybrid_lr.jsonl --laptop-key qwen2.5vl-3b
bench --name full-qwen2.5vl-3b-lr $VL --probe data/full_onboard_lr.jsonl --laptop-key qwen2.5vl-3b
echo done > $O/FULLBANK_FAST_DONE; log "serialized system, hybrid and reduced-resolution VLM done"
bench --name full-qwen2.5vl-3b    $VL --probe data/full_onboard.jsonl    --laptop-key qwen2.5vl-3b
echo done > $O/FULLBANK_DONE; log "session done"
