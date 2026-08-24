"""Phase-2 step 8: reader-scale sweep analysis (Amendment A4, commit 8b17f17).

Builds the curve CSV (accuracy vs reader parameter count), runs the S1/S2
paired bootstraps through exp1_package/analysis_bootstrap.py, scans unparsed
rates, draws a draft matplotlib figure, and writes
exp2_runs/analysis/SUMMARY2.md. Raw numbers only, no interpretation.

Curve lines: D0@cf, D1@N2, GT-D0@cf (qwen2.5 0.5b..7b); pixel arms as
scatter (cross-family, descriptive). qwen3-vl:2b deviation arm reported in
a separate row, never in a contrast.
Usage: python scripts/paper/exp2_analysis.py
"""
import csv, json, re, subprocess, sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PY = sys.executable
BOOT = ROOT / "exp1_package" / "analysis_bootstrap.py"
OUT = ROOT / "exp2_runs" / "analysis"
PARAMS = json.load(open(ROOT / "exp2_runs" / "model_params.json",
                        encoding="utf-8"))

TXT = "state_typed__clean__forced.jsonl"
PX = "pixel__clean__forced.jsonl"

# (dir, file, arm, bank, model-key, curve-line)
SOURCES = [
    # D0 @ cf
    ("exp2_runs/infer/cf_d0_0.5b", TXT, "D0_05b", "cf", "qwen2.5:0.5b", "D0@cf"),
    ("exp2_runs/infer/cf_d0_1.5b", TXT, "D0_15b", "cf", "qwen2.5:1.5b", "D0@cf"),
    ("outputs/phase10/coda/results_cf_v15_3b", TXT, "D0_3b", "cf", "qwen2.5:3b", "D0@cf"),
    ("outputs/phase10/coda/results_cf_v15_7b", TXT, "D0_7b", "cf", "qwen2.5:7b", "D0@cf"),
    # D0 @ N2 (context line, exported in the CSV)
    ("exp2_runs/infer/n2_d0_0.5b", TXT, "D0_05b", "n2", "qwen2.5:0.5b", "D0@N2"),
    ("exp2_runs/infer/n2_d0_1.5b", TXT, "D0_15b", "n2", "qwen2.5:1.5b", "D0@N2"),
    ("exp1_runs/infer/n2_d0_3b", TXT, "D0_3b", "n2", "qwen2.5:3b", "D0@N2"),
    ("exp1_runs/infer/n2_d0_7b", TXT, "D0_7b", "n2", "qwen2.5:7b", "D0@N2"),
    # D1 @ N2
    ("exp2_runs/infer/n2_d1_0.5b", TXT, "D1_05b", "n2", "qwen2.5:0.5b", "D1@N2"),
    ("exp2_runs/infer/n2_d1_1.5b", TXT, "D1_15b", "n2", "qwen2.5:1.5b", "D1@N2"),
    ("exp1_runs/infer/n2_d1_3b", TXT, "D1_3b", "n2", "qwen2.5:3b", "D1@N2"),
    ("exp1_runs/infer/n2_d1_7b", TXT, "D1_7b", "n2", "qwen2.5:7b", "D1@N2"),
    # GT-D0 @ cf
    ("exp2_runs/infer/gtcf_d0_0.5b", TXT, "GT_05b", "gtcf", "qwen2.5:0.5b", "GT-D0@cf"),
    ("exp2_runs/infer/gtcf_d0_1.5b", TXT, "GT_15b", "gtcf", "qwen2.5:1.5b", "GT-D0@cf"),
    ("exp2_runs/infer/gtcf_d0_3b", TXT, "GT_3b", "gtcf", "qwen2.5:3b", "GT-D0@cf"),
    ("exp2_runs/infer/gtcf_d0_7b", TXT, "GT_7b", "gtcf", "qwen2.5:7b", "GT-D0@cf"),
    # pixel scatter
    ("outputs/phase10/coda/results_cf_px3b_robust", PX, "PIXEL_3b", "cf", "qwen2.5vl:3b", "pixel@cf"),
    ("outputs/phase10/coda/results_cf_px_7b", PX, "PIXEL_7b", "cf", "qwen2.5vl:7b", "pixel@cf"),
    ("exp1_runs/infer/n2_px_3b", PX, "PIXEL_3b", "n2", "qwen2.5vl:3b", "pixel@N2"),
    ("exp1_runs/infer/n2_px_7b", PX, "PIXEL_7b", "n2", "qwen2.5vl:7b", "pixel@N2"),
    ("exp2_runs/infer/px_moondream_cf", PX, "PX_moondream", "cf", "moondream", "pixel@cf"),
    ("exp2_runs/infer/px_moondream_n2", PX, "PX_moondream", "n2", "moondream", "pixel@N2"),
    ("exp2_runs/infer/px_llava-phi3_cf", PX, "PX_llavaphi3", "cf", "llava-phi3", "pixel@cf"),
    ("exp2_runs/infer/px_llava-phi3_n2", PX, "PX_llavaphi3", "n2", "llava-phi3", "pixel@N2"),
    # recorded-deviation arm: separate line tag, excluded from contrasts
    ("exp2_runs/infer/px_q3vl2b_cf", PX, "PXDEV_q3vl2b", "cf", "qwen3-vl:2b", "pixel-deviation@cf"),
]


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    rows, curve, unparsed, missing = [], [], {}, []
    for d, fn, arm, bank, mkey, line in SOURCES:
        p = ROOT / d / fn
        if not p.exists():
            missing.append(str(p))
            continue
        rs = [json.loads(l) for l in open(p, encoding="utf-8")]
        n = len(rs)
        nu = sum(r.get("pred") is None for r in rs)
        acc = sum(bool(r["correct"]) for r in rs) / n
        unparsed[f"{arm}@{bank}"] = (nu, n)
        curve.append({"line": line, "arm": arm, "bank": bank, "model": mkey,
                      "params": PARAMS[mkey]["param_count"], "n": n,
                      "acc": round(acc, 4),
                      "unparsed_pct": round(100 * nu / n, 2)})
        for r in rs:
            rows.append({"question_id": r["qa_id"],
                         "sequence_id": r["scene_name"],
                         "family": r.get("family", r["category"]),
                         "arm": arm, "bank": bank,
                         "correct": int(bool(r["correct"]))})
    if missing:
        print("MISSING:\n  " + "\n  ".join(missing))
        sys.exit(1)

    with open(OUT / "curve_points.csv", "w", newline="",
              encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(curve[0]))
        w.writeheader()
        w.writerows(curve)

    for bank in ("cf", "n2", "gtcf"):
        with open(OUT / f"predictions2_{bank}.csv", "w", newline="",
                  encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=[
                "question_id", "sequence_id", "family", "arm", "correct"])
            w.writeheader()
            for r in rows:
                if r["bank"] == bank:
                    w.writerow({k: r[k] for k in w.fieldnames})

    # ---------------- bootstraps ----------------
    def boot(bank, a, b, label, loso=False):
        cmd = [PY, str(BOOT), str(OUT / f"predictions2_{bank}.csv"), a, b,
               "--seed", "20260809"] + (["--loso"] if loso else [])
        r = subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT)
        out = (r.stdout + r.stderr).strip()
        m = re.search(r"Delta = ([+-][\d.]+)\s+95% CI \[([+-][\d.]+), "
                      r"([+-][\d.]+)\]\s*(\*?)", out)
        print("-" * 66 + f"\n### {label}\n{out}")
        return (label, bank, f"{a} vs {b}") + (m.groups() if m else
                                               ("?", "?", "?", "?"))

    contrasts = [
        boot("cf", "D0_05b", "PX_moondream", "S1 D0_0.5b vs moondream@cf (cross-family, descriptive)"),
        boot("cf", "D0_15b", "PX_moondream", "S1 D0_1.5b vs moondream@cf (cross-family, descriptive)"),
        boot("cf", "D0_15b", "PX_llavaphi3", "S1 D0_1.5b vs llava-phi3@cf (cross-family, descriptive)"),
        boot("n2", "D1_05b", "D0_05b", "S2 D1 vs D0 @N2, 0.5b (within-text)"),
        boot("n2", "D1_15b", "D0_15b", "S2 D1 vs D0 @N2, 1.5b (within-text)"),
        boot("n2", "D1_3b", "D0_3b", "S2 D1 vs D0 @N2, 3b (within-text)"),
        boot("n2", "D1_7b", "D0_7b", "S2 D1 vs D0 @N2, 7b (within-text)"),
        boot("n2", "D1_05b", "PX_moondream", "S2 D1_0.5b vs moondream@N2 (cross-family, descriptive)"),
        boot("n2", "D1_15b", "PX_moondream", "S2 D1_1.5b vs moondream@N2 (cross-family, descriptive)"),
        boot("gtcf", "GT_05b", "GT_15b", "GT curve step 0.5b vs 1.5b"),
        boot("gtcf", "GT_15b", "GT_3b", "GT curve step 1.5b vs 3b"),
        boot("gtcf", "GT_3b", "GT_7b", "GT curve step 3b vs 7b"),
    ]

    # ---------------- draft figure ----------------
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(figsize=(7, 5))
        lines = {}
        for c in curve:
            lines.setdefault(c["line"], []).append((c["params"], c["acc"]))
        for name, pts in lines.items():
            pts.sort()
            xs = [p / 1e9 for p, _ in pts]
            ys = [a for _, a in pts]
            if name.startswith("pixel"):
                mark = "x" if "deviation" in name else "o"
                ax.scatter(xs, ys, label=name, marker=mark)
            else:
                ax.plot(xs, ys, marker="s", label=name)
        ax.set_xscale("log")
        ax.set_xlabel("reader / decoder parameters (B, log)")
        ax.set_ylabel("accuracy")
        ax.grid(True, alpha=.3)
        ax.legend(fontsize=8)
        fig.tight_layout()
        fig.savefig(OUT / "sweep_draft.png", dpi=150)
        print(f"figure -> {OUT/'sweep_draft.png'}")
    except Exception as e:  # noqa: BLE001
        print(f"[warn] figure skipped: {e}")

    # ---------------- SUMMARY2 ----------------
    with open(OUT / "SUMMARY2.md", "w", encoding="utf-8") as f:
        f.write("# Amendment A4 -- sweep summary (raw, no interpretation)\n\n")
        f.write("## curve points (accuracy vs parameters)\n\n")
        f.write("| line | arm | bank | model | params | n | acc | unparsed% |\n")
        f.write("|---|---|---|---|---|---|---|---|\n")
        for c in sorted(curve, key=lambda c: (c["line"], c["params"])):
            f.write(f"| {c['line']} | {c['arm']} | {c['bank']} | {c['model']} "
                    f"| {c['params']/1e9:.2f}B | {c['n']} | {c['acc']:.4f} "
                    f"| {c['unparsed_pct']:.2f} |\n")
        f.write("\n## contrasts (21 clusters, B=20000, seed 20260809; "
                "cross-family rows are descriptive per A4)\n\n")
        f.write("| contrast | bank | arms | Delta | 95% CI | sig |\n")
        f.write("|---|---|---|---|---|---|\n")
        for label, bank, arms, d, lo, hi, star in contrasts:
            f.write(f"| {label} | {bank} | {arms} | {d} | [{lo}, {hi}] "
                    f"| {star} |\n")
        f.write("\n## unparsed scan (discipline 6: >20% unusable)\n\n")
        bad = []
        for k in sorted(unparsed):
            nu, n = unparsed[k]
            pct = 100 * nu / n
            if pct > 20:
                bad.append(k)
            f.write(f"- {k}: {nu}/{n} ({pct:.2f}%)"
                    + ("  **OVER 20%**" if pct > 20 else "") + "\n")
        f.write("\n## phase-2 artefact index\n\n")
        f.write("- step 1: exp2_runs/seq20_diagnostic.md\n")
        f.write("- step 2: exp2_runs/baselines.md (+ bootstrap vs readers)\n")
        f.write("- step 2b: exp2_runs/baselines_n1n2.md\n")
        f.write("- step 3: exp2_runs/occlusion_audit.json + clean-subset "
                "contrasts in LOG.md\n")
        f.write("- step 7: exp2_runs/compute_table.md\n")
        if bad:
            f.write("\n**FLAGGED ARMS (>20% unparsed):** " + ", ".join(bad)
                    + "\n")
    print(f"summary -> {OUT/'SUMMARY2.md'}")


if __name__ == "__main__":
    main()
