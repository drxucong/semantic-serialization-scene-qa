"""Phase-3 step 6: SUMMARY3 assembly (A5 + addendum, commits 1f47f6f/71812cc).

Collects every Phase-3 number (deviation rerun, Qwen3 arms, cf blind, M1
matrix), runs the paired bootstraps, scans unparsed, writes
exp3_runs/analysis/SUMMARY3.md. Raw numbers only.
Usage: python scripts/paper/exp3_analysis.py [--with-7b]
"""
import argparse, csv, json, re, subprocess, sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PY = sys.executable
BOOT = ROOT / "exp1_package" / "analysis_bootstrap.py"
OUT = ROOT / "exp3_runs" / "analysis"

SOURCES = [
    ("exp3_runs/infer/blind_cf_3b/blind__clean__forced.jsonl", "BLIND_3b"),
    ("exp3_runs/infer/blind_cf_7b/blind__clean__forced.jsonl", "BLIND_7b"),
    ("exp3_runs/infer/qwen3_4b_d0_cf/state_typed__clean__forced.jsonl", "Q3TXT4B_D0"),
    ("exp3_runs/infer/qwen3_8b_d0_cf/state_typed__clean__forced.jsonl", "Q3TXT8B_D0"),
    ("exp3_runs/infer/qwen3vl_4b_cf/pixel__clean__forced.jsonl", "Q3VL4B"),
    ("exp3_runs/infer/qwen3vl_8b_cf/pixel__clean__forced.jsonl", "Q3VL8B"),
    ("exp3_runs/infer/px_q3vl2b_cf_t1024/pixel__clean__forced.jsonl", "PXDEV_t1024"),
    ("exp3_runs/infer/zs3b_lowres_cf/pixel__clean__forced.jsonl", "ZS3B_low"),
    ("exp3_runs/infer/ft3b_lowres_cf/pixel__clean__forced.jsonl", "FT3B_low"),
    ("outputs/phase10/coda/results_cf_v15_3b/state_typed__clean__forced.jsonl", "D0_3b"),
    ("outputs/phase10/coda/results_cf_v15_7b/state_typed__clean__forced.jsonl", "D0_7b"),
    ("outputs/phase10/coda/results_cf_px3b_robust/pixel__clean__forced.jsonl", "PIXEL_3b"),
    ("outputs/phase10/coda/results_cf_px_7b/pixel__clean__forced.jsonl", "PIXEL_7b"),
]
SOURCES_7B = [("exp3_runs/infer/ft7b_lowres_cf/pixel__clean__forced.jsonl",
               "FT7B_low"),
              ("exp3_runs/infer/zs3b_fullres_hf_cf/pixel__clean__forced.jsonl",
               "ZS3B_full_hf")]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--with-7b", action="store_true")
    a = ap.parse_args()
    src = SOURCES + (SOURCES_7B if a.with_7b else [])
    OUT.mkdir(parents=True, exist_ok=True)

    rows, stats = [], {}
    for p, arm in src:
        fp = ROOT / p
        rs = [json.loads(l) for l in open(fp, encoding="utf-8")]
        nu = sum(r.get("pred") is None for r in rs)
        fam = defaultdict(list)
        for r in rs:
            fam[r["category"]].append(bool(r["correct"]))
            rows.append({"question_id": r["qa_id"],
                         "sequence_id": r["scene_name"],
                         "family": r["category"], "arm": arm,
                         "correct": int(bool(r["correct"]))})
        stats[arm] = {
            "n": len(rs), "unparsed": nu,
            "unp_pct": round(100 * nu / len(rs), 2),
            "acc": round(sum(bool(r["correct"]) for r in rs) / len(rs), 4),
            "fam": {k: round(sum(v) / len(v), 3) for k, v in sorted(fam.items())}}

    csv_p = OUT / "predictions3_cf.csv"
    with open(csv_p, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["question_id", "sequence_id",
                                          "family", "arm", "correct"])
        w.writeheader()
        w.writerows(rows)

    def boot(x, y, label, fam=None):
        cmd = [PY, str(BOOT), str(csv_p), x, y, "--seed", "20260809"]
        if fam:
            cmd += ["--family", fam]
        r = subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT)
        out = r.stdout + r.stderr
        m = re.search(r"Delta = ([+-][\d.]+)\s+95% CI \[([+-][\d.]+), "
                      r"([+-][\d.]+)\]\s*(\*?)", out)
        print(f"### {label}\n{out.strip()}")
        return (label, f"{x} vs {y}", fam or "all") + \
            (m.groups() if m else ("?",) * 4)

    contrasts = [
        boot("Q3TXT4B_D0", "Q3VL4B", "Qwen3 family interface contrast, 4B"),
        boot("Q3TXT8B_D0", "Q3VL8B", "Qwen3 family interface contrast, 8B"),
        boot("ZS3B_low", "PIXEL_3b",
             "ZS low (HF bf16) vs ZS full (ollama Q4) -- resolution AND "
             "runtime/quant differ; deconfounding fullres-HF run queued"),
        boot("FT3B_low", "ZS3B_low", "fine-tuning effect at matched resolution"),
        boot("FT3B_low", "PIXEL_3b", "FT vs original full-res ZS (system change)"),
        boot("D0_3b", "FT3B_low", "M1 headline: D0_3b vs fine-tuned pixel"),
        boot("D0_7b", "FT3B_low", "D0_7b vs fine-tuned 3B pixel"),
        boot("D0_3b", "PIXEL_3b", "reference zero-shot Delta, 3B"),
        boot("D0_7b", "PIXEL_7b", "reference zero-shot Delta, 7B"),
    ]
    if a.with_7b:
        contrasts += [
            boot("FT7B_low", "ZS3B_low", "FT-7B vs ZS-3B low (descriptive)"),
            boot("D0_7b", "FT7B_low", "M1 at 7B: D0_7b vs fine-tuned 7B pixel"),
            boot("FT7B_low", "FT3B_low", "FT scale step 7B vs 3B"),
            boot("ZS3B_low", "ZS3B_full_hf",
                 "clean resolution effect (same HF bf16 runtime)"),
            boot("ZS3B_full_hf", "PIXEL_3b",
                 "runtime/quant effect (same full resolution)"),
        ]

    md = OUT / ("SUMMARY3.md" if not a.with_7b else "SUMMARY3_full.md")
    with open(md, "w", encoding="utf-8") as f:
        f.write("# Phase-3 SUMMARY3 -- raw numbers, no interpretation\n\n")
        f.write("A5 (1f47f6f) + addendum (71812cc). Deviations recorded "
                "inline; deviation arm descriptive only.\n\n")
        f.write("## arm accuracies (cf, forced 3-choice)\n\n")
        f.write("| arm | n | acc | unparsed% | per-family |\n")
        f.write("|---|---|---|---|---|\n")
        for arm, s in stats.items():
            fams = " ".join(f"{k[:9]}={v}" for k, v in s["fam"].items())
            f.write(f"| {arm} | {s['n']} | {s['acc']:.4f} | "
                    f"{s['unp_pct']} | {fams} |\n")
        f.write("\n## contrasts (21 clusters, B=20000, seed 20260809)\n\n")
        f.write("| contrast | arms | family | Delta | 95% CI | sig |\n")
        f.write("|---|---|---|---|---|---|\n")
        for label, arms, fam, d, lo, hi, star in contrasts:
            f.write(f"| {label} | {arms} | {fam} | {d} | [{lo}, {hi}] "
                    f"| {star} |\n")
        f.write("\n## deviations in force\n\n")
        f.write("- PXDEV_t1024: qwen3-vl:2b thinking budget 1024 vs 8 tokens "
                "everywhere else; favorable asymmetry; descriptive only.\n")
        f.write("- Qwen3 arms: HF chat template instead of ollama's; "
                "Qwen3-8B run in official non-thinking mode.\n")
        f.write("- FT arm + ZS-low control: max_pixels=401408 (512*28*28) "
                "for training AND inference; grid reduced to r=16, "
                "lr in {1e-4, 5e-5}; winner ep2 kept "
                "(val .8841/.8817 -> lr1e-4; ep2 .9016).\n")
        f.write("- FT hyperparameters for 7B transferred from the 3B "
                "selection, not re-selected.\n")
        f.write("- CONFOUND NOTE: ZS3B_low is transformers bf16 while the "
                "legacy full-res ZS arm (PIXEL_3b) is ollama Q4_K_M; their "
                "difference mixes resolution with runtime/quantization. A "
                "transformers full-res ZS run is queued to deconfound. "
                "FT-vs-ZS_low is unaffected (same runtime, same "
                "resolution).\n")
        f.write("\n## step-5 artefact index\n\n")
        f.write("- exp3_runs/writing_exports/table2_per_family.md\n")
        f.write("- exp3_runs/writing_exports/blind_audit.md "
                "(cf blind gap CLOSED by BLIND_3b/7b above)\n")
        f.write("- exp3_runs/writing_exports/qualitative/{win_scoped,"
                "fail_nearest_class}/\n")
        f.write("- exp3_runs/writing_exports/arms_master_table.md\n")
        f.write("- 7B QLoRA smoke: PASSED (100 steps, 34.6 min, loss .145); "
                + ("full 7B included above.\n" if a.with_7b else
                   "full 7B running, addendum to follow.\n"))
    print(f"wrote {md}")


if __name__ == "__main__":
    main()
