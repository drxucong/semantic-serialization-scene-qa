# -*- coding: utf-8 -*-
"""Re-derive the 2026-08-05 attribution counts from archived data.

Paper sentences (VIII):
  "bearing calibration ... produced 1 sector flip in 309; the losses were 43
   undetected classes and 39 ordering errors"        <- direction family, v8 system
  "most nearest-distance errors were reader errors on correctly perceived
   states (54 of 98): handed 4.7 m, picked the wrong band"

Inputs (all archived): dev bank qa_coda.jsonl, GT states_coda.json, v8 perceived
states_kf_v8.json, v8 7B per-item results results_system8_kf_7b."""
import json, math, re, glob
from pathlib import Path
UP = Path(".")  # repo root: banks/, states/, results/
GT = json.load(open(UP/"states"/"states_coda.json", encoding="utf-8"))
PV = json.load(open(UP/"states"/"states_kf_v8.json", encoding="utf-8"))
QA = [json.loads(l) for l in open(UP/"banks"/"qa_coda.jsonl", encoding="utf-8")]
RES = {r["qa_id"]: r for f in glob.glob(str(UP/"results"/"phase10"/"results_system8_kf_7b"/"*.jsonl"))
       for r in map(json.loads, open(f, encoding="utf-8"))}

def cls_of(it):
    m = re.search(r"'([^']+)'", it["question"]); return m.group(1) if m else None
def sec_bear(t):
    return "on the left side" if t > 15 else ("on the right side" if t < -15 else "in the center")
def band(d):
    return "under 5 meters away" if d < 5 else ("5 to 15 meters away" if d <= 15 else "over 15 meters away")
def norm(s): return (s or "").strip().lower().replace("metres","meters")

# ---------------- direction ----------------
UTOL = 25.0  # sweep below
und = orde = flip = hwrong = 0
n = 0
for it in QA:
    if it["category"] != "direction": continue
    n += 1
    cls = cls_of(it); gold = it["choices"][it["answer"]]
    gt_c = [g for g in GT[it["sample_id"]]["agents"] if g["cls"] == cls]
    pv_c = [g for g in PV.get(it["sample_id"], {"agents": []})["agents"] if g["cls"] == cls]
    if not gt_c: continue
    gt_near = min(gt_c, key=lambda g: g["dist"])
    if not pv_c:
        und += 1; hwrong += 1; continue
    sel = min(pv_c, key=lambda g: g["dist"])
    h = sec_bear(sel["bearing"])
    if h == gold: continue
    hwrong += 1
    same = abs(sel.get("u", 1e9) - gt_near.get("u", -1e9)) <= UTOL
    if same: flip += 1
    else: orde += 1
print(f"direction (UTOL=25): n={n}  h-wrong={hwrong}  undetected={und}  ordering={orde}  sector-flip={flip}")
# UTOL sweep for the association tolerance
for utol in (40.0, 50.0, 80.0, 120.0):
    u2=o2=f2=0
    for it in QA:
        if it["category"] != "direction": continue
        cls = cls_of(it); gold = it["choices"][it["answer"]]
        gt_c=[g for g in GT[it["sample_id"]]["agents"] if g["cls"]==cls]
        pv_c=[g for g in PV.get(it["sample_id"],{"agents":[]})["agents"] if g["cls"]==cls]
        if not gt_c: continue
        gt_near=min(gt_c,key=lambda g:g["dist"])
        if not pv_c: u2+=1; continue
        sel=min(pv_c,key=lambda g:g["dist"])
        if sec_bear(sel["bearing"])==gold: continue
        if abs(sel.get("u",1e9)-gt_near.get("u",-1e9))<=utol: f2+=1
        else: o2+=1
    print(f"direction (UTOL={utol:.0f}): undetected={u2} ordering={o2} flip={f2}")

# ---------------- nearest-distance ----------------
tot_err = rderr = 0
examples = []
for it in QA:
    if it["category"] != "nearest_dist": continue
    r = RES.get(it["qa_id"])
    if r is None or r["correct"]: continue
    tot_err += 1
    cls = cls_of(it); gold = norm(it["choices"][it["answer"]])
    pv_c = [g for g in PV.get(it["sample_id"], {"agents": []})["agents"] if g["cls"] == cls]
    if not pv_c: continue
    d = min(g["dist"] for g in pv_c)
    if norm(band(d)) == gold:
        rderr += 1
        examples.append(round(d, 2))
print(f"nearest_dist: reader-errors-on-correct-state={rderr} of total-errors={tot_err}")
examples.sort()
print("handed distances (reader still picked the wrong band):", examples)
