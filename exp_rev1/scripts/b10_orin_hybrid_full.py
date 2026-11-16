#!/usr/bin/env python3
"""B10 (Orin), added 2026-11-15 after the reader runs of the full-bank session had finished
(amendments/A7_addendum1.md; exploratory): prompts for the VLM with the reduced image and the
serialized text of the board's own states, for all 1328 confirmatory questions.

Reads data/full_onboard_lr.jsonl (written by b10_orin_fullbank.py prompts) and the states that
the board computed; writes data/full_onboard_hybrid_lr.jsonl. The VLM prompt is the prompt of the
arm 'VLM + text' of the paper: the sentence HYBRID, the serialized text, an empty line, and the
VLM prompt of the question.
usage: python3 b10_orin_hybrid_full.py
"""
import json, os, sys
from pathlib import Path

HOME = Path.home()
sys.path.insert(0, str(HOME / "rev1"))
import b10_orin_perceive as BP

E = BP.E
HYBRID = "A perception system produced the following description of the same image; it may contain errors.\n"
for p in ("scripts/paper", "scripts/pilot", "scripts/coda", "."):
    sys.path.insert(0, str(E / p))
os.chdir(E)
import run_serializer_dladder as DL

states = json.load(open(E / "outputs/coda/states_confirm_light1_orin.json"))
bank = {it["qa_id"]: it for it in DL.load_bank("outputs/coda/qa_confirm.jsonl", "repo")}
D = HOME / "rev1/data"
n = 0
with open(D / "full_onboard_hybrid_lr.jsonl", "w", encoding="utf-8") as f:
    for l in open(D / "full_onboard_lr.jsonl", encoding="utf-8"):
        r = json.loads(l)
        it = bank[r["qa_id"]]
        scene = DL.serialize_dl(states[it["sample_id"]], it["category"], "d0")
        f.write(json.dumps({**r, "px_user": HYBRID + scene + "\n\n" + r["px_user"]}) + "\n")
        n += 1
print("hybrid prompts written:", n, flush=True)
