#!/bin/bash
# B10 (Orin), added 2026-11-16 (amendments/A7_addendum2.md). In the full-image run of the VLM
# on the whole bank (out_e2e_full1328/full-qwen2.5vl-3b) the answers of questions 991 to 1328
# are the string "????????"; the server log shows no error. This script answers those 338
# questions again with a newly started server process, together with the 100 questions that
# precede the failure (891 to 990), which check that a new process gives the same answers.
# Same condition, harness, model files, prompts and images as run_b10_orin_fullbank.sh.
# It waits for the timing run that is queued before it (out_e2e_mintok/MINTOK_DONE).
# usage: bash run_b10_orin_vlfull_rerun.sh   (writes out_e2e_full1328/full-qwen2.5vl-3b-rerun/)
cd ~/rev1
until [ -f out_e2e_mintok/MINTOK_DONE ]; do sleep 30; done
export B10_E2E_OUT=out_e2e_full1328
export B10_SERVER=~/rev1/llama.cpp-11fe021/build-cuda/bin/llama-server
O=$B10_E2E_OUT
log () { echo "$(date +%H:%M:%S) $*" >> $O/session.log; }
log "full-image repeat run start; $(nvpmodel -q | head -1); $(free -m | sed -n 2p)"
python3 - > $O/log_vlfull_rerun_prep.txt 2>&1 <<'PY'
import json
from pathlib import Path
R = Path.home() / "rev1"
rows = [l for l in open(R / "data" / "full_onboard.jsonl", encoding="utf-8") if l.strip()]
old = [json.loads(l) for l in open(R / "out_e2e_full1328" / "full-qwen2.5vl-3b" / "items.jsonl", encoding="utf-8")]
assert len(rows) == len(old) == 1328
assert [json.loads(l)["qa_id"] for l in rows] == [r["qa_id"] for r in old]
bad = [i for i, r in enumerate(old) if r["raw"] == "????????"]
assert bad == list(range(990, 1328)), (bad[:3], len(bad))
keep = list(range(890, 1328))
with open(R / "data" / "full_onboard_rerun.jsonl", "w", encoding="utf-8") as f:
    for i in keep:
        f.write(rows[i] if rows[i].endswith("\n") else rows[i] + "\n")
print("failed answers:", len(bad), "| questions in the repeat run:", len(keep), "(100 before the failure + 338 failed)")
PY
log "repeat-run question file done (rc $?)"
python3 b10_board_bench.py --threads 6 --ngl 99 --mem-max none --out-root $O --name full-qwen2.5vl-3b-rerun \
  --model models/Qwen2.5-VL-3B-Instruct-Q4_K_M.gguf --mmproj models/mmproj-Qwen2.5-VL-3B-Instruct-f16.gguf --pixel \
  --probe data/full_onboard_rerun.jsonl --laptop-key qwen2.5vl-3b > $O/log_full-qwen2.5vl-3b-rerun.txt 2>&1
log "bench full-qwen2.5vl-3b-rerun done"
echo done > $O/VLFULL_RERUN_DONE; log "full-image repeat run done"
