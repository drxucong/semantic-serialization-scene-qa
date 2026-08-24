"""Amendment A3 step-5 analysis driver (freeze commit dca34c1).

Builds predictions.csv from the frozen prediction files, runs every contrast
of d_ladder_spec.md through exp1_package/analysis_bootstrap.py (21 clusters,
B=20000, seed 20260809), computes the P2 attenuation, and emits one summary
table. No interpretive edits: numbers are printed as computed.

Prediction sources (existing outputs reused per the frozen pairing rule):
  D0 confirmatory   outputs/phase10/coda/results_cf_v15_{3b,7b}
  PIXEL confirmatory outputs/phase10/coda/results_cf_px_7b, results_cf_px3b_robust
  D1/D2/D3 confirmatory + all N1/N2 arms: exp1_runs/infer/*

correct: unparsed (pred null) counts 0, exactly as stored by the runners.
Usage: python scripts/paper/exp1_analysis.py [--csv-only]
"""
import argparse, csv, json, re, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PY = sys.executable
BOOT = ROOT / "exp1_package" / "analysis_bootstrap.py"
OUT = ROOT / "exp1_runs" / "analysis"

# (path, file, arm label, bank tag)
SOURCES = []
for scale in ("3b", "7b"):
    SOURCES += [
        (f"outputs/phase10/coda/results_cf_v15_{scale}",
         "state_typed__clean__forced.jsonl", f"D0_{scale}", "cf"),
        (f"exp1_runs/infer/cf_d1_{scale}",
         "state_typed__clean__forced.jsonl", f"D1_{scale}", "cf"),
        (f"exp1_runs/infer/cf_d2_{scale}",
         "state_typed__clean__forced.jsonl", f"D2_{scale}", "cf"),
        (f"exp1_runs/infer/cf_d3_{scale}",
         "state_typed__clean__forced.jsonl", f"D3_{scale}", "cf"),
        (f"exp1_runs/infer/n1_d0_{scale}",
         "state_typed__clean__forced.jsonl", f"D0_{scale}", "n1"),
        (f"exp1_runs/infer/n1_d1_{scale}",
         "state_typed__clean__forced.jsonl", f"D1_{scale}", "n1"),
        (f"exp1_runs/infer/n2_d0_{scale}",
         "state_typed__clean__forced.jsonl", f"D0_{scale}", "n2"),
        (f"exp1_runs/infer/n2_d1_{scale}",
         "state_typed__clean__forced.jsonl", f"D1_{scale}", "n2"),
        (f"exp1_runs/infer/n1_px_{scale}",
         "pixel__clean__forced.jsonl", f"PIXEL_{scale}", "n1"),
        (f"exp1_runs/infer/n2_px_{scale}",
         "pixel__clean__forced.jsonl", f"PIXEL_{scale}", "n2"),
    ]
SOURCES += [
    ("outputs/phase10/coda/results_cf_px3b_robust",
     "pixel__clean__forced.jsonl", "PIXEL_3b", "cf"),
    ("outputs/phase10/coda/results_cf_px_7b",
     "pixel__clean__forced.jsonl", "PIXEL_7b", "cf"),
]


def qid_norm(qa_id, bank):
    """pair N1 rows with their source item id space, keep others as-is"""
    return qa_id


def build_csv():
    OUT.mkdir(parents=True, exist_ok=True)
    rows, missing, unparsed = [], [], {}
    for d, fn, arm, bank in SOURCES:
        p = ROOT / d / fn
        if not p.exists():
            missing.append(str(p))
            continue
        n = nu = 0
        for line in open(p, encoding="utf-8"):
            r = json.loads(line)
            fam = r.get("family", r["category"])
            rows.append({
                "question_id": r["qa_id"], "sequence_id": r["scene_name"],
                "family": fam, "arm": arm, "bank": bank,
                "correct": int(bool(r["correct"]))})
            n += 1
            nu += r.get("pred") is None
        unparsed[f"{arm}@{bank}"] = (nu, n)
    if missing:
        print("MISSING prediction files:\n  " + "\n  ".join(missing))
        sys.exit(1)
    for bank in ("cf", "n1", "n2"):
        fp = OUT / f"predictions_{bank}.csv"
        with open(fp, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=[
                "question_id", "sequence_id", "family", "arm", "correct"])
            w.writeheader()
            for r in rows:
                if r["bank"] == bank:
                    w.writerow({k: r[k] for k in w.fieldnames})
        print(f"wrote {fp}")
    print("\nunparsed-rate scan (discipline 6: >20% file is unusable):")
    bad = []
    for k in sorted(unparsed):
        nu, n = unparsed[k]
        pct = 100.0 * nu / max(n, 1)
        flag = "  <-- OVER 20%" if pct > 20 else ""
        print(f"  {k:14} unparsed {nu:5d}/{n}  ({pct:5.2f}%){flag}")
        if pct > 20:
            bad.append(k)
    return bad


def run_boot(bank, a, b, family=None, loso=False):
    cmd = [PY, str(BOOT), str(OUT / f"predictions_{bank}.csv"), a, b,
           "--seed", "20260809"]
    if family:
        cmd += ["--family", family]
    if loso:
        cmd += ["--loso"]
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT)
    out = (r.stdout + r.stderr).strip()
    m = re.search(r"Delta = ([+-][\d.]+)\s+95% CI \[([+-][\d.]+), "
                  r"([+-][\d.]+)\]\s*(\*?)", out)
    return out, (m.groups() if m else None)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv-only", action="store_true")
    a = ap.parse_args()
    bad = build_csv()
    if a.csv_only:
        return

    # every contrast in d_ladder_spec.md, both scales; family filters on the
    # confirmatory bank use the repo category names carried into the csv
    contrasts = []
    for s in ("3b", "7b"):
        contrasts += [
            ("cf", f"D1_{s}", f"PIXEL_{s}", None, True,  "P1 D1 vs PIXEL (all)"),
            ("cf", f"D1_{s}", f"PIXEL_{s}", "counting", False, "P1 counting"),
            ("cf", f"D1_{s}", f"PIXEL_{s}", "nearest_dist", False, "P1 nearest-distance"),
            ("cf", f"D0_{s}", f"D1_{s}",    None, False, "band vocab value (leak bound)"),
            ("cf", f"D2_{s}", f"D1_{s}",    None, False, "discretisation beyond vocab"),
            ("cf", f"D3_{s}", f"PIXEL_{s}", None, False, "negative control"),
            ("n1", f"D0_{s}", f"PIXEL_{s}", None, True,  "P2 D0 vs PIXEL on N1"),
            ("n1", f"D1_{s}", f"PIXEL_{s}", None, False, "D1 vs PIXEL on N1"),
            ("n2", f"D0_{s}", f"PIXEL_{s}", None, False, "D0 vs PIXEL on N2"),
            ("n2", f"D1_{s}", f"PIXEL_{s}", None, True,  "P3 D1 vs PIXEL on N2"),
            ("cf", f"D0_{s}", f"PIXEL_{s}", None, False, "reference Dconf (for P2)"),
        ]
    results = {}
    lines = []
    for bank, x, y, fam, loso, label in contrasts:
        out, g = run_boot(bank, x, y, fam, loso)
        key = (bank, x, y, fam)
        results[key] = g
        star = g[3] if g else "?"
        d, lo, hi = (g[0], g[1], g[2]) if g else ("?", "?", "?")
        lines.append(f"| {label} | {bank} | {x} vs {y} | {fam or 'all'} | "
                     f"{d} | [{lo}, {hi}] | {star} |")
        print("-" * 70)
        print(f"### {label}")
        print(out)

    # P2 attenuation per scale: 1 - Delta(N1)/Delta(conf), overall contrast
    print("=" * 70)
    att_lines = []
    for s in ("3b", "7b"):
        try:
            dc = float(results[("cf", f"D0_{s}", f"PIXEL_{s}", None)][0])
            dn = float(results[("n1", f"D0_{s}", f"PIXEL_{s}", None)][0])
            att = 1.0 - dn / dc if dc else float("nan")
            att_lines.append(
                f"| P2 attenuation {s} | Delta_conf {dc:+.4f} | "
                f"Delta_N1 {dn:+.4f} | attenuation {att:.3f} | "
                f"{'P2 HOLDS (<0.5)' if att < 0.5 else 'P2 FAILS (>=0.5)'} |")
        except (TypeError, KeyError):
            att_lines.append(f"| P2 attenuation {s} | ? | ? | ? | ? |")

    md = ROOT / "exp1_runs" / "analysis" / "SUMMARY.md"
    with open(md, "w", encoding="utf-8") as f:
        f.write("# Amendment A3 -- contrast summary (raw, no interpretation)\n\n")
        f.write("21 clusters, B=20000, seed 20260809, percentile CI. "
                "`*` = CI excludes 0.\n\n")
        f.write("| contrast | bank | arms | family | Delta | 95% CI | sig |\n")
        f.write("|---|---|---|---|---|---|---|\n")
        f.write("\n".join(lines) + "\n\n")
        f.write("| P2 | Delta_conf | Delta_N1 | attenuation | verdict |\n")
        f.write("|---|---|---|---|---|\n")
        f.write("\n".join(att_lines) + "\n")
        if bad:
            f.write("\n**UNPARSED >20% (flagged unusable per discipline 6):** "
                    + ", ".join(bad) + "\n")
    print(f"summary table -> {md}")
    for l in att_lines:
        print(l)


if __name__ == "__main__":
    main()
