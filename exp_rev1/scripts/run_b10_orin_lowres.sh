#!/bin/bash
# B10 (Orin), added 2026-11-15 after the simulated review: the 3B VLM with the camera frame
# reduced to at most 0.40 megapixels (672 x 560, the size that the image processor of the
# model produces for max_pixels = 401408, as in the reduced-resolution arms of the paper),
# and the full-resolution run repeated in the same session. Same condition and same harness
# as run_b10_orin_e2e.sh (25 W mode, desktop running, llama.cpp 11fe021, all layers on GPU).
# usage: bash run_b10_orin_lowres.sh        (writes ~/rev1/out_e2e_lowres/)
cd ~/rev1
export B10_E2E_OUT=out_e2e_lowres
export B10_SERVER=~/rev1/llama.cpp-11fe021/build-cuda/bin/llama-server
O=$B10_E2E_OUT; mkdir -p $O
log () { echo "$(date +%H:%M:%S) $*" >> $O/session.log; }
log "start; gdm $(systemctl is-active gdm 2>/dev/null); $(nvpmodel -q | head -1); $(free -m | sed -n 2p)"

# reduced copies of the probe images and probe files that point to them
python3 - > $O/log_resize.txt 2>&1 <<'PY'
import json
from pathlib import Path
from PIL import Image
D = Path.home() / "rev1" / "data"
(D / "images_lr").mkdir(exist_ok=True)
n = 0
for p in sorted((D / "images").glob("*.png")):
    im = Image.open(p).convert("RGB")
    assert im.size == (1224, 1024), (p.name, im.size)
    q = D / "images_lr" / p.name
    if not q.exists():
        im.resize((672, 560), Image.BICUBIC).save(q)
    n += 1
print("reduced images:", n, "size 672x560 =", 672 * 560, "pixels")
for src, dst in (("probe50.jsonl", "probe50_lr.jsonl"), ("series_onboard.jsonl", "series_onboard_lr.jsonl")):
    rows = [json.loads(l) for l in open(D / src, encoding="utf-8")]
    for r in rows:
        assert r["image"].startswith("images/"), r["image"]
        r["image"] = "images_lr/" + r["image"][len("images/"):]
    with open(D / dst, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")
    print("wrote", dst, len(rows))
PY
log "resize done"
# a copy of the series harness that reads the reduced series file; nothing else differs
sed 's#data/series_onboard.jsonl#data/series_onboard_lr.jsonl#' b10_series.py > b10_series_lr.py

VL="--model models/Qwen2.5-VL-3B-Instruct-Q4_K_M.gguf --mmproj models/mmproj-Qwen2.5-VL-3B-Instruct-f16.gguf --pixel"
bench () { python3 b10_board_bench.py --threads 6 --ngl 99 --mem-max none --out-root $O "$@" > "$O/log_$2.txt" 2>&1; log "bench $2 done"; }
bench --name qwen2.5vl-3b    $VL --laptop-key qwen2.5vl-3b
bench --name qwen2.5vl-3b-lr $VL --probe data/probe50_lr.jsonl --laptop-key qwen2.5vl-3b
python3 b10_series.py    --name qwen2.5vl-3b    $VL > "$O/log_series_qwen2.5vl-3b.txt" 2>&1;    log "series full done"
python3 b10_series_lr.py --name qwen2.5vl-3b-lr $VL > "$O/log_series_qwen2.5vl-3b-lr.txt" 2>&1; log "series lr done"
echo done > $O/LOWRES_DONE; log "session done"
