"""The confirmatory re-run on frames nothing was selected on.

Criteria, quoted from go_confirm.bat and frozen before the bank existed:

  A1  PRIMARY   v15 - pixel VLM at 7B: CI lower bound > 0 AND delta > +.006
  A2  PRIMARY   v15 - pixel VLM at 3B: CI lower bound > 0 AND delta > +.008
  A3  DECISION  v15 - v9 at both scales, floor applied. The paper leads with
                v15 only if v15 is not WORSE than v9 above the floor at either
                scale. If it loses above the floor, the paper keeps v9.

Bank: 1328 questions over 1329 CODa_sm frames, every one of them at least 15
frames (1.5 s) from every frame of the 1366-question development bank -- the
development bank's own median spacing. Same generator, same visible-scope gate,
same five families, same four-option format with a never-correct abstain, new
seed. Perception is the shipped configuration (yolo-conf .25) with the same
sequence-held-out fold detectors, so a confirmatory frame is perceived by a
model that never trained on its sequence.

Paired by qa_id, bootstrapped over recording sequences (B=20000, seed 0).

Usage: python confirm_analysis.py [uploads_root]
"""
import json, random, sys, collections
from pathlib import Path

ROOT = Path(sys.argv[1] if len(sys.argv) > 1
            else "/mnt/user-data/uploads/lvcworld/outputs")
CODA = ROOT / "phase10" / "coda"
B, SEED = 20000, 0
FULL_N = 1328
FLOOR = {"7B": 0.006, "3B": 0.008}

T = "state_typed__clean__forced.jsonl"
X = "pixel__clean__forced.jsonl"
ARMS = {
    "v15_7b": ("results_cf_v15_7b", T, "7B"),
    "v15_3b": ("results_cf_v15_3b", T, "3B"),
    "v9_7b":  ("results_cf_v9_7b",  T, "7B"),
    "v9_3b":  ("results_cf_v9_3b",  T, "3B"),
    "px_7b":  ("results_cf_px_7b",  X, "7B"),
    "px_3b":  ("results_cf_px_3b",  X, "3B"),
}


def load(name):
    d, f, _ = ARMS[name]
    p = CODA / d / f
    if not p.exists():
        return None
    rows, seen = [], {}
    for line in open(p, encoding="utf-8"):
        try:
            r = json.loads(line)
        except json.JSONDecodeError:
            continue
        seen[r["qa_id"]] = r
        rows.append(r)
    return {"by_id": seen, "order": rows}


def scene_of(rec):
    return rec.get("scene_name") or rec["qa_id"].split("_")[1]


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


def contrast(a, b, label, per_family=False):
    A, Bb = load(a), load(b)
    if A is None or Bb is None:
        miss = a if A is None else b
        print(f"{label:<50} [pending: {ARMS[miss][0]}]")
        return None
    for nm, Xx in ((a, A), (b, Bb)):
        if len(Xx["by_id"]) < FULL_N:
            print(f"{label:<50} [partial: {nm} {len(Xx['by_id'])}/{FULL_N}]")
            return None
    qs = sorted(set(A["by_id"]) & set(Bb["by_id"]))
    pairs = [(scene_of(A["by_id"][q]),
              int(bool(A["by_id"][q]["correct"]))
              - int(bool(Bb["by_id"][q]["correct"]))) for q in qs]
    d, lo, hi = boot(pairs)
    fl = FLOOR[ARMS[a][2]]
    sig = lo > 0 or hi < 0
    above = abs(d) > fl
    note = "" if above else f"   <- below the {fl:+.3f} floor"
    aa = sum(bool(A["by_id"][q]["correct"]) for q in qs) / len(qs)
    bb = sum(bool(Bb["by_id"][q]["correct"]) for q in qs) / len(qs)
    print(f"{label:<50} {aa:.4f} vs {bb:.4f}  {d:+.4f} "
          f"[{lo:+.4f},{hi:+.4f}]{'*' if sig else ' '} n={len(qs)}{note}")
    out = {"label": label, "accA": round(aa, 4), "accB": round(bb, 4),
           "delta": round(d, 4), "ci": [round(lo, 4), round(hi, 4)],
           "n": len(qs), "sig": bool(sig), "above_floor": bool(above)}
    if per_family:
        fam = {}
        for f_ in sorted({A["by_id"][q].get("category") for q in qs}):
            fq = [q for q in qs if A["by_id"][q].get("category") == f_]
            fd, flo, fhi = boot([(scene_of(A["by_id"][q]),
                                  int(bool(A["by_id"][q]["correct"]))
                                  - int(bool(Bb["by_id"][q]["correct"])))
                                 for q in fq])
            fam[f_] = {"n": len(fq), "delta": round(fd, 4),
                       "ci": [round(flo, 4), round(fhi, 4)]}
            print(f"      {f_:<18} {fd:+.4f} [{flo:+.4f},{fhi:+.4f}] n={len(fq)}")
        out["by_family"] = fam
    return out


def main():
    print("=" * 100)
    print("ARM HEALTH -- confirmatory bank, 1328 questions on frames nothing "
          "was selected on")
    print("=" * 100)
    for n in ARMS:
        A = load(n)
        if A is None:
            print(f"{n:<10}{ARMS[n][0]:<24}[pending]")
            continue
        rows = A["order"]
        parsed = sum(r.get("pred") is not None for r in rows)
        run = best = 0
        for r in rows:
            run = run + 1 if r.get("pred") is None else 0
            best = max(best, run)
        acc = sum(bool(r["correct"]) for r in A["by_id"].values()) / len(A["by_id"])
        flag = "" if len(A["by_id"]) >= FULL_N else "  <- PARTIAL"
        print(f"{n:<10}{ARMS[n][0]:<24}n={len(A['by_id']):<6}acc={acc:.4f}  "
              f"parse={parsed/len(rows):.3f}  longest unparsed run={best}{flag}")

    print()
    print("=" * 100)
    print("A1 / A2 -- the confirmatory contrast, criteria frozen before the "
          "bank existed")
    print("=" * 100)
    a1 = contrast("v15_7b", "px_7b", "A1 v15 - pixel VLM, 7B", per_family=True)
    a2 = contrast("v15_3b", "px_3b", "A2 v15 - pixel VLM, 3B", per_family=True)

    print()
    print("=" * 100)
    print("A3 -- which system the paper leads with")
    print("=" * 100)
    a3a = contrast("v15_7b", "v9_7b", "A3a v15 - v9, 7B")
    a3b = contrast("v15_3b", "v9_3b", "A3b v15 - v9, 3B")
    print()
    print("for reference, the version the paper currently leads with:")
    contrast("v9_7b", "px_7b", "    v9 - pixel VLM, 7B")
    contrast("v9_3b", "px_3b", "    v9 - pixel VLM, 3B")

    print()
    print("=" * 100)
    print("VERDICTS")
    print("=" * 100)
    def v(name, c, rule, ok):
        if c is None:
            print(f"  {name:<5} PENDING  {rule}"); return None
        p = ok(c)
        print(f"  {name:<5} {'PASS' if p else 'FAIL':<8} {rule}")
        print(f"        observed {c['delta']:+.4f} "
              f"[{c['ci'][0]:+.4f},{c['ci'][1]:+.4f}], "
              f"{'significant' if c['sig'] else 'not significant'}, "
              f"{'above' if c['above_floor'] else 'below'} the floor")
        return p
    p1 = v("A1", a1, "v15 > pixel at 7B, CI lo > 0 and delta > +.006",
           lambda c: c["ci"][0] > 0 and c["delta"] > 0.006)
    p2 = v("A2", a2, "v15 > pixel at 3B, CI lo > 0 and delta > +.008",
           lambda c: c["ci"][0] > 0 and c["delta"] > 0.008)
    print()
    if a3a and a3b:
        worse = [nm for nm, c, fl in (("7B", a3a, 0.006), ("3B", a3b, 0.008))
                 if c["delta"] < -fl and c["ci"][1] < 0]
        if worse:
            print(f"  A3    KEEP v9 -- v15 is worse above the floor at "
                  f"{', '.join(worse)}")
        else:
            print("  A3    LEAD WITH v15 -- it is not worse than v9 above the "
                  "floor at either scale")
    print()
    print("  A criterion that was not met is a result. If A1 or A2 failed, the")
    print("  paper says the advantage did not replicate on unseen frames.")

    json.dump({"A1": a1, "A2": a2, "A3a": a3a, "A3b": a3b},
              open(Path(__file__).with_name("confirm_results.json"), "w"),
              indent=1)


if __name__ == "__main__":
    main()
