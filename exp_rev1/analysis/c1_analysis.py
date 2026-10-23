"""C1 external evaluation (nuScenes mini, front camera): accuracy and paired
cluster bootstrap (10 scene clusters, B=20000, seed 20260809) for
  pixel_{3b,7b}        zero-shot Qwen2.5-VL on the keyframe
  d0_rfdetr_{3b,7b}    shipped serializer over zero-shot COCO RF-DETR + mono ranging
  d0_gt_{3b,7b}        shipped serializer over ground-truth state (oracle)
  blind_{3b,7b}        question + options only (answer-only prior)
Contrasts: d0_rfdetr - pixel (primary, descriptive), d0_gt - d0_rfdetr (perception
gap), blind as prior. Per-family deltas. Writes c1_results.{md,json}.
"""
import glob, json
from pathlib import Path
import numpy as np, pandas as pd

LV = Path(__file__).resolve().parents[2]  # repository root
HERE = Path(__file__).resolve().parent
B, SEED = 20000, 20260809
bank = {json.loads(l)["qa_id"]: json.loads(l) for l in open(LV / "exp_rev1/c1_nusc/qa_nusc.jsonl", encoding="utf-8")}


def load(name):
    ps = glob.glob(str(LV / f"exp_rev1/c1_nusc/{name}/*__clean__forced.jsonl"))
    if not ps:
        return None
    df = pd.DataFrame([json.loads(l) for l in open(ps[0], encoding="utf-8")]).set_index("qa_id")
    df["scene"] = [bank[q]["scene_name"] for q in df.index]
    df["family"] = [bank[q]["category"] for q in df.index]
    return df


def boot(diff, seq):
    rng = np.random.default_rng(SEED)
    g = pd.DataFrame({"d": diff, "s": seq}).groupby("s")["d"].agg(["sum", "size"])
    idx = rng.integers(0, len(g), size=(B, len(g)))
    est = g["sum"].values[idx].sum(1) / g["size"].values[idx].sum(1)
    lo, hi = np.percentile(est, [2.5, 97.5])
    return float(np.mean(diff)), float(lo), float(hi)


def contrast(a, b):
    common = a.index.intersection(b.index)
    d, lo, hi = boot((a.loc[common, "correct"].astype(float) - b.loc[common, "correct"].astype(float)).values, a.loc[common, "scene"].values)
    return {"delta": d, "lo": lo, "hi": hi, "n": int(len(common)), "txt": f"{d:+.4f} [{lo:+.4f}, {hi:+.4f}]" + ("*" if lo > 0 or hi < 0 else "")}


arms = {n: load(n) for n in ["pixel_3b", "pixel_7b", "d0_rfdetr_3b", "d0_rfdetr_7b", "d0_gt_3b", "d0_gt_7b", "blind_3b", "blind_7b"]}
out, L = {}, ["# C1 external evaluation: nuScenes mini, CAM_FRONT, 347 items, 10 scenes\n", "| arm | n | acc | parse |", "|---|---|---|---|"]
for n, df in arms.items():
    if df is None:
        L.append(f"| {n} | - | pending | |"); continue
    out[n] = {"n": int(len(df)), "acc": float(df["correct"].mean()), "parse": float(df["pred"].notna().mean()),
              "per_family_acc": {f: float(g["correct"].mean()) for f, g in df.groupby("family")}}
    L.append(f"| {n} | {len(df)} | {out[n]['acc']:.4f} | {out[n]['parse']:.4f} |")
L.append("\n| contrast | 3B | 7B |"); L.append("|---|---|---|")
for lab, a, b in [("serialized (zero-shot RF-DETR) − pixel", "d0_rfdetr", "pixel"), ("GT oracle − serialized", "d0_gt", "d0_rfdetr"),
                  ("serialized − blind", "d0_rfdetr", "blind"), ("pixel − blind", "pixel", "blind")]:
    row = []
    for s in ("3b", "7b"):
        if arms.get(f"{a}_{s}") is not None and arms.get(f"{b}_{s}") is not None:
            c = contrast(arms[f"{a}_{s}"], arms[f"{b}_{s}"]); out[f"{lab}|{s}"] = c; row.append(c["txt"])
        else:
            row.append("pending")
    L.append(f"| {lab} | {row[0]} | {row[1]} |")
L.append("\nPer-family accuracy (3B / 7B):")
for f in ["counting", "direction", "nearest_class", "nearest_dist", "path_object"]:
    cells = []
    for a in ["pixel", "d0_rfdetr", "d0_gt", "blind"]:
        v = [out.get(f"{a}_{s}", {}).get("per_family_acc", {}).get(f) for s in ("3b", "7b")]
        cells.append(f"{a}: " + " / ".join("-" if x is None else f"{x:.3f}" for x in v))
    L.append(f"- {f}: " + "; ".join(cells))
(HERE / "c1_results.md").write_text("\n".join(L), encoding="utf-8")
json.dump(out, open(HERE / "c1_results.json", "w"), indent=1)
print("\n".join(L))
