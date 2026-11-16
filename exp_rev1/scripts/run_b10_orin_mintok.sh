#!/bin/bash
# B10 (Orin), added 2026-11-15 after an internal check: llama.cpp warns at load that Qwen-VL
# models "require at minimum 1024 image tokens to function correctly on grounding tasks". The
# reduced image of the earlier sessions (672 x 560) gives 480 image tokens. This session times
# the 3B VLM on the timing set of 50 questions with the camera frame reduced to 980 x 840,
# which gives 35 x 30 = 1050 image tokens, the smallest size of this aspect ratio above that
# minimum. Time and energy only; 50 questions do not estimate accuracy.
# Same condition and harness as run_b10_orin_lowres.sh. It waits for the follow-up run of the
# full-bank session (out_e2e_full1328/HYBRID_LR_DONE).
# usage: bash run_b10_orin_mintok.sh        (writes ~/rev1/out_e2e_mintok/)
cd ~/rev1
until [ -f out_e2e_full1328/HYBRID_LR_DONE ]; do sleep 30; done
export B10_E2E_OUT=out_e2e_mintok
export B10_SERVER=~/rev1/llama.cpp-11fe021/build-cuda/bin/llama-server
O=$B10_E2E_OUT; mkdir -p $O
log () { echo "$(date +%H:%M:%S) $*" >> $O/session.log; }
log "start; gdm $(systemctl is-active gdm 2>/dev/null); $(nvpmodel -q | head -1); $(free -m | sed -n 2p)"
python3 - > $O/log_resize.txt 2>&1 <<'PY'
import json
from pathlib import Path
from PIL import Image
D = Path.home() / "rev1" / "data"
(D / "images_mr").mkdir(exist_ok=True)
n = 0
for p in sorted((D / "images").glob("*.png")):
    im = Image.open(p).convert("RGB")
    assert im.size == (1224, 1024), (p.name, im.size)
    q = D / "images_mr" / p.name
    if not q.exists():
        im.resize((980, 840), Image.BICUBIC).save(q)
    n += 1
print("reduced images:", n, "size 980x840 =", 980 * 840, "pixels")
for src, dst in (("probe50.jsonl", "probe50_mr.jsonl"), ("series_onboard.jsonl", "series_onboard_mr.jsonl")):
    rows = [json.loads(l) for l in open(D / src, encoding="utf-8")]
    for r in rows:
        assert r["image"].startswith("images/"), r["image"]
        r["image"] = "images_mr/" + r["image"][len("images/"):]
    with open(D / dst, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")
    print("wrote", dst, len(rows))
PY
log "resize done"
sed 's#data/series_onboard.jsonl#data/series_onboard_mr.jsonl#' b10_series.py > b10_series_mr.py
VL="--model models/Qwen2.5-VL-3B-Instruct-Q4_K_M.gguf --mmproj models/mmproj-Qwen2.5-VL-3B-Instruct-f16.gguf --pixel"
bench () { python3 b10_board_bench.py --threads 6 --ngl 99 --mem-max none --out-root $O "$@" > "$O/log_$2.txt" 2>&1; log "bench $2 done"; }
bench --name qwen2.5vl-3b-mr $VL --probe data/probe50_mr.jsonl --laptop-key qwen2.5vl-3b
python3 b10_series_mr.py --name qwen2.5vl-3b-mr $VL > "$O/log_series_qwen2.5vl-3b-mr.txt" 2>&1; log "series mr done"
echo done > $O/MINTOK_DONE; log "session done"
