"""Check that the serializer source in this folder is the code behind the released logs.

The runs of the text readers wrote, for every question, the number of characters of the text
that the reader received (`scene_chars`). This script serializes the released states again with the
code of this folder and compares:

  1. Scoped (run_serializer_v15.serialize_v15) against the logs of the confirmatory runs
     at 0.5B, 1.5B, 3B, and 7B, and of the development runs at 3B and 7B;
  2. Flat (run_coda_text_v9.typed_text) against the logs of the confirmatory runs;
  3. Scoped on the ground-truth objects against the logs of those runs;
  4. the five texts of exemplars/serialized_state_examples.json, character by character;
  5. serialize_dl(..., 'd0') against serialize_v15, character by character, on both banks.

It also writes the Scoped and the Flat text of every confirmatory question to
serialized_text_confirm.jsonl. Run from the repository root:

    python serializer/verify_serializer.py
"""
import json, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
sys.path.insert(0, str(HERE))
import run_coda_text_v9 as V9  # noqa: E402
from run_serializer_v15 import serialize_v15  # noqa: E402
from run_serializer_dladder import serialize_dl  # noqa: E402


def jl(p):
    return [json.loads(l) for l in open(p, encoding="utf-8")]


def log_chars(rel):
    ps = sorted((REPO / rel).glob("*forced.jsonl"))
    assert ps, rel
    return {r["qa_id"]: r["scene_chars"] for r in jl(ps[0])}


def main():
    cf, dev = jl(REPO / "banks/qa_confirm.jsonl"), jl(REPO / "banks/qa_coda.jsonl")
    st_cf = json.load(open(REPO / "states/states_confirm_v9.json", encoding="utf-8"))
    st_dev = json.load(open(REPO / "states/states_kf_v9.json", encoding="utf-8"))
    st_gt = json.load(open(REPO / "states/states_confirm_gt.json", encoding="utf-8"))
    ok = True

    def check(name, bank, states, fn, logs):
        nonlocal ok
        text = {it["qa_id"]: fn(states[it["sample_id"]], it["category"]) for it in bank if it["sample_id"] in states}
        for rel in logs:
            lc = log_chars(rel)
            n = sum(1 for q in lc if q in text)
            bad = sum(1 for q in lc if q in text and len(text[q]) != lc[q])
            ok &= (bad == 0 and n == len(lc))
            print(f"{name:28s} {rel:44s} questions {n:5d}  length differs {bad}")
        return text

    scoped = check("Scoped, confirmatory", cf, st_cf, serialize_v15,
                   ["results/phase10/results_cf_v15_0_5b", "results/phase10/results_cf_v15_1_5b",
                    "results/phase10/results_cf_v15_3b", "results/phase10/results_cf_v15_7b"])
    check("Scoped, development", dev, st_dev, serialize_v15,
          ["results/phase10/results_v15_d5_3b", "results/phase10/results_v15_d5_7b"])
    flat = check("Flat, confirmatory", cf, st_cf, lambda st, cat: V9.typed_text(st),
                 ["results/phase10/results_cf_v9_3b", "results/phase10/results_cf_v9_7b"])
    check("Scoped, ground-truth objects", cf, st_gt, lambda st, cat: serialize_dl(st, cat, "d0"),
          ["results/exp2_infer/gtcf_d0_3b", "results/exp2_infer/gtcf_d0_7b"])

    ex = json.load(open(REPO / "exemplars/serialized_state_examples.json", encoding="utf-8"))
    same = sum(1 for v in ex.values() if scoped.get(v["qa_id"]) == v["serialized_state_D0"])
    ok &= (same == len(ex))
    print(f"exemplars identical: {same} of {len(ex)}")

    diff = 0
    for bank, states in ((cf, st_cf), (dev, st_dev)):
        for it in bank:
            if it["sample_id"] in states:
                st = states[it["sample_id"]]
                diff += serialize_dl(st, it["category"], "d0") != serialize_v15(st, it["category"])
    ok &= (diff == 0)
    print(f"serialize_dl('d0') differs from serialize_v15 on {diff} questions of the two banks")

    with open(HERE / "serialized_text_confirm.jsonl", "w", encoding="utf-8") as f:
        for it in cf:
            f.write(json.dumps({"qa_id": it["qa_id"], "category": it["category"], "scoped": scoped[it["qa_id"]],
                                "flat": flat[it["qa_id"]]}) + "\n")
    print("wrote serializer/serialized_text_confirm.jsonl")
    print("ALL CHECKS PASSED" if ok else "CHECK FAILED")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
