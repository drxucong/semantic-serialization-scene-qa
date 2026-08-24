"""M1 exactly as pre-registered at 06:45Z:

  "on the path_object subset where the S1 field is FALSE, v11 - v10 CI lower > 0"

and the matching M2 shape for counting, so both are tested on the subset the
repair was aimed at rather than on the whole family.
"""
import json, math, re, random, collections
from pathlib import Path

UP = Path("/mnt/user-data/uploads/lvcworld/outputs")
CODA = UP / "phase10" / "coda"
STATES = json.load(open(UP / "coda" / "states_kf_v9.json", encoding="utf-8"))
QA = {json.loads(l)["qa_id"]: json.loads(l)
      for l in open(UP / "coda" / "qa_coda.jsonl", encoding="utf-8")}
B, SEED = 20000, 0


def lateral(g): return abs(g["dist"] * math.sin(math.radians(g["bearing"])))
def path_rank(g): return lateral(g) + g["dist"] / 10.0
def norm(s): return (s or "").strip().lower()


def near_by_cls(ags):
    n = {}
    for g in ags:
        n.setdefault(g["cls"], g)
    return n


def load(d):
    p = CODA / d / "state_typed__clean__forced.jsonl"
    if not p.exists():
        return None
    r = {json.loads(l)["qa_id"]: json.loads(l) for l in open(p, encoding="utf-8")}
    return r if len(r) >= 1366 else None


def boot(pairs):
    scenes = sorted({s for s, _ in pairs})
    by = collections.defaultdict(list)
    for s, v in pairs:
        by[s].append(v)
    rng = random.Random(SEED); st = []
    for _ in range(B):
        acc = []
        for _ in scenes:
            acc.extend(by[rng.choice(scenes)])
        st.append(sum(acc) / len(acc))
    st.sort()
    d = sum(sum(v) for v in by.values()) / sum(len(v) for v in by.values())
    return d, st[int(.025 * B)], st[int(.975 * B)]


def tgt(it):
    m = re.search(r"'([^']+)'", it["question"])
    return m.group(1) if m else None


# subsets where the compiled verdict is WRONG
false_path, false_cnt = set(), set()
for q, it in QA.items():
    st = STATES.get(it["sample_id"])
    if st is None:
        continue
    gold = norm(it["choices"].get(it["answer"]))
    if it["category"] == "path_object" and st["agents"]:
        if norm(min(st["agents"], key=path_rank)["cls"]) != gold:
            false_path.add(q)
    if it["category"] == "counting":
        k = tgt(it)
        hi = sum(1 for g in st["agents"] if g["cls"] == k and not g.get("lowconf"))
        try:
            if int(gold) != hi:
                false_cnt.add(q)
        except (TypeError, ValueError):
            pass

print(f"subset sizes: path_object with FALSE arg-min = {len(false_path)}, "
      f"counting with FALSE header = {len(false_cnt)}")


def test(a, b, subset, label, rule):
    A, Bb = load(a), load(b)
    if A is None or Bb is None:
        print(f"{label:<44} [pending]")
        return
    qs = [q for q in subset if q in A and q in Bb]
    pairs = [(A[q].get("scene_name") or q.split("_")[1],
              int(bool(A[q]["correct"])) - int(bool(Bb[q]["correct"]))) for q in qs]
    d, lo, hi = boot(pairs)
    aa = sum(bool(A[q]["correct"]) for q in qs) / len(qs)
    bb = sum(bool(Bb[q]["correct"]) for q in qs) / len(qs)
    v = "PASS" if lo > 0 else "FAIL"
    print(f"{label:<44} {aa:.4f} vs {bb:.4f}  {d:+.4f} [{lo:+.4f},{hi:+.4f}]  "
          f"n={len(qs)}   {rule} -> {v}")


print()
print("=" * 104)
print("PRE-REGISTERED MECHANISM TESTS (subset the repair was aimed at)")
print("=" * 104)
test("results_v11_d5_7b", "results_v10_d5_7b", false_path,
     "M1  v11 - v10 | S1 FALSE, path_object @7B", "CI lo > 0")
test("results_v11_d5_3b", "results_v10_d5_3b", false_path,
     "M1  v11 - v10 | S1 FALSE, path_object @3B", "CI lo > 0")
test("results_v11b_d5_7b", "results_v11_d5_7b", false_cnt,
     "M2  v11b - v11 | count FALSE @7B", "CI lo > 0")
test("results_v11b_d5_3b", "results_v11_d5_3b", false_cnt,
     "M2  v11b - v11 | count FALSE @3B", "CI lo > 0")
print()
print("reference: same subsets, v9 vs v10 (what was lost in the first place)")
test("results_v10_d5_7b", "results_system9_kf_7b", false_path,
     "     v10 - v9  | S1 FALSE, path_object @7B", "(ref)")
test("results_v10_d5_7b", "results_system9_kf_7b", false_cnt,
     "     v10 - v9  | count FALSE @7B", "(ref)")
test("results_v11_d5_7b", "results_system9_kf_7b", false_path,
     "     v11 - v9  | S1 FALSE, path_object @7B", "(ref)")
