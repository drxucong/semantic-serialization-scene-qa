#!/bin/bash
# B10 (Orin), 2026-11-16 (amendments/A7_addendum4.md): the 3B VLM on all 1328 confirmatory
# questions with the camera frame reduced to 980 x 840 pixels (35 x 30 = 1050 image tokens,
# the size of run_b10_orin_mintok.sh, just above the 1024 that the server names as the
# minimum for this model family). Same condition as the earlier sessions (25 W mode, desktop
# running, llama.cpp 11fe021, all layers on the GPU). The reload rule of
# b10_board_bench_guard.py is in force from the first question.
# Swap: the board has the compressed in-memory swap (zram) of the system image; the counters
# pswpin/pswpout of /proc/vmstat and SwapFree are sampled every 10 s during the run.
# usage: bash run_b10_orin_mr_full.sh    (writes out_e2e_full1328/full-qwen2.5vl-3b-mr/)
cd ~/rev1
export B10_SERVER=~/rev1/llama.cpp-11fe021/build-cuda/bin/llama-server
O=out_e2e_full1328
N=full-qwen2.5vl-3b-mr
log () { echo "$(date +%H:%M:%S) $*" >> $O/session.log; }
log "run at 980x840 start; gdm $(systemctl is-active gdm 2>/dev/null); $(nvpmodel -q | head -1); $(free -m | sed -n 2p); $(free -m | sed -n 3p)"
python3 - > $O/log_resize_mr_full.txt 2>&1 <<'PY'
import json
from pathlib import Path
from PIL import Image
D = Path.home() / "rev1" / "data"
(D / "images_full_mr").mkdir(exist_ok=True)
rows = [json.loads(l) for l in open(D / "full_onboard.jsonl", encoding="utf-8")]
lr = [json.loads(l) for l in open(D / "full_onboard_lr.jsonl", encoding="utf-8")]
assert [r["qa_id"] for r in rows] == [r["qa_id"] for r in lr]
n = 0
with open(D / "full_onboard_mr.jsonl", "w", encoding="utf-8") as f:
    for r, l in zip(rows, lr):
        name = Path(l["image"]).name                      # the file name of the 672 x 560 copy: <sample_id>.png
        q = D / "images_full_mr" / name
        if not q.exists():
            im = Image.open(D / r["image"]).convert("RGB")
            assert im.size == (1224, 1024), (r["image"], im.size)
            im.resize((980, 840), Image.BICUBIC).save(q)
            n += 1
        f.write(json.dumps({**r, "image": "images_full_mr/" + name}) + "\n")
print("questions:", len(rows), "new reduced images:", n, "size 980x840 =", 980 * 840, "pixels")
PY
log "resize done: $(tail -1 $O/log_resize_mr_full.txt)"
test "$(wc -l < data/full_onboard_mr.jsonl)" = 1328 || { log "question file missing"; exit 1; }
( while true; do echo "$(date +%s) $(grep -E '^(pswpin|pswpout) ' /proc/vmstat | tr '\n' ' ') $(grep -E '^(SwapFree|MemAvailable):' /proc/meminfo | tr -s ' ' | tr '\n' ' ')"; sleep 10; done ) > $O/swap_$N.txt 2>&1 &
SWP=$!
python3 b10_board_bench_guard.py --name $N --probe data/full_onboard_mr.jsonl --warm-probe data/full_onboard_mr.jsonl --out-root $O > $O/log_$N.txt 2>&1
log "bench $N done (rc $?)"
kill $SWP
echo done > $O/MR_FULL_DONE; log "run at 980x840 done"
