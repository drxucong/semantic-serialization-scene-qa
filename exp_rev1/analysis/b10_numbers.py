"""B10 edge-board numbers, read from the per-board summary.json files
(lvcworld/exp_rev1/b10_boards/{opi3b,hps_agilex5,orin_nano}/<run>/summary.json).
Units: latency s; memory GB = 1e9 B (peak_rss_mb and peak_sys_used_mb are MiB;
mem_available_before_kb is KiB); power W from tegrastats VDD_IN (Orin only), mean
over the measured window; energy per question = mean VDD_IN x window / n.
Writes b10_numbers.json and prints a table. Imported by make_b10.py."""
import json
from pathlib import Path

LV = Path(__file__).resolve().parents[2]  # repository root
B = LV / "exp_rev1/b10_boards"
MIB, KIB = 1048576 / 1e9, 1024 / 1e9
FILE_GB = {"qwen2.5-0.5b": 0.397807936, "qwen2.5-1.5b": 0.986048512, "qwen2.5-3b": 1.929903008,
           "qwen2.5-7b": 4.683073952, "moondream": 0.828661152 + 0.909777984,
           "qwen2.5vl-3b": 1.929901056 + 1.338428128}


def load(board, run):
    p = B / board / run / "summary.json"
    return json.load(open(p)) if p.exists() else None


def row(board, run, mem_from=None):
    s = load(board, run)
    if s is None:
        return None
    r = {"board": board, "run": run, "file_gb": FILE_GB.get(run.replace("-mem", "")), "load_status": s["load_status"],
         "avail0_gb": s["mem_available_before_kb"] * KIB}
    if s.get("n"):
        r.update(n=s["n"], acc=s["acc"], agree=round(s["agree_laptop"] * s["n"]), med=s["latency_median_s"],
                 mean=s["latency_mean_s"], p95=s["latency_p95_s"])
    if board == "orin_nano":
        r["min_avail_gb"] = (s["mem_available_before_kb"] - s["peak_sys_used_mb"] * 1024) * KIB
        if s.get("power_run_mw") and s.get("n"):
            w = s["t_measure_end"] - s["t_measure_start"]
            r.update(p_idle_w=s["power_idle_mw"]["VDD_IN"] / 1e3, p_run_w=s["power_run_mw"]["VDD_IN"] / 1e3,
                     p_cpugpu_w=s["power_run_mw"].get("VDD_CPU_GPU_CV", 0) / 1e3,
                     energy_j=s["power_run_mw"]["VDD_IN"] / 1e3 * w / s["n"], window_s=w)
    else:
        src = load(board, mem_from) if mem_from else s
        r["peak_gb"] = src["peak_rss_mb"] * MIB
    return r


ROWS = {
    "opi3b": [row("opi3b", "qwen2.5-0.5b", mem_from="qwen2.5-0.5b-mem"), row("opi3b", "qwen2.5-1.5b"),
              row("opi3b", "qwen2.5-3b"), row("opi3b", "moondream")],
    "hps_agilex5": [row("hps_agilex5", "qwen2.5-0.5b"), row("hps_agilex5", "qwen2.5-1.5b")],
    "orin_nano": [row("orin_nano", r) for r in ("qwen2.5-0.5b", "qwen2.5-1.5b", "qwen2.5-3b", "qwen2.5-7b",
                                                "moondream", "qwen2.5vl-3b")],
}

if __name__ == "__main__":
    out = {b: [r for r in rs if r] for b, rs in ROWS.items()}
    json.dump(out, open(Path(__file__).with_name("b10_numbers.json"), "w"), indent=1)
    for b, rs in out.items():
        for r in rs:
            print(b, {k: (round(v, 3) if isinstance(v, float) else v) for k, v in r.items() if k not in ("board",)})
