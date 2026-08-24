"""The last two experiments, judged against criteria frozen before the arms ran.

Two levers came out of the perception error decomposition, and only these two
were worth compute:

  RELABEL   fix the LABEL of detections we already have          priced +.0864
  TEMPORAL  carry in objects a neighbouring frame saw and this   priced +.0454
            one missed (the dense CODa_sm split makes this
            possible at all: median frame gap 2-3 vs tiny's 15)

and one pre-registered PREDICTION that could falsify the menu the whole plan is
built on:

  T-DROP    plain temporal filtering -- delete detections no        priced -.0124
            neighbour supports -- must come out <= 0.

Every contrast is same-machine (5090), paired by qa_id, bootstrapped over scene
clusters (B=20000, seed 0). Every verdict is additionally checked against the
measured reproducibility floor: two runs of one identical arm differ by +-.006
at 7B and +-.008 at 3B purely from serving nondeterminism, so a bootstrap
interval that excludes zero is necessary but NOT sufficient.

Controls are shared and exact: all relabel and temporal arms use serializer v15
on states derived from states_kf_v9_xy, and their control is v15 on
states_kf_v9_xy itself. The only thing that differs inside each contrast is the
perceived state.

Usage: python late_analysis.py [uploads_root]
New file; v10_analysis.py is untouched.
"""
import json, random, sys, collections
from pathlib import Path

ROOT = Path(sys.argv[1] if len(sys.argv) > 1
            else "/mnt/user-data/uploads/lvcworld/outputs")
CODA = ROOT / "phase10" / "coda"
B, SEED = 20000, 0
FULL_N = 1366
FLOOR = {"7B": 0.006, "3B": 0.008, "8B": 0.006}

F = "state_typed__clean__forced.jsonl"
ARMS = {
    # --- shared controls -------------------------------------------------
    "ctl_7b":    ("results_v15_xy_7b",    F, "qwen2.5:7b", "7B"),
    "ctl_3b":    ("results_v15_xy_3b",    F, "qwen2.5:3b", "3B"),
    # --- relabel ---------------------------------------------------------
    "relab_7b":  ("results_v15_relab_7b", F, "qwen2.5:7b", "7B"),
    "relab_3b":  ("results_v15_relab_3b", F, "qwen2.5:3b", "3B"),
    # --- temporal --------------------------------------------------------
    "tadd_7b":   ("results_v15_tadd_7b",  F, "qwen2.5:7b", "7B"),
    "tdrop_7b":  ("results_v15_tdrop_7b", F, "qwen2.5:7b", "7B"),
    "tboth_7b":  ("results_v15_tboth_7b", F, "qwen2.5:7b", "7B"),
    "tadd_3b":   ("results_v15_tadd_3b",  F, "qwen2.5:3b", "3B"),
    # --- reference points already in hand --------------------------------
    "v15_7b":    ("results_v15_d5_7b",    F, "qwen2.5:7b", "7B"),
    "v15_3b":    ("results_v15_d5_3b",    F, "qwen2.5:3b", "3B"),
    "v9_7b":     ("results_system9_kf_7b", F, "qwen2.5:7b", "7B"),
    "v9_3b":     ("results_v9_3b",        F, "qwen2.5:3b", "3B"),
    "px_7b":     ("results_qwen2.5vl_7b_retry", "pixel__clean__forced.jsonl",
                  "qwen2.5vl:7b", "7B"),
    "px_3b":     ("results_px3b_robust",  "pixel__clean__forced.jsonl",
                  "qwen2.5vl:3b", "3B"),
}


def load(name):
    d, f, *_ = ARMS[name]
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


def health(name, A):
    rows = A["order"]
    n = len(A["by_id"])
    parsed = [r for r in rows if r.get("pred") is not None]
    run = best = 0
    for r in rows:
        run = run + 1 if r.get("pred") is None else 0
        best = max(best, run)
    acc = sum(bool(r["correct"]) for r in A["by_id"].values()) / n
    return {"arm": name, "n": n, "complete": n >= FULL_N, "acc": round(acc, 4),
            "parse": round(len(parsed) / len(rows), 4),
            "longest_unparsed_run": best}


def contrast(a, b, label, per_family=False):
    A, Bb = load(a), load(b)
    if A is None or Bb is None:
        miss = a if A is None else b
        print(f"{label:<52} [pending: {ARMS[miss][0]}]")
        return None
    for nm, X in ((a, A), (b, Bb)):
        if len(X["by_id"]) < FULL_N:
            print(f"{label:<52} [partial: {nm} has {len(X['by_id'])}/{FULL_N}"
                  f" -- refusing to score a prefix]")
            return None
    qs = sorted(set(A["by_id"]) & set(Bb["by_id"]))
    pairs = [(scene_of(A["by_id"][q]),
              int(bool(A["by_id"][q]["correct"]))
              - int(bool(Bb["by_id"][q]["correct"]))) for q in qs]
    d, lo, hi = boot(pairs)
    sig = lo > 0 or hi < 0
    fl = FLOOR[ARMS[a][3]]
    above = abs(d) > fl
    tag = "*" if sig else " "
    note = "" if above else f"  <- below the {fl:+.3f} run-noise floor"
    aa = sum(bool(A["by_id"][q]["correct"]) for q in qs) / len(qs)
    bb = sum(bool(Bb["by_id"][q]["correct"]) for q in qs) / len(qs)
    print(f"{label:<52} {aa:.4f} vs {bb:.4f}  {d:+.4f} "
          f"[{lo:+.4f},{hi:+.4f}]{tag} n={len(qs)}{note}")
    out = {"label": label, "a": a, "b": b, "accA": round(aa, 4),
           "accB": round(bb, 4), "delta": round(d, 4),
           "ci": [round(lo, 4), round(hi, 4)], "n": len(qs),
           "sig": bool(sig), "above_floor": bool(above),
           "resolved": bool(sig and above)}
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
            print(f"      {f_:<20} {fd:+.4f} [{flo:+.4f},{fhi:+.4f}] n={len(fq)}")
        out["by_family"] = fam
    return out


def verdict(name, c, rule, ok):
    if c is None:
        print(f"  {name:<12} PENDING   {rule}")
        return
    print(f"  {name:<12} {'PASS' if ok(c) else 'FAIL':<9} {rule}")
    print(f"               observed {c['delta']:+.4f} "
          f"[{c['ci'][0]:+.4f},{c['ci'][1]:+.4f}] "
          f"{'significant' if c['sig'] else 'not significant'}, "
          f"{'above' if c['above_floor'] else 'below'} the run-noise floor")


def main():
    res = {"health": [], "contrasts": {}, "verdicts": {}}

    print("=" * 100)
    print("ARM HEALTH  (a partial arm is never scored; parse faults hid a "
          "serving bug for two runs)")
    print("=" * 100)
    print(f"{'arm':<12}{'dir':<26}{'n':>6}{'acc':>9}{'parse':>8}"
          f"{'longest unparsed run':>22}")
    for name in ARMS:
        A = load(name)
        if A is None:
            print(f"{name:<12}{ARMS[name][0]:<26}{'[pending]':>6}")
            continue
        h = health(name, A)
        res["health"].append(h)
        flag = "" if h["complete"] else "   <- PARTIAL"
        print(f"{name:<12}{ARMS[name][0]:<26}{h['n']:>6}{h['acc']:>9.4f}"
              f"{h['parse']:>8.3f}{h['longest_unparsed_run']:>22}{flag}")

    print()
    print("=" * 100)
    print("EXPERIMENT R -- RELABEL: does fixing detection labels reach the answers?")
    print("=" * 100)
    r1 = contrast("relab_7b", "ctl_7b",
                  "R1 PRIMARY   relabelled - as-is, 7B", per_family=True)
    r2 = contrast("relab_3b", "ctl_3b", "R2 secondary relabelled - as-is, 3B")
    res["contrasts"]["R1"] = r1; res["contrasts"]["R2"] = r2

    print()
    print("=" * 100)
    print("EXPERIMENT T -- TEMPORAL: neighbour frames, three ways")
    print("=" * 100)
    t1 = contrast("tadd_7b", "ctl_7b",
                  "T1 PRIMARY   carry-in (T-ADD) - as-is, 7B", per_family=True)
    t2 = contrast("tdrop_7b", "ctl_7b",
                  "T2 PREDICTION filter (T-DROP) - as-is, 7B")
    t3 = contrast("tboth_7b", "ctl_7b", "T3 secondary T-BOTH - as-is, 7B")
    t4 = contrast("tadd_3b", "ctl_3b", "T4 secondary T-ADD - as-is, 3B")
    for k, v in (("T1", t1), ("T2", t2), ("T3", t3), ("T4", t4)):
        res["contrasts"][k] = v

    print()
    print("=" * 100)
    print("CONTEXT -- what the hot state and the shipped system cost each other")
    print("=" * 100)
    res["contrasts"]["C1"] = contrast(
        "ctl_7b", "v15_7b", "C1 hot state - shipped state, v15, 7B")
    res["contrasts"]["C2"] = contrast(
        "ctl_3b", "v15_3b", "C2 hot state - shipped state, v15, 3B")
    res["contrasts"]["C3"] = contrast("v15_7b", "v9_7b", "C3 v15 - v9, 7B")
    res["contrasts"]["C4"] = contrast("v15_3b", "v9_3b", "C4 v15 - v9, 3B")
    res["contrasts"]["C5"] = contrast("v15_7b", "px_7b",
                                      "C5 v15 - pixel VLM, 7B  (hard floor)")
    res["contrasts"]["C6"] = contrast("v15_3b", "px_3b",
                                      "C6 v15 - pixel VLM, 3B  (hard floor)")

    print()
    print("=" * 100)
    print("VERDICTS against the criteria frozen before these arms existed")
    print("=" * 100)
    verdict("R1", r1, "relabelled > as-is at 7B, CI lo > 0 AND delta > +.006",
            lambda c: c["ci"][0] > 0 and c["delta"] > 0.006)
    verdict("T1", t1, "T-ADD > as-is at 7B, CI lo > 0 AND delta > +.006",
            lambda c: c["ci"][0] > 0 and c["delta"] > 0.006)
    verdict("T2", t2, "T-DROP <= 0 at 7B (falsifiable: the price menu said "
                      "ghost deletion HURTS)",
            lambda c: c["delta"] <= 0)
    print()
    print("  R2/T3/T4 carry no bar; they are reported to show the shape.")
    print("  A criterion that was not met is a result. Nothing below the")
    print("  run-noise floor is called a win whatever its interval says.")

    out = Path(__file__).with_name("late_results.json")
    json.dump(res, open(out, "w"), indent=1)
    print(f"\nwrote {out}")


if __name__ == "__main__":
    main()
