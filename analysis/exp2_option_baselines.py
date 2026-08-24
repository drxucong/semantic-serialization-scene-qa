"""Phase-2 step 2: option-aware deterministic baselines ("Why keep the LLM").

Both baselines read ONLY the compiled perceived state and the option text.
Everything tunable is fixed or fitted on the DEVELOPMENT bank
(qa_coda.jsonl + states_kf_v9.json, 1366 items) and evaluated once on the
CONFIRMATORY bank (qa_confirm.jsonl + states_confirm_v9.json, forced
3-choice via the frozen forced_choices rule). No LLM anywhere.

B1  rule-based option scorer: each option is parsed and mapped to a query
    against the compiled state (count comparison, band comparison, class
    match incl. runner-up, sector comparison); argmax score, ties broken by
    fixed letter order.
B2  shallow learners on per-option features: logistic regression and
    gradient-boosted trees (sklearn), P(correct|option), argmax per item.

Outputs: exp2_runs/baselines.md + exp2_runs/baseline_preds.csv (for the
paired bootstrap vs the D0 readers).
Usage: python scripts/paper/exp2_option_baselines.py
"""
import csv, json, re, sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
for p in ("scripts/pilot", "scripts/coda", "scripts/paper"):
    sys.path.insert(0, str(ROOT / p))
from run_pilot_phase0 import forced_choices  # noqa: E402
import run_coda_text_v9 as V9  # noqa: E402
import run_serializer_v12 as V12  # noqa: E402

BANDS = ("under 5 meters away", "5 to 15 meters away", "over 15 meters away")
DIRS = ("on the left side", "in the center", "on the right side")


def load_bank(qa, states_path):
    states = json.load(open(ROOT / states_path, encoding="utf-8"))
    items = []
    for line in open(ROOT / qa, encoding="utf-8"):
        it = json.loads(line)
        if it["sample_id"] not in states:
            continue
        fch, fans = forced_choices(it)
        if fans is None:
            continue
        items.append((it, fch, fans, states[it["sample_id"]]))
    return items


def queried_class(question, known):
    m = re.search(r"'([^']+)'", question or "")
    if m:
        return m.group(1)
    for k in sorted(known, key=len, reverse=True):
        if k.lower() in (question or "").lower():
            return k
    return None


def state_facts(st, category, question):
    """the compiled facts every baseline works from"""
    ags = st["agents"]
    known = {a["cls"] for a in ags}
    tc = queried_class(question, known)
    f = {"tc": tc, "n_obj": len(ags), "n_cls": len(known)}
    f["conf_n"] = sum(1 for a in ags if a["cls"] == tc and not a.get("lowconf"))
    f["unc_n"] = sum(1 for a in ags if a["cls"] == tc and a.get("lowconf"))
    cand = [a for a in ags if a["cls"] == tc] or ags
    w = min(cand, key=lambda g: g["dist"]) if cand else None
    f["near_dist"] = w["dist"] if w else None
    f["near_band"] = V9.band(w["dist"]) + " away" if w else None
    f["near_conf"] = w.get("conf", 1.0) if w else 0.0
    f["near_lowconf"] = bool(w and w.get("lowconf"))
    f["edge_margin"] = (min(abs(w["dist"] - 5), abs(w["dist"] - 15))
                       if w else None)
    f["sector"] = V12.sector(w) if w else None
    f["sector_margin_px"] = None
    if w and w.get("u") is not None:
        f["sector_margin_px"] = min(abs(w["u"] - 1224 / 3),
                                    abs(w["u"] - 2 * 1224 / 3))
    near = V12.nearest_by_cls(ags)
    order = sorted(near.values(), key=lambda g: g["dist"])
    f["nc1"] = order[0]["cls"] if order else None
    f["nc2"] = order[1]["cls"] if len(order) > 1 else None
    f["nc_margin"] = (order[1]["dist"] - order[0]["dist"]
                      if len(order) > 1 else 99.0)
    corr = sorted((a for a in ags if V12.in_corridor(a)),
                  key=lambda g: g["dist"])
    f["po1"] = corr[0]["cls"] if corr else None
    po2 = next((a for a in corr if a["cls"] != f["po1"]), None)
    f["po2"] = po2["cls"] if po2 else None
    f["po_margin"] = (po2["dist"] - corr[0]["dist"]) if po2 else 99.0
    return f


def rule_scores(category, opts, f):
    """B1: per-option score, higher = better. Deterministic."""
    s = {}
    for L, t in opts.items():
        t = t.strip()
        sc = 0.0
        if category == "counting" and t.isdigit():
            sc = -abs(int(t) - f["conf_n"])
            if int(t) == f["conf_n"] + f["unc_n"]:
                sc = max(sc, -0.5)          # dev-fixed: total-count near-match
        elif category == "nearest_dist" and t in BANDS:
            sc = 1.0 if t == f["near_band"] else 0.0
        elif category == "direction" and t in DIRS:
            sc = 1.0 if t == f["sector"] else 0.0
        elif category == "nearest_class":
            sc = 1.0 if t == f["nc1"] else (0.5 if t == f["nc2"] else 0.0)
        elif category == "path_object":
            sc = 1.0 if t == f["po1"] else (0.5 if t == f["po2"] else 0.0)
        s[L] = sc
    return s


def rule_pick(category, opts, f):
    s = rule_scores(category, opts, f)
    best = max(s.values())
    return sorted(L for L in opts if s[L] == best)[0]   # fixed letter order


FAMS = ("counting", "direction", "nearest_class", "nearest_dist", "path_object")


def option_features(category, L, t, opts, f):
    """B2 feature vector for one (item, option) pair (list order is frozen
    in FEATURE_NAMES)."""
    t = t.strip()
    x = []
    x += [1.0 if category == c else 0.0 for c in FAMS]
    x.append(1.0 if t.isdigit() else 0.0)
    x.append(1.0 if t in BANDS else 0.0)
    x.append(1.0 if t in DIRS else 0.0)
    x.append(1.0 if (not t.isdigit() and t not in BANDS and t not in DIRS)
             else 0.0)
    rs = rule_scores(category, opts, f)
    x.append(rs[L])
    x.append(1.0 if rule_pick(category, opts, f) == L else 0.0)
    x.append(abs(int(t) - f["conf_n"]) if t.isdigit() else -1.0)
    x.append(abs(int(t) - f["conf_n"] - f["unc_n"]) if t.isdigit() else -1.0)
    x.append(float(f["unc_n"]))
    x.append(1.0 if (f["near_band"] and t == f["near_band"]) else 0.0)
    x.append(f["near_dist"] if f["near_dist"] is not None else -1.0)
    x.append(f["edge_margin"] if f["edge_margin"] is not None else -1.0)
    x.append(1.0 if (f["sector"] and t == f["sector"]) else 0.0)
    x.append(f["sector_margin_px"] if f["sector_margin_px"] is not None
             else -1.0)
    x.append(1.0 if t == f["nc1"] else 0.0)
    x.append(1.0 if t == f["nc2"] else 0.0)
    x.append(f["nc_margin"])
    x.append(1.0 if t == f["po1"] else 0.0)
    x.append(1.0 if t == f["po2"] else 0.0)
    x.append(f["po_margin"])
    x.append(f["near_conf"])
    x.append(1.0 if f["near_lowconf"] else 0.0)
    x.append(float(f["n_obj"]))
    x.append(float(f["n_cls"]))
    x.append(1.0 if f["tc"] else 0.0)
    return x


FEATURE_NAMES = (
    [f"fam_{c}" for c in FAMS] +
    ["opt_is_number", "opt_is_band", "opt_is_direction", "opt_is_class",
     "rule_score", "rule_pick",
     "cnt_absdiff_conf", "cnt_absdiff_total", "unc_count",
     "band_match", "near_dist_m", "band_edge_margin_m",
     "sector_match", "sector_margin_px",
     "is_nearest_class", "is_runnerup_class", "nearest_class_margin_m",
     "is_path_argmin", "is_path_runnerup", "path_margin_m",
     "winner_det_conf", "winner_lowconf", "n_objects", "n_classes",
     "queried_class_present"])


def featurize(items):
    X, y, meta = [], [], []
    for it, fch, fans, st in items:
        f = state_facts(st, it["category"], it["question"])
        for L, t in fch.items():
            X.append(option_features(it["category"], L, t, fch, f))
            y.append(1 if L == fans else 0)
            meta.append((it["qa_id"], it["scene_name"], it["category"], L,
                         fans))
    return X, y, meta


def pick_argmax(meta, proba):
    by_item = defaultdict(list)
    for (qid, seq, cat, L, ans), p in zip(meta, proba):
        by_item[qid].append((L, p, seq, cat, ans))
    preds = {}
    for qid, lst in by_item.items():
        lst.sort(key=lambda x: (-x[1], x[0]))     # prob desc, letter asc
        preds[qid] = (lst[0][0], lst[0][2], lst[0][3], lst[0][4])
    return preds


def acc_table(preds):
    tot = Counter()
    hit = Counter()
    for qid, (L, seq, cat, ans) in preds.items():
        tot[cat] += 1
        tot["all"] += 1
        if L == ans:
            hit[cat] += 1
            hit["all"] += 1
    return {k: hit[k] / tot[k] for k in tot}


def main():
    dev = load_bank("outputs/coda/qa_coda.jsonl",
                    "outputs/coda/states_kf_v9.json")
    cf = load_bank("outputs/coda/qa_confirm.jsonl",
                   "outputs/coda/states_confirm_v9.json")
    print(f"dev {len(dev)} items, cf {len(cf)} items")

    # ---- B1 rules ----
    results = {}
    for name, items in (("dev", dev), ("cf", cf)):
        preds = {}
        for it, fch, fans, st in items:
            f = state_facts(st, it["category"], it["question"])
            preds[it["qa_id"]] = (rule_pick(it["category"], fch, f),
                                  it["scene_name"], it["category"], fans)
        results[("rule", name)] = (acc_table(preds), preds)
        print(f"B1 rule@{name}: {results[('rule', name)][0]['all']:.4f}")

    # ---- B2 learners: fit on dev, evaluate on cf ----
    import numpy as np
    from sklearn.ensemble import GradientBoostingClassifier
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler
    Xd, yd, md = featurize(dev)
    Xc, yc, mc = featurize(cf)
    Xd, Xc = np.array(Xd), np.array(Xc)
    models = {
        "logreg": make_pipeline(StandardScaler(),
                                LogisticRegression(max_iter=2000, C=1.0)),
        "gbtree": GradientBoostingClassifier(random_state=20260810),
    }
    for name, m in models.items():
        m.fit(Xd, yd)
        for split, X, meta in (("dev", Xd, md), ("cf", Xc, mc)):
            proba = m.predict_proba(X)[:, 1]
            preds = pick_argmax(meta, proba)
            results[(name, split)] = (acc_table(preds), preds)
        print(f"B2 {name}: dev {results[(name,'dev')][0]['all']:.4f}  "
              f"cf {results[(name,'cf')][0]['all']:.4f}")

    # ---- write per-item preds for the paired bootstrap ----
    outdir = ROOT / "exp2_runs"
    with open(outdir / "baseline_preds.csv", "w", newline="",
              encoding="utf-8") as fcsv:
        w = csv.writer(fcsv)
        w.writerow(["question_id", "sequence_id", "family", "arm", "correct"])
        for name in ("rule", "logreg", "gbtree"):
            for qid, (L, seq, cat, ans) in results[(name, "cf")][1].items():
                w.writerow([qid, seq, cat, f"BASE_{name}",
                            int(L == ans)])

    # ---- markdown table ----
    fams = list(FAMS)
    with open(outdir / "baselines.md", "w", encoding="utf-8") as f:
        f.write("# Option-aware deterministic baselines (fit on dev, "
                "evaluated on cf)\n\n")
        f.write("Features used by B2 (frozen list):\n\n```\n" +
                ", ".join(FEATURE_NAMES) + "\n```\n\n")
        f.write("| system | cf overall | " + " | ".join(fams) + " |\n")
        f.write("|---|---|" + "---|" * len(fams) + "\n")
        for name in ("rule", "logreg", "gbtree"):
            t = results[(name, "cf")][0]
            f.write(f"| BASE_{name} | {t['all']:.4f} | " +
                    " | ".join(f"{t.get(c, float('nan')):.3f}"
                               for c in fams) + " |\n")
        f.write("\n(dev-split accuracies: rule "
                f"{results[('rule','dev')][0]['all']:.4f}, logreg "
                f"{results[('logreg','dev')][0]['all']:.4f}, gbtree "
                f"{results[('gbtree','dev')][0]['all']:.4f}; "
                "option-blind closed-form reference from the paper: .619)\n")
    print(f"wrote {outdir/'baselines.md'} and baseline_preds.csv")


if __name__ == "__main__":
    main()
