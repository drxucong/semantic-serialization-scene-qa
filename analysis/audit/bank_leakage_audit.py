"""Standardized bank-leakage / shortcut audit (moat P1).

Mandatory gate for EVERY question bank before any trained arm or surplus
measurement uses it. Stdlib-only checks (runs anywhere):
  1. forced-track letter balance (abstain removed, re-lettered)
  2. numeric gold-rank distribution (pick-smallest/-largest/-middle shortcuts)
  3. gold vs distractor category-text frequency divergence (implausible
     distractor bias: texts that appear as distractors but ~never as gold)
  4. band-option gold balance (each textual band should be gold comparably)
  5. exact template-majority shortcut under the md5%5 scene split
  6. duplicate (question+options) collisions across the split
The nonlinear text-probe ladder (TF-IDF/GBM) is the cloud-side extension;
run it where sklearn is available. New file (no-overwrite).

Usage: python bank_leakage_audit.py --qa outputs/rebuild/qa_womd_v3.jsonl \
         --out outputs/audit/leakage_womd_v3.json
"""
import argparse, collections, hashlib, json, re
from pathlib import Path


def forced(it):
    opts = [t for l, t in sorted(it["choices"].items())
            if l != it.get("abstain_letter")]
    letters = "ABCD"[:len(opts)]
    ch = {l: t for l, t in zip(letters, opts)}
    gold = it["choices"][it["answer"]]
    return ch, (letters[opts.index(gold)] if gold in opts else None)


def is_eval(scene):
    return int(hashlib.md5(scene.encode()).hexdigest(), 16) % 5 == 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--qa", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    qa = [json.loads(l) for l in open(args.qa, encoding="utf-8")]
    rep = {"bank": args.qa, "n_raw": len(qa)}

    letters = collections.Counter()
    rank = collections.defaultdict(collections.Counter)
    gold_txt = collections.defaultdict(collections.Counter)
    dis_txt = collections.defaultdict(collections.Counter)
    tmpl = collections.defaultdict(collections.Counter)   # train side
    tmpl_eval = []
    dup_train, n_ab = set(), 0
    items = []
    for it in qa:
        ch, ans = forced(it)
        if ans is None:
            n_ab += 1
            continue
        items.append((it, ch, ans))
        letters[ans] += 1
        vals = {}
        for l, t in ch.items():
            m = re.fullmatch(r"-?\d+\.?\d*\s*(m|meters)?", t.strip())
            if m:
                vals[l] = float(re.search(r"-?\d+\.?\d*", t).group())
        if len(vals) == len(ch) and len(vals) >= 3:
            order = sorted(vals, key=vals.get)
            rank[it["category"]][order.index(ans)] += 1
        for l, t in ch.items():
            key = t if len(t) < 40 else t[:40]
            (gold_txt if l == ans else dis_txt)[it["category"]][key] += 1
        sig = it["question"] + "||" + "|".join(sorted(ch.values()))
        if is_eval(it["scene_name"]):
            tmpl_eval.append((sig, ans))
        else:
            tmpl[sig][ans] += 1
            dup_train.add(sig)

    tot = sum(letters.values())
    rep["dropped_gold_abstain"] = n_ab
    rep["letter_dist"] = {k: round(v / tot, 4) for k, v in sorted(letters.items())}
    rep["numeric_gold_rank"] = {
        c: {str(k): round(v / sum(cnt.values()), 4) for k, v in sorted(cnt.items())}
        for c, cnt in rank.items()}

    # implausible-distractor flags: texts with >=10 distractor uses and
    # distractor:gold ratio >= 5 (never/rarely gold)
    flags = {}
    for c in dis_txt:
        bad = []
        for t, dv in dis_txt[c].most_common():
            gv = gold_txt[c].get(t, 0)
            if dv >= 10 and dv >= 5 * max(gv, 1):
                bad.append([t, dv, gv])
        if bad:
            flags[c] = bad[:10]
    rep["implausible_distractor_flags"] = flags

    # band balance: categories whose options are a small closed text set
    band = {}
    for c in gold_txt:
        texts = set(gold_txt[c]) | set(dis_txt[c])
        if 2 <= len(texts) <= 6:
            n = sum(gold_txt[c].values())
            band[c] = {t: round(gold_txt[c].get(t, 0) / n, 4) for t in sorted(texts)}
    rep["band_gold_balance"] = band

    # template-majority shortcut on the scene split
    cov = hit = 0
    for sig, ans in tmpl_eval:
        if sig in tmpl:
            cov += 1
            hit += tmpl[sig].most_common(1)[0][0] == ans
    rep["template_shortcut"] = {
        "eval_n": len(tmpl_eval), "covered": cov,
        "majority_acc_on_covered": round(hit / cov, 4) if cov else None}

    # verdicts
    warns = []
    for c, d in rep["numeric_gold_rank"].items():
        if any(v >= 0.45 for v in d.values()):
            warns.append(f"numeric-rank bias in {c}: {d}")
    for c, d in band.items():
        if any(v >= 0.55 or v <= 0.05 for v in d.values()):
            warns.append(f"band imbalance in {c}: {d}")
    if flags:
        warns.append(f"implausible distractors in: {sorted(flags)}")
    rep["warnings"] = warns
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    json.dump(rep, open(args.out, "w"), indent=1)
    print(f"[audit] {args.qa}: {len(warns)} warnings", flush=True)
    for w in warns:
        print("  WARN:", w, flush=True)


if __name__ == "__main__":
    main()
