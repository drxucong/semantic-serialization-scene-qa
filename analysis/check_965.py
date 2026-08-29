# -*- coding: utf-8 -*-
"""When the compiled arg-min is wrong, how often is the class it names NOT
among the three offered (non-abstain) options?  (paper: 0.965)"""
import json, math
from pathlib import Path
UP = Path(".")  # repo root: banks/, states/, results/
STATES = json.load(open(UP / "states" / "states_kf_v9.json", encoding="utf-8"))
QA = [json.loads(l) for l in open(UP / "banks" / "qa_coda.jsonl", encoding="utf-8")]

def lateral(g): return abs(g["dist"] * math.sin(math.radians(g["bearing"])))
def path_rank(g): return lateral(g) + g["dist"] / 10.0
def s1(st):
    ags = st["agents"]; return min(ags, key=path_rank)["cls"] if ags else None
def s2(st):
    near = {}
    for g in st["agents"]: near.setdefault(g["cls"], g)
    return min(near.items(), key=lambda kv: kv[1]["dist"])[0] if near else None
def norm(s): return (s or "").strip().lower()

for fam, fn in (("path_object", s1), ("nearest_class", s2)):
    wrong = outside = tot = 0
    for it in QA:
        if it["category"] != fam: continue
        st = STATES.get(it["sample_id"])
        if not st: continue
        pred = fn(st)
        if pred is None: continue
        tot += 1
        gold = norm(it["choices"][it["answer"]])
        if norm(pred) == gold: continue
        wrong += 1
        opts = {norm(v) for k, v in it["choices"].items() if k != it.get("abstain_letter")}
        if norm(pred) not in opts: outside += 1
    print(f"{fam}: n={tot} wrong={wrong} named-class-outside-options={outside} -> {outside/wrong:.3f}")
