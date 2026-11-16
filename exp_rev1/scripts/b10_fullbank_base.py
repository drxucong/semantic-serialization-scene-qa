"""B10 (Orin), full confirmatory bank, laptop side (added 2026-11-15): write the file that the
board needs for every one of the 1328 confirmatory questions: option letters, the correct
letter, the VLM prompt of the shipped arm, the image path on the board, and the answers that
the same models gave on the laptop (for the 'same answers' count).

Writes outputs/b10_fullbank/full_base.jsonl and sids_confirm.txt.
"""
import glob, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
for p in ("", "scripts/pilot"):
    sys.path.insert(0, str(ROOT / p) if p else str(ROOT))
from run_pilot_phase0 import forced_choices  # noqa: E402
import run_pilot_pixel_ollama as PX  # noqa: E402

REL = Path(r"C:/Users/drxuc/Downloads/files/serialized-scene-qa-release")


def preds(pattern):
    ps = glob.glob(str(pattern))
    assert ps, pattern
    return {json.loads(l)["qa_id"]: json.loads(l).get("pred") for l in open(ps[0], encoding="utf-8")}


LAP = {"light1-3b": preds(ROOT / "exp_rev1/b5_light/infer/cf_d0_light1_3b/*forced.jsonl"),
       "light1-7b": preds(ROOT / "exp_rev1/b5_light/infer/cf_d0_light1_7b/*forced.jsonl"),
       "qwen2.5vl-3b": preds(REL / "results/phase10/results_cf_px3b_robust/*forced.jsonl")}
out = ROOT / "outputs/b10_fullbank"; out.mkdir(parents=True, exist_ok=True)
qa = [json.loads(l) for l in open(ROOT / "outputs/coda/qa_confirm.jsonl", encoding="utf-8")]
n = 0
with open(out / "full_base.jsonl", "w", encoding="utf-8") as f, open(out / "sids_confirm.txt", "w") as g:
    for it in qa:
        fch, fans = forced_choices(it)
        if fans is None:
            continue
        assert it["cam_front"].startswith("data/coda_sm/"), it["cam_front"]
        f.write(json.dumps({"qa_id": it["qa_id"], "sample_id": it["sample_id"], "family": it["category"], "gold": fans,
                            "choices": list(fch), "image": "../e2e/" + it["cam_front"], "px_system": PX.SYSTEM,
                            "px_user": PX.build_prompt(it, fch),
                            "laptop_pred": {k: v.get(it["qa_id"]) for k, v in LAP.items()}}) + "\n")
        g.write(it["sample_id"] + "\n"); n += 1
print("wrote", n, "questions ->", out)
