"""Run-to-run sensitivity, measured instead of assumed.

What the paper said before this ran: one repeat pair per scale gave a
predicted-letter flip rate f, and under a sign-symmetry assumption sd =
sqrt(f/N), so +-.006 (7B) / +-.008 (3B). Two weaknesses a reviewer named: one
pair, and an assumption.

What this does: with R independent runs of the same arm on byte-identical
prompts there are R(R-1)/2 pairs, and the accuracy difference of a pair is
observed directly -- no symmetry assumption, no sqrt(f/N). We report the
empirical sd of that difference and its range, and we keep the flip rate as a
descriptive statistic beside it.

Two things this is NOT. It is not a test: runs of one arm are not a sample from
a population of systems. And it does not replace the bootstrap, which prices
resampling of items; this prices resampling of runs. They answer different
questions and the paper reports both.
"""
import json, itertools, statistics as st
from pathlib import Path

CODA = Path("/mnt/user-data/uploads/lvcworld/outputs/phase10/coda")
T = "state_typed__clean__forced.jsonl"

GROUPS = {
    "SCOPED 7B": ["results_cf_v15_7b"] + [f"results_rep_v15_7b_{r}"
                                          for r in ("r2", "r3", "r4", "r5")],
    "SCOPED 3B": ["results_cf_v15_3b"] + [f"results_rep_v15_3b_{r}"
                                          for r in ("r2", "r3", "r4", "r5")],
    "FLAT 7B":   ["results_cf_v9_7b"] + [f"results_rep_v9_7b_{r}"
                                         for r in ("r2", "r3")],
}


def load(d):
    p = CODA / d / T
    if not p.exists():
        return None
    seen = {}
    for line in open(p, encoding="utf-8"):
        try:
            r = json.loads(line)
        except json.JSONDecodeError:
            continue
        seen[r["qa_id"]] = r
    return seen if len(seen) >= 1328 else None


out = {}
for name, dirs in GROUPS.items():
    runs = [(d, load(d)) for d in dirs]
    have = [(d, r) for d, r in runs if r is not None]
    missing = [d for d, r in runs if r is None]
    if len(have) < 2:
        print(f"{name:<12} only {len(have)} complete run(s); pending {missing}")
        continue
    qs = sorted(set.intersection(*[set(r) for _, r in have]))
    accs = [sum(bool(r[q]["correct"]) for q in qs) / len(qs) for _, r in have]
    diffs, flips = [], []
    for (da, ra), (db, rb) in itertools.combinations(have, 2):
        a = sum(bool(ra[q]["correct"]) for q in qs) / len(qs)
        b = sum(bool(rb[q]["correct"]) for q in qs) / len(qs)
        diffs.append(a - b)
        flips.append(sum(ra[q].get("pred") != rb[q].get("pred")
                         for q in qs) / len(qs))
    ad = [abs(d) for d in diffs]
    sd = st.pstdev(diffs) if len(diffs) > 1 else float("nan")
    print(f"\n{name}   R={len(have)} runs, N={len(qs)}"
          + (f"   [pending {len(missing)}]" if missing else ""))
    print("  accuracies      " + "  ".join(f"{a:.4f}" for a in sorted(accs)))
    print(f"  spread          max-min = {max(accs)-min(accs):+.4f}")
    print(f"  pairwise |diff| n={len(diffs)}  median {st.median(ad):.4f}  "
          f"max {max(ad):.4f}")
    print(f"  sd of the paired run-to-run difference   {sd:.4f}"
          f"   -> 1.96 sd = {1.96*sd:.4f}")
    print(f"  predicted-letter flip rate  median {st.median(flips):.4f}  "
          f"range {min(flips):.4f}-{max(flips):.4f}")
    old = {"SCOPED 7B": 0.0063, "FLAT 7B": 0.0063, "SCOPED 3B": 0.0080}[name]
    print(f"  the paper's single-pair sqrt(f/N) scale was {old:+.4f}"
          f"   -> measured/assumed = {1.96*sd/old:.2f}x")
    out[name] = {"R": len(have), "N": len(qs),
                 "accs": [round(a, 4) for a in accs],
                 "spread": round(max(accs) - min(accs), 4),
                 "sd_diff": round(sd, 5), "scale_1p96sd": round(1.96 * sd, 4),
                 "max_abs_diff": round(max(ad), 4),
                 "flip_median": round(st.median(flips), 4),
                 "flip_range": [round(min(flips), 4), round(max(flips), 4)],
                 "old_scale": old, "pending": missing}

json.dump(out, open("/home/claude/work/analysis/repeat_results.json", "w"),
          indent=1)
print("\nwrote repeat_results.json")
