#!/bin/bash
# B10 (Orin) end-to-end session. usage: bash run_b10_orin_e2e.sh <out-folder-name>
# One session, one condition: perception timing, probe states, on-board prompts,
# reader runs on the board's own states, co-resident memory, same-frame series for
# readers and VLMs, and the single-question runs of Table 15 repeated in the same
# session so that every Orin number comes from one condition.
cd ~/rev1
export B10_E2E_OUT="${1:-out_e2e}"
export B10_SERVER=~/rev1/llama.cpp-11fe021/build-cuda/bin/llama-server
O=$B10_E2E_OUT; mkdir -p $O
log () { echo "$(date +%H:%M:%S) $*" >> $O/session.log; }
log "start; gdm $(systemctl is-active gdm 2>/dev/null); $(nvpmodel -q | head -1); $(free -m | sed -n 2p)"
python3 b10_orin_perceive.py timing  > $O/log_timing.txt 2>&1;  log "timing done"
python3 b10_orin_perceive.py probe   > $O/log_probe.txt 2>&1;   log "probe done"
python3 b10_orin_perceive.py prompts > $O/log_prompts.txt 2>&1; log "prompts done"
bench () { python3 b10_board_bench.py --threads 6 --ngl 99 --mem-max none --out-root $O "$@" > "$O/log_$2.txt" 2>&1; log "bench $2 done"; }
# readers on the board's own perceived states (frame to answer)
bench --name e2e-qwen2.5-3b   --model models/qwen2.5-3b-q4km.gguf   --probe data/probe50_onboard.jsonl --laptop-key light1-3b
bench --name e2e-qwen2.5-7b   --model models/qwen2.5-7b-q4km.gguf   --probe data/probe50_onboard.jsonl --laptop-key light1-7b
bench --name e2e-qwen2.5-1.5b --model models/qwen2.5-1.5b-q4km.gguf --probe data/probe50_onboard.jsonl --laptop-key light1-3b
# detectors and reader resident together
$B10_SERVER -m models/qwen2.5-3b-q4km.gguf -t 6 -c 4096 --port 8099 --host 127.0.0.1 --load-mode none -np 1 --cache-ram 0 -ngl 99 > $O/coresident_server.log 2>&1 &
SP=$!; for i in $(seq 1 120); do curl -s -m 2 http://127.0.0.1:8099/health | grep -q ok && break; sleep 1; done
python3 b10_orin_perceive.py coresident > $O/log_coresident.txt 2>&1; kill $SP; wait $SP 2>/dev/null; log "coresident done"
# several questions on one frame
ser () { python3 b10_series.py "$@" > "$O/log_series_$2.txt" 2>&1; log "series $2 done"; }
ser --name qwen2.5-3b   --model models/qwen2.5-3b-q4km.gguf
ser --name qwen2.5-7b   --model models/qwen2.5-7b-q4km.gguf
ser --name qwen2.5-1.5b --model models/qwen2.5-1.5b-q4km.gguf
ser --name moondream    --model models/moondream2-text.gguf --mmproj models/moondream2-mmproj.gguf --pixel --ollama-moondream
ser --name qwen2.5vl-3b --model models/Qwen2.5-VL-3B-Instruct-Q4_K_M.gguf --mmproj models/mmproj-Qwen2.5-VL-3B-Instruct-f16.gguf --pixel
# the single-question runs of Table 15, same session
bench --name qwen2.5-0.5b --model models/qwen2.5-0.5b-q4km.gguf
bench --name qwen2.5-1.5b --model models/qwen2.5-1.5b-q4km.gguf
bench --name qwen2.5-3b   --model models/qwen2.5-3b-q4km.gguf
bench --name qwen2.5-7b   --model models/qwen2.5-7b-q4km.gguf
bench --name moondream    --model models/moondream2-text.gguf --mmproj models/moondream2-mmproj.gguf --pixel --ollama-moondream --laptop-key moondream
bench --name qwen2.5vl-3b --model models/Qwen2.5-VL-3B-Instruct-Q4_K_M.gguf --mmproj models/mmproj-Qwen2.5-VL-3B-Instruct-f16.gguf --pixel --laptop-key qwen2.5vl-3b
echo done > $O/SESSION_DONE; log "session done"
