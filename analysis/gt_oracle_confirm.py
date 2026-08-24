"""Same-bank GT-state oracle (job18) -- the headroom question, answered properly.

Until now the paper could only say: the GT oracle reached .955 ON THE DEVELOPMENT
BANK, and we refuse to subtract that from a confirmatory score because the two
banks are different. That refusal was right and it was also unsatisfying.

job18 ran the oracle on the CONFIRMATORY bank -- same 1328 questions, same
serializer, same reader, ground-truth boxes instead of perceived ones. So the
subtraction is now legal:

    oracle - system  =  what perfect perception would buy, on this bank
    1 - oracle       =  what is left for the serializer and the reader

Same pairing and bootstrap as confirm_analysis.py: paired by qa_id, resampled
over the 21 recording sequences, B=20000, seed 0.
"""
import json, random, sys, collections
from pathlib import Path

ROOT = Path("/mnt/user-data/uploads/lvcworld/outputs")
CODA = ROOT / "phase10" / "coda"
B, SEED, FULL_N = 20000, 0, 1328
T = "state_typed__clean__forced.jsonl"

ARMS = {
    "SCOPED 7B (real perception)": "results_cf_v15_7b",
    "SCOPED 3B (real perception)": "results_cf_v15_3b",
    "GT oracle 7B":                "results_cf_gt_7b",
    "GT oracle 3B":                "results_cf_gt_3b",
    "record v16 7B":               "results_rec_7b",
    "record v16 3B":               "results_rec_3b",
    "record v16 1.5B":             "results_rec_1_5b",
    "record v16 0.5B":             "results_rec_0_5b",
    "Qwen2.5-VL 7B on text":       "results_if2_txt_7b",
    "Qwen2.5-VL 3B on text":       "results_if2_txt_3b",
}


def load(d):
    p = CODA / d / T
    if not p.exists():
        return None
    seen, order = {}, []
    for line in open(p, encoding="utf-8"):
        try:
            r = json.loads(line)
        except json.JSONDecodeError:
            continue
        seen[r["qa_id"]] = r
        order.append(r)
    return {"by_id": seen, "order": order}


def scene_of(r):
    return r.get("scene_name") or r["qa_id"].split("_")[1]


def boot(pairs):
    scenes = sorted({s for s, _ in pairs})
    by = collections.defaultdict(list)
    for s, v in pairs:
        by[s].append(v)
    rng = random.Random(SEED)
    st = []
    for _ in range(B):
        acc = []
        for _ in scenes:
            acc.extend(by[rng.choice(scenes)])
        st.append(sum(acc) / len(acc))
    st.sort()
    d = sum(sum(v) for v in by.values()) / sum(len(v) for v in by.values())
    return d, st[int(.025 * B)], st[int(.975 * B)]


def contrast(da, db, label, per_family=False):
    A, Bb = load(da), load(db)
    if A is None or Bb is None:
        print(f"{label:<46} [pending]")
        return None
    qs = sorted(set(A["by_id"]) & set(Bb["by_id"]))
    pairs = [(scene_of(A["by_id"][q]),
              int(bool(A["by_id"][q]["correct"]))
              - int(bool(Bb["by_id"][q]["correct"]))) for q in qs]
    d, lo, hi = boot(pairs)
    aa = sum(bool(A["by_id"][q]["correct"]) for q in qs) / len(qs)
    bb = sum(bool(Bb["by_id"][q]["correct"]) for q in qs) / len(qs)
    sig = lo > 0 or hi < 0
    print(f"{label:<46} {aa:.4f} vs {bb:.4f}  {d:+.4f} "
          f"[{lo:+.4f},{hi:+.4f}]{'*' if sig else ' '} n={len(qs)}")
    out = {"label": label, "accA": round(aa, 4), "accB": round(bb, 4),
           "delta": round(d, 4), "ci": [round(lo, 4), round(hi, 4)],
           "n": len(qs), "sig": bool(sig)}
    if per_family:
        for f_ in sorted({A["by_id"][q].get("category") for q in qs}):
            fq = [q for q in qs if A["by_id"][q].get("category") == f_]
            fd, flo, fhi = boot([(scene_of(A["by_id"][q]),
                                  int(bool(A["by_id"][q]["correct"]))
                                  - int(bool(Bb["by_id"][q]["correct"])))
                                 for q in fq])
            print(f"      {f_:<18} {fd:+.4f} [{flo:+.4f},{fhi:+.4f}] n={len(fq)}")
    return out


print("=" * 100)
print("ARM HEALTH -- confirmatory bank")
print("=" * 100)
health = {}
for name, d in ARMS.items():
    A = load(d)
    if A is None:
        print(f"{name:<30}{d:<26}[pending]")
        continue
    rows = A["order"]
    parsed = sum(r.get("pred") is not None for r in rows)
    run = best = 0
    for r in rows:
        run = run + 1 if r.get("pred") is None else 0
        best = max(best, run)
    acc = sum(bool(r["correct"]) for r in A["by_id"].values()) / len(A["by_id"])
    accp = (sum(bool(r["correct"]) for r in A["by_id"].values()
                if r.get("pred") is not None)
            / max(1, sum(r.get("pred") is not None
                         for r in A["by_id"].values())))
    arm = rows[0].get("arm", "?")
    print(f"{name:<30}n={len(A['by_id']):5d}  acc={acc:.4f}  "
          f"acc|parsed={accp:.4f}  parse={parsed/len(rows):.4f}  "
          f"longest_unparsed_run={best}  arm={arm}")
    health[name] = {"n": len(A["by_id"]), "acc": round(acc, 4),
                    "acc_parsed": round(accp, 4),
                    "parse": round(parsed / len(rows), 4),
                    "longest_unparsed_run": best, "arm_tag": arm}

print()
print("=" * 100)
print("SAME-BANK HEADROOM  (this is what replaces the cross-bank refusal)")
print("=" * 100)
res = {}
res["gt_7b"] = contrast("results_cf_gt_7b", "results_cf_v15_7b",
                        "GT oracle - SCOPED, 7B  [same bank]", per_family=True)
res["gt_3b"] = contrast("results_cf_gt_3b", "results_cf_v15_3b",
                        "GT oracle - SCOPED, 3B  [same bank]")
res["gt_scale"] = contrast("results_cf_gt_7b", "results_cf_gt_3b",
                           "GT oracle 7B - GT oracle 3B")

print()
print("=" * 100)
print("v16 RECORD -- zero-shot scaling curve on the confirmatory bank")
print("=" * 100)
for a, b, lab in [("results_rec_7b", "results_cf_v15_7b", "record - SCOPED, 7B"),
                  ("results_rec_3b", "results_cf_v15_3b", "record - SCOPED, 3B")]:
    res[lab] = contrast(a, b, lab)
res["rec_slope"] = contrast("results_rec_7b", "results_rec_0_5b",
                            "record 7B - record 0.5B  (slope)")
res["scoped_slope_ref"] = contrast("results_cf_v15_7b", "results_cf_v15_3b",
                                   "SCOPED 7B - SCOPED 3B  (slope ref)")

print()
print("=" * 100)
print("INTERFACE LADDER -- same VL weights, text vs their own image")
print("=" * 100)
res["if2_7b"] = contrast("results_if2_txt_7b", "results_cf_px_7b",
                         "Qwen2.5-VL 7B: text - own image")
res["if2_3b"] = contrast("results_if2_txt_3b", "results_cf_px3b_robust",
                         "Qwen2.5-VL 3B: text - own image")

json.dump({"health": health, "contrasts": res},
          open("/home/claude/work/analysis/gt_oracle_confirm.json", "w"),
          indent=1)
print("\nwrote gt_oracle_confirm.json")
