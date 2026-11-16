#!/usr/bin/env python3
"""B10 (Orin), full confirmatory bank on the board (added 2026-11-15).

The session of run_b10_orin_e2e.sh measured time and energy on 50 questions and did not measure
accuracy on the board. This driver runs the same one-pass detector pair ('light1': two
fine-tuned YOLO11 detectors, one full-frame pass each, ground-plane and class-height ranging,
one camera) on all 1328 confirmatory frames on the board, each frame with the detectors of the
fold that never saw its recording, and builds the reader prompts from the board's own states
with the shipped serializer.

  perceive  all frames of outputs/coda/sids_confirm.txt -> states_confirm_light1_orin.json
  prompts   data/full_onboard.jsonl (text and VLM prompts for all questions),
            data/full_onboard_lr.jsonl (the same with images reduced to 672 x 560),
            data/probe50_hybrid.jsonl and probe50_hybrid_lr.jsonl (the 50 probe questions with the
            serialized text of the board's state added to the VLM prompt, as in the arm
            'VLM + text' of the paper)
usage: python3 b10_orin_fullbank.py perceive|prompts
"""
import json, os, sys, time
from pathlib import Path

HOME = Path.home()
sys.path.insert(0, str(HOME / "rev1"))
import b10_orin_perceive as BP   # Sampler, perceive, paths (same harness as the 50-question session)

E, OUT = BP.E, BP.OUT
HYBRID = "A perception system produced the following description of the same image; it may contain errors.\n"


def stage_perceive():
    S = BP.Sampler(); time.sleep(5); idle_end = time.time()
    idle = S.window(idle_end - 5, idle_end)
    r = BP.perceive("states_confirm_light1_orin", "outputs/coda/sids_confirm.txt", 0)
    d = json.load(open(r["states"]))
    res = {"n_frames": len(d), "wall_s": r["wall_s"], "n_folds": r["n_folds"], "idle": idle, "whole": S.window(r["t0"], r["t1"]),
           "tail": r["tail"]}
    if r["loop_start"] and r["loop_end"]:
        res["loop_s"] = r["loop_end"] - r["loop_start"]; res["loop"] = S.window(r["loop_start"], r["loop_end"])
    S.close()
    json.dump(res, open(OUT / "fullbank_perception.json", "w"), indent=1)
    print("full bank perceived:", len(d), "frames; wall", round(r["wall_s"], 1), "s;", res.get("loop"), flush=True)


def stage_prompts():
    for p in ("scripts/paper", "scripts/pilot", "scripts/coda", "."):
        sys.path.insert(0, str(E / p))
    os.chdir(E)
    import run_serializer_dladder as DL
    from PIL import Image
    states = json.load(open(E / "outputs/coda/states_confirm_light1_orin.json"))
    bank = {it["qa_id"]: it for it in DL.load_bank("outputs/coda/qa_confirm.jsonl", "repo")}
    base = [json.loads(l) for l in open(HOME / "rev1/data/full_base.jsonl", encoding="utf-8")]
    D = HOME / "rev1/data"; (D / "images_full_lr").mkdir(exist_ok=True)
    n = miss = 0
    with open(D / "full_onboard.jsonl", "w", encoding="utf-8") as fo, open(D / "full_onboard_lr.jsonl", "w", encoding="utf-8") as fl:
        for b in base:
            it = bank[b["qa_id"]]
            if it["sample_id"] not in states:
                miss += 1; continue
            scene = DL.serialize_dl(states[it["sample_id"]], it["category"], "d0")
            rec = {**{k: b[k] for k in ("qa_id", "family", "gold", "choices", "image", "px_system", "px_user", "laptop_pred")},
                   "text_system": DL.SYSTEM, "text_user": DL.V9.build_prompt(scene, it, it["choices"])}
            fo.write(json.dumps(rec) + "\n")
            lr = D / "images_full_lr" / (it["sample_id"] + ".png")
            if not lr.exists():
                im = Image.open(D / b["image"]).convert("RGB")
                assert im.size == (1224, 1024), im.size
                im.resize((672, 560), Image.BICUBIC).save(lr)
            fl.write(json.dumps({**rec, "image": "images_full_lr/" + it["sample_id"] + ".png"}) + "\n"); n += 1
    # the 50 probe questions with the serialized text of the board's state in the VLM prompt
    st50 = json.load(open(E / "outputs/coda/states_probe_light1_orin.json"))
    for src, dst in (("probe50.jsonl", "probe50_hybrid.jsonl"), ("probe50_lr.jsonl", "probe50_hybrid_lr.jsonl")):
        rows = [json.loads(l) for l in open(D / src, encoding="utf-8")]
        with open(D / dst, "w", encoding="utf-8") as f:
            for r in rows:
                it = bank[r["qa_id"]]
                scene = DL.serialize_dl(st50[it["sample_id"]], it["category"], "d0")
                f.write(json.dumps({**r, "px_user": HYBRID + scene + "\n\n" + r["px_user"]}) + "\n")
    print(f"prompts written for {n} questions ({miss} without a state); hybrid probe files written", flush=True)


if __name__ == "__main__":
    {"perceive": stage_perceive, "prompts": stage_prompts}[sys.argv[1]]()
