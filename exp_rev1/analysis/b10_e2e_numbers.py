#!/usr/bin/env python3
"""Numbers of the Jetson Orin Nano end-to-end session (one session, one condition:
25 W mode, desktop running) -> analysis/b10_e2e_numbers.json, read by build_paper.py.

Source: exp_rev1/b10_boards/orin_nano_e2e/ (copy of ~/rev1/out_e2e_desktop_on on the
board; written by scripts/rev1/run_b10_orin_e2e.sh).

Definitions
  one question, new frame   mean wall time over the 50 probe questions (prompt cache off)
  power                     mean VDD_IN while answering (tegrastats, 100 ms)
  energy                    power x mean time
  five questions, one frame mean total time of 5 questions (one per family) on each of
                            10 frames, server prompt cache on; energy = mean VDD_IN over
                            the run x run time / 10 frames
  detector pair             slope of the perceiver's wall time over 1, 11, 41 frames;
                            power over the frame loop of the 41-frame run; energy =
                            power x (loop time / 41)
  serialized system         detector pair + reader (sum of the two rows)
"""
import json, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
LV = Path(__file__).resolve().parents[2]  # repository root
D = LV / "exp_rev1/b10_boards/orin_nano_e2e"


def J(p):
    return json.load(open(D / p, encoding="utf-8"))


t = J("perception_timing.json")
r41 = t["runs"]["41"]
perc_s = t["per_frame_s_slope"]; perc_w = r41["loop"]["vdd_in_mean_mw"] / 1000; perc_j = perc_w * r41["loop_s"] / 41
O = {"perc_s": f"{perc_s:.2f}", "perc_w": f"{perc_w:.1f}", "perc_j": f"{perc_j:.1f}",
     "perc_loop_s": f"{r41['loop_s'] / 41:.3f}", "perc_fixed_s": f"{t['fixed_s']:.1f}",
     "idle_w": f"{t['idle']['vdd_in_mean_mw'] / 1000:.1f}",
     "perc_min_avail_gb": f"{r41['loop']['min_avail_kb'] / 1e6:.2f}",
     "ser_ms": f"{J('serializer_onboard.json')['serializer_ms_per_item']:.2f}",
     "cores_min_avail_gb": f"{J('coresident.json')['min_avail_kb'] / 1e6:.2f}"}
raw = {"perc_s": perc_s, "perc_j": perc_j}


def bench(tag, d, agree=True):
    s = J(f"{d}/summary.json")
    w = s["power_run_mw"]["VDD_IN"] / 1000; m = s["latency_mean_s"]
    O.update({f"{tag}_s": f"{m:.2f}", f"{tag}_med": f"{s['latency_median_s']:.2f}", f"{tag}_w": f"{w:.1f}", f"{tag}_j": f"{w * m:.1f}",
              f"{tag}_acc": f"{s['acc']:.2f}", f"{tag}_parse": f"{s['parse']:.2f}",
              f"{tag}_agree": f"{round(s['agree_laptop'] * s['n'])}/{s['n']}" if agree else "---"})
    raw[f"{tag}_s"] = m; raw[f"{tag}_j"] = w * m


def series(tag, d):
    s = J(f"{d}/summary.json")
    e = s["vdd_in_mean_mw"] / 1000 * s["window_s"] / s["frames"]
    O.update({f"{tag}_s5": f"{s['per_frame_5q_mean_s']:.2f}", f"{tag}_j5": f"{e:.1f}",
              f"{tag}_first": f"{s['first_turn_median_s']:.2f}", f"{tag}_later": f"{s['later_turn_median_s']:.2f}",
              f"{tag}_s5_min_avail_gb": f"{s['min_avail_kb'] / 1e6:.2f}"})
    raw[f"{tag}_s5"] = s["per_frame_5q_mean_s"]; raw[f"{tag}_j5"] = e


bench("r15", "e2e-qwen2.5-1.5b", agree=False); bench("r3", "e2e-qwen2.5-3b"); bench("r7", "e2e-qwen2.5-7b")
bench("md", "moondream"); bench("vl", "qwen2.5vl-3b")
# The probe file on the board carries the laptop answers of the first 3B VLM run, which had the
# serving fault (Section VI); the paper's 3B VLM arm is the guarded re-run. Agreement is recomputed
# against that arm here.
_REL = LV / "results/phase10/results_cf_px3b_robust/pixel__clean__forced.jsonl"
_lap = {json.loads(l)["qa_id"]: json.loads(l).get("pred") for l in open(_REL, encoding="utf-8")}
_it = [json.loads(l) for l in open(D / "qwen2.5vl-3b/items.jsonl", encoding="utf-8")]
O["vl_agree"] = f"{sum(r['pred'] == _lap[r['qa_id']] for r in _it)}/{len(_it)}"
for tag, d in (("s05", "qwen2.5-0.5b"), ("s15", "qwen2.5-1.5b"), ("s3", "qwen2.5-3b"), ("s7", "qwen2.5-7b")):
    bench(tag, d)                                   # readers on the shipped-stack prompts (laptop states)
series("r15", "series_qwen2.5-1.5b"); series("r3", "series_qwen2.5-3b"); series("r7", "series_qwen2.5-7b")
series("md", "series_moondream"); series("vl", "series_qwen2.5vl-3b")
for r in ("r15", "r3", "r7"):
    e = "e" + r[1:]
    O[f"{e}_s"] = f"{raw['perc_s'] + raw[f'{r}_s']:.2f}"; O[f"{e}_j"] = f"{raw['perc_j'] + raw[f'{r}_j']:.1f}"
    O[f"{e}_s5"] = f"{raw['perc_s'] + raw[f'{r}_s5']:.2f}"; O[f"{e}_j5"] = f"{raw['perc_j'] + raw[f'{r}_j5']:.1f}"
    raw[f"{e}_s"] = raw["perc_s"] + raw[f"{r}_s"]; raw[f"{e}_j"] = raw["perc_j"] + raw[f"{r}_j"]
    raw[f"{e}_s5"] = raw["perc_s"] + raw[f"{r}_s5"]; raw[f"{e}_j5"] = raw["perc_j"] + raw[f"{r}_j5"]
O["ratio_s_vl_e3"] = f"{raw['vl_s'] / raw['e3_s']:.0f}"; O["ratio_j_vl_e3"] = f"{raw['vl_j'] / raw['e3_j']:.0f}"
O["ratio_s5_vl_e3"] = f"{raw['vl_s5'] / raw['e3_s5']:.1f}"; O["ratio_j5_vl_e3"] = f"{raw['vl_j5'] / raw['e3_j5']:.1f}"
O["session"] = open(D / "session.log", encoding="utf-8").readline().strip()
json.dump(O, open(HERE / "b10_e2e_numbers.json", "w", encoding="utf-8"), indent=1)
for k, v in O.items():
    print(f"{k:22s} {v}")
