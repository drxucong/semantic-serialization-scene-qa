"""Is the emitted arg-min TRUE? (offline, zero GPU)

Why this exists. Both Mac readers say v10 < v9, and the family that loses on
both is path_object -- the exact family the new S1 line ("Closest to the
robot's forward path: <class>") was added to solve. A precomputed field can
only help if it is right. If the compiler's arg-min disagrees with the gold
answer, then v10 does not merely fail to help: it prints a confident wrong
answer at the top of the stream, which is strictly worse than v9 handing the
reader the raw list and letting it decide.

So, before touching the serializer again, measure the compiler's own accuracy
on the two new fields, on exactly the states the readers were given:

  S1 path arg-min   vs  gold answer of path_object questions
  S2 cross-class arg-min vs gold answer of nearest_class questions

and, for the losing families, cross-tabulate reader correctness against
whether the emitted field was true. That separates "the field is wrong" from
"the field is right but the reader ignored it".

New file; run_serializer_v10.py is untouched.
"""
import json, math, sys, collections
from pathlib import Path

UP = Path(".")  # repo root: banks/, states/, results/
CODA = UP / "phase10" / "coda"
STATES = json.load(open(UP / "states" / "states_kf_v9.json", encoding="utf-8"))
QA = [json.loads(l) for l in open(UP / "banks" / "qa_coda.jsonl", encoding="utf-8")]


# ---- the exact v10 field definitions, copied verbatim from the serializer ----
def lateral(g):
    return abs(g["dist"] * math.sin(math.radians(g["bearing"])))


def path_rank(g):
    return lateral(g) + g["dist"] / 10.0


def nearest_by_class(ags):
    near = {}
    for g in ags:
        near.setdefault(g["cls"], g)
    return near


def s1(st):
    ags = st["agents"]
    return min(ags, key=path_rank)["cls"] if ags else None


def s2(st):
    near = nearest_by_class(st["agents"])
    return min(near.items(), key=lambda kv: kv[1]["dist"])[0] if near else None


def gold_text(it):
    """the option TEXT of the gold letter, so we can compare class names"""
    ch = it.get("choices")
    ans = it.get("answer")
    if isinstance(ch, dict):
        return ch.get(ans)
    if isinstance(ch, list) and isinstance(ans, int):
        return ch[ans]
    return None


def norm(s):
    return (s or "").strip().lower()


def load_arm(d, f="state_typed__clean__forced.jsonl"):
    p = CODA / d / f
    if not p.exists():
        return None
    out = {}
    for line in open(p, encoding="utf-8"):
        r = json.loads(line)
        out[r["qa_id"]] = r
    return out


def main():
    by_fam = collections.defaultdict(list)
    for it in QA:
        by_fam[it["category"]].append(it)

    print("=" * 88)
    print("COMPILER TRUTH AUDIT -- is the field we now print actually correct?")
    print("=" * 88)
    checks = [("path_object", s1, "S1 forward-path arg-min"),
              ("nearest_class", s2, "S2 cross-class arg-min")]
    truth = {}
    for fam, fn, label in checks:
        items = by_fam.get(fam, [])
        hit = miss = skip = 0
        for it in items:
            st = STATES.get(it["sample_id"])
            g = gold_text(it)
            if st is None or g is None:
                skip += 1
                continue
            emitted = fn(st)
            ok = norm(emitted) == norm(g)
            truth[it["qa_id"]] = ok
            hit += ok
            miss += not ok
        n = hit + miss
        print(f"{label:<26} family={fam:<14} correct {hit}/{n} = "
              f"{hit/n if n else 0:.4f}   (skipped {skip})")

    # the readers' scores on those same families, for reference
    print()
    print("=" * 88)
    print("READER vs FIELD  (did the reader follow a true field / resist a false one?)")
    print("=" * 88)
    arms = [("v9  Mac 7B  ", "results_mac_v9_qwen7b"),
            ("v10 Mac 7B  ", "results_v10_d5_mac_qwen7b"),
            ("v9  Mac llama", "results_mac_v9_llama31"),
            ("v10 Mac llama", "results_v10_d5_mac_llama31")]
    for fam, _, label in checks:
        print(f"\n--- {fam}  ({label}) ---")
        print(f"{'arm':<14}{'acc|field TRUE':>16}{'acc|field FALSE':>18}"
              f"{'n_true':>8}{'n_false':>9}")
        for name, d in arms:
            A = load_arm(d)
            if A is None:
                print(f"{name:<14}  [pending]")
                continue
            t = [A[q]["correct"] for q in A
                 if truth.get(q) is True and A[q].get("category") == fam]
            f_ = [A[q]["correct"] for q in A
                  if truth.get(q) is False and A[q].get("category") == fam]
            at = sum(map(bool, t)) / len(t) if t else float("nan")
            af = sum(map(bool, f_)) / len(f_) if f_ else float("nan")
            print(f"{name:<14}{at:>16.4f}{af:>18.4f}{len(t):>8}{len(f_):>9}")

    # how often does the field, when false, name the option the reader picked?
    print()
    print("=" * 88)
    print("CAPTURE TEST -- when the field is FALSE, does the reader echo it?")
    print("=" * 88)
    qa_by_id = {it["qa_id"]: it for it in QA}
    for fam, fn, label in checks:
        for name, d in arms:
            if not name.startswith("v10"):
                continue
            A = load_arm(d)
            if A is None:
                continue
            echoed = tot = 0
            for q, r in A.items():
                if r.get("category") != fam or truth.get(q) is not False:
                    continue
                it = qa_by_id.get(q)
                st = STATES.get(r["sample_id"])
                if it is None or st is None or r.get("pred") is None:
                    continue
                ch = it.get("choices")
                picked = ch.get(r["pred"]) if isinstance(ch, dict) else None
                tot += 1
                echoed += norm(picked) == norm(fn(st))
            if tot:
                print(f"{name:<14} {fam:<14} reader echoed the false field "
                      f"{echoed}/{tot} = {echoed/tot:.4f}")


if __name__ == "__main__":
    main()


# ---------------------------------------------------------------------------
def rank_audit():
    """Where does the gold answer sit in the compiler's own ranking?

    If the gold is usually the runner-up, then emitting the top-2 plus the
    margin restores the reader's ability to overrule a wrong primary, at a
    cost of a few tokens -- which is what the design called for and what the
    implementation dropped.
    """
    by_fam = collections.defaultdict(list)
    for it in QA:
        by_fam[it["category"]].append(it)

    print()
    print("=" * 88)
    print("RANK AUDIT -- when the primary is wrong, where is the gold?")
    print("=" * 88)
    for fam, keyfn, pick, label in [
            ("path_object", path_rank, "all", "S1 path arg-min"),
            ("nearest_class", lambda g: g["dist"], "nearest", "S2 cross-class arg-min")]:
        pos = collections.Counter()
        absent = 0
        margins = []
        for it in by_fam[fam]:
            st = STATES.get(it["sample_id"])
            g = norm(gold_text(it))
            if st is None or not g:
                continue
            ags = st["agents"]
            if pick == "nearest":
                cand = sorted(nearest_by_class(ags).values(), key=keyfn)
            else:
                cand = sorted(ags, key=keyfn)
            order, seen = [], set()
            for a in cand:                       # dedupe to a class ranking
                c = norm(a["cls"])
                if c not in seen:
                    seen.add(c)
                    order.append((c, keyfn(a)))
            names = [c for c, _ in order]
            if g not in names:
                absent += 1
                continue
            r = names.index(g)
            pos[r] += 1
            if r == 1 and len(order) >= 2:
                margins.append(order[1][1] - order[0][1])
        tot = sum(pos.values()) + absent
        c1 = pos[0]
        c2 = pos[0] + pos[1]
        c3 = c2 + pos[2]
        print(f"\n{label}  (family {fam}, n={tot})")
        print(f"  gold = rank 1 (what we print)      {c1:>4}  {c1/tot:.4f}")
        print(f"  gold within top-2                  {c2:>4}  {c2/tot:.4f}")
        print(f"  gold within top-3                  {c3:>4}  {c3/tot:.4f}")
        print(f"  gold ABSENT from perceived state   {absent:>4}  {absent/tot:.4f}"
              f"   <- unreachable by any formatting")
        if margins:
            margins.sort()
            print(f"  when gold is rank 2, score margin: median "
                  f"{margins[len(margins)//2]:.3f}, P25 {margins[len(margins)//4]:.3f}"
                  f"  (small margin = the primary was a coin flip)")


rank_audit()
