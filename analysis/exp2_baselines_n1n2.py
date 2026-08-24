"""Phase-2 step 2b: frozen option-aware baselines evaluated AS-IS on N1/N2.

Protocol (checkpoint-1 decision, 2026-08-10): no refitting, no parser repair,
no feature change. The B2 learners are re-materialized by the identical
deterministic fit on the development bank (same data, same hyperparameters,
fixed random_state) and applied unchanged. Options that fail to parse or map
score zero for every candidate; the resulting tie falls through to the fixed
letter-order tie-break and is counted as answered (wrong unless lucky). That
brittleness IS the measurement target.

Family mapping bank->baseline categories is the same fixed table the reader
runner uses (adapter level, not a parser change).

Usage: python scripts/paper/exp2_baselines_n1n2.py
"""
import csv, json, sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "paper"))
from exp2_option_baselines import (FAMS, featurize, load_bank,  # noqa: E402
                                   pick_argmax, rule_pick, state_facts)
from run_serializer_dladder import FAMILY_TO_CATEGORY  # noqa: E402

STATES = "outputs/coda/states_confirm_v9.json"


def load_schema_bank(path):
    states = json.load(open(ROOT / STATES, encoding="utf-8"))
    items = []
    for line in open(ROOT / path, encoding="utf-8"):
        q = json.loads(line)
        if q["frame_id"] not in states:
            continue
        it = {"qa_id": q["question_id"], "sample_id": q["frame_id"],
              "scene_name": q["sequence_id"],
              "category": FAMILY_TO_CATEGORY[q["family"]],
              "question": q["stem"]}
        items.append((it, q["options"], q["gold"], states[q["frame_id"]]))
    return items


def acc_table(preds):
    tot, hit = Counter(), Counter()
    for qid, (L, seq, cat, ans) in preds.items():
        tot[cat] += 1
        tot["all"] += 1
        if L == ans:
            hit[cat] += 1
            hit["all"] += 1
    return {k: hit[k] / tot[k] for k in tot}


def main():
    import numpy as np
    from sklearn.ensemble import GradientBoostingClassifier
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler

    dev = load_bank("outputs/coda/qa_coda.jsonl",
                    "outputs/coda/states_kf_v9.json")
    Xd, yd, _ = featurize(dev)
    Xd = np.array(Xd)
    models = {
        "logreg": make_pipeline(StandardScaler(),
                                LogisticRegression(max_iter=2000, C=1.0)),
        "gbtree": GradientBoostingClassifier(random_state=20260810),
    }
    for m in models.values():
        m.fit(Xd, yd)                       # identical deterministic re-fit

    banks = {"n1": load_schema_bank("exp1_runs/frozen/n1_bank.jsonl"),
             "n2": load_schema_bank("exp1_runs/frozen/n2_bank.jsonl")}
    rows_out = []
    table = {}
    for bname, items in banks.items():
        # B1 rules
        preds = {}
        for it, opts, gold, st in items:
            f = state_facts(st, it["category"], it["question"])
            preds[it["qa_id"]] = (rule_pick(it["category"], opts, f),
                                  it["scene_name"], it["category"], gold)
        table[("rule", bname)] = acc_table(preds)
        for qid, (L, seq, cat, ans) in preds.items():
            rows_out.append([qid, seq, cat, f"BASE_rule", int(L == ans),
                             bname])
        # B2 learners
        X, y, meta = [], [], []
        from exp2_option_baselines import option_features
        for it, opts, gold, st in items:
            f = state_facts(st, it["category"], it["question"])
            for L, t in opts.items():
                X.append(option_features(it["category"], L, t, opts, f))
                y.append(1 if L == gold else 0)
                meta.append((it["qa_id"], it["scene_name"], it["category"],
                             L, gold))
        X = np.array(X)
        for name, m in models.items():
            proba = m.predict_proba(X)[:, 1]
            preds = pick_argmax(meta, proba)
            table[(name, bname)] = acc_table(preds)
            for qid, (L, seq, cat, ans) in preds.items():
                rows_out.append([qid, seq, cat, f"BASE_{name}",
                                 int(L == ans), bname])

    with open(ROOT / "exp2_runs" / "baseline_preds_n1n2.csv", "w",
              newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["question_id", "sequence_id", "family", "arm", "correct",
                    "bank"])
        w.writerows(rows_out)

    with open(ROOT / "exp2_runs" / "baselines_n1n2.md", "w",
              encoding="utf-8") as f:
        f.write("# Frozen baselines evaluated as-is on N1/N2 "
                "(no refit, no parser repair)\n\n")
        for bname in ("n1", "n2"):
            fams = sorted({c for (m, b), t in table.items() if b == bname
                           for c in t if c != "all"})
            f.write(f"## {bname}\n\n| system | overall | " +
                    " | ".join(fams) + " |\n")
            f.write("|---|---|" + "---|" * len(fams) + "\n")
            for name in ("rule", "logreg", "gbtree"):
                t = table[(name, bname)]
                f.write(f"| BASE_{name} | {t['all']:.4f} | " +
                        " | ".join(f"{t.get(c, float('nan')):.3f}"
                                   for c in fams) + " |\n")
            f.write("\n")
    for k in sorted(table):
        print(k, round(table[k]["all"], 4))
    print("wrote exp2_runs/baselines_n1n2.md + baseline_preds_n1n2.csv")


if __name__ == "__main__":
    main()
