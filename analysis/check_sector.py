# -*- coding: utf-8 -*-
"""Sector-rule agreement (paper: object-level 0.986; question-level 0.553 serializer rule
/ 0.761 generator rule).  Generator: image column thirds of 1224 px.  Serializer: bearing
+-15 deg (theta>0 = left)."""
import json
from pathlib import Path
UP = Path(".")  # repo root: banks/, states/, results/
GT = json.load(open(UP/"states"/"states_coda.json", encoding="utf-8"))
PV = json.load(open(UP/"states"/"states_kf_v9.json", encoding="utf-8"))
QA = [json.loads(l) for l in open(UP/"banks"/"qa_coda.jsonl", encoding="utf-8")]
b1, b2 = 1224/3, 2*1224/3
def sec_col(u): return "on the left side" if u < b1 else ("in the center" if u < b2 else "on the right side")
def sec_bear(th): return "on the left side" if th > 15 else ("on the right side" if th < -15 else "in the center")

# object-level: over GT objects, bearing rule vs column rule
n=a=0
for sid, st in GT.items():
    for g in st["agents"]:
        if "u" not in g or "bearing" not in g: continue
        n+=1; a+= sec_col(g["u"]) == sec_bear(g["bearing"])
print(f"object-level agreement (GT objects, bearing rule vs column rule): {a}/{n} = {a/n:.3f}")

# question-level: direction questions; gold vs perceived nearest instance of queried class
import re
tot=agree_b=agree_c=0
for it in QA:
    if it["category"]!="direction": continue
    m = re.search(r"'([^']+)'", it["question"]); cls = m.group(1) if m else None
    st = PV.get(it["sample_id"])
    if not st or not cls: continue
    cands = [g for g in st["agents"] if g["cls"]==cls]
    if not cands: tot+=1; continue
    g = min(cands, key=lambda g: g["dist"])
    gold = it["choices"][it["answer"]]
    tot+=1
    agree_b += sec_bear(g["bearing"]) == gold
    agree_c += sec_col(g["u"]) == gold
print(f"question-level (direction, n={tot}): serializer bearing rule {agree_b/tot:.3f} | generator column rule {agree_c/tot:.3f}")
