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
                            10 frames; the server reuses the processed prefix of the
                            prompt within its slot; energy = mean VDD_IN over the run x
                            that mean total time
  detector pair             slope of the perceiver's wall time over 1, 11, 41 frames;
                            power over the frame loop of the 41-frame run; energy =
                            power x that time per frame
  median                    median of the per-question times (items.jsonl, turns.jsonl)
  free memory               MemAvailable (KiB) x 1024 / 10^9, in GB
  serialized system         detector pair + reader (sum of the two rows)
"""
import json, statistics, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
LV = Path(__file__).resolve().parents[2]  # repository root
D = LV / "exp_rev1/b10_boards/orin_nano_e2e"


def J(p):
    return json.load(open(D / p, encoding="utf-8"))


def JL(p):
    return [json.loads(l) for l in open(D / p, encoding="utf-8")]


def GB(kib):
    return kib * 1024 / 1e9


t = J("perception_timing.json")
r41 = t["runs"]["41"]
perc_s = t["per_frame_s_slope"]; perc_w = r41["loop"]["vdd_in_mean_mw"] / 1000; perc_j = perc_w * perc_s
O = {"perc_s": f"{perc_s:.2f}", "perc_w": f"{perc_w:.1f}", "perc_j": f"{perc_j:.1f}",
     "perc_loop_s": f"{r41['loop_s'] / 41:.3f}", "perc_fixed_s": f"{t['fixed_s']:.1f}",
     "idle_w": f"{t['idle']['vdd_in_mean_mw'] / 1000:.1f}",
     "perc_min_avail_gb": f"{GB(r41['loop']['min_avail_kb']):.2f}",
     "ser_ms": f"{J('serializer_onboard.json')['serializer_ms_per_item']:.2f}",
     "cores_min_avail_gb": f"{GB(J('coresident.json')['min_avail_kb']):.2f}"}
raw = {"perc_s": perc_s, "perc_j": perc_j}


def bench(tag, d, agree=True):
    s = J(f"{d}/summary.json")
    w = s["power_run_mw"]["VDD_IN"] / 1000; m = s["latency_mean_s"]
    med = statistics.median(r["latency_s"] for r in JL(f"{d}/items.jsonl"))
    O.update({f"{tag}_s": f"{m:.2f}", f"{tag}_med": f"{med:.2f}", f"{tag}_w": f"{w:.1f}", f"{tag}_j": f"{w * m:.1f}",
              f"{tag}_acc": f"{s['acc']:.2f}", f"{tag}_parse": f"{s['parse']:.2f}",
              f"{tag}_agree": f"{round(s['agree_laptop'] * s['n'])}/{s['n']}" if agree else "---"})
    raw[f"{tag}_s"] = m; raw[f"{tag}_j"] = w * m


def series(tag, d):
    s = J(f"{d}/summary.json")
    e = s["vdd_in_mean_mw"] / 1000 * s["per_frame_5q_mean_s"]
    tr = JL(f"{d}/turns.jsonl")
    first = statistics.median(r["latency_s"] for r in tr if r["turn"] == 1); later = statistics.median(r["latency_s"] for r in tr if r["turn"] > 1)
    O.update({f"{tag}_s5": f"{s['per_frame_5q_mean_s']:.2f}", f"{tag}_j5": f"{e:.1f}",
              f"{tag}_first": f"{first:.2f}", f"{tag}_later": f"{later:.2f}",
              f"{tag}_s5_min_avail_gb": f"{GB(s['min_avail_kb']):.2f}"})
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

# ---------------------------------------------------------------- sessions added on 2026-11-15
# (a) orin_nano_e2e_lowres: Qwen2.5-VL 3B on the timing set with the image reduced to 672 x 560,
#     and once more at the full resolution (check that the board gives the time of the first session).
# (b) orin_nano_fullbank: the whole confirmatory bank on the board (amendment A7). Accuracy and the
#     comparisons of that session are computed in rev2_analysis.py (key "onboard"); here only the
#     times of the arms that were run on 50 questions (VLM with image and serialized text).
import statistics as _st
D0 = D


def _other(dirname):
    global D
    D = LV / "exp_rev1/b10_boards" / dirname


_other("orin_nano_e2e_lowres")
if (D / "LOWRES_DONE").exists():
    bench("vlr", "qwen2.5vl-3b-lr", agree=False); bench("vl2", "qwen2.5vl-3b", agree=False)
    series("vlr", "series_qwen2.5vl-3b-lr"); series("vl2", "series_qwen2.5vl-3b")
    for tag, d in (("vlr", "qwen2.5vl-3b-lr"), ("vl2", "qwen2.5vl-3b")):
        it = [json.loads(l) for l in open(D / d / "items.jsonl", encoding="utf-8")]
        O[f"{tag}_correct50"] = f"{sum(r['correct'] for r in it)}/{len(it)}"
        O[f"{tag}_prompt_tokens"] = f"{_st.median(r['prompt_tokens'] for r in it):.0f}"
        O[f"{tag}_prompt_share"] = f"{100 * _st.median(r['prompt_ms'] / 1000 / r['latency_s'] for r in it):.0f}"
    # visual tokens at the reduced resolution: the prompts differ only in the image
    _full = {json.loads(l)["qa_id"]: json.loads(l)["prompt_tokens"] for l in open(D / "qwen2.5vl-3b/items.jsonl", encoding="utf-8")}
    _lr = {json.loads(l)["qa_id"]: json.loads(l)["prompt_tokens"] for l in open(D / "qwen2.5vl-3b-lr/items.jsonl", encoding="utf-8")}
    _d = {_full[k] - _lr[k] for k in _full}
    assert len(_d) == 1, _d
    O["vlr_visual_tokens"] = str(1628 - _d.pop())
    O["ratio_s_vlr_e3"] = f"{raw['vlr_s'] / raw['e3_s']:.1f}"; O["ratio_j_vlr_e3"] = f"{raw['vlr_j'] / raw['e3_j']:.1f}"
    assert abs(raw["vl2_s"] - raw["vl_s"]) < 0.05, (raw["vl2_s"], raw["vl_s"])     # "the board gives the same time in both sessions"
_other("orin_nano_fullbank")
if (D / "hyb-qwen2.5vl-3b/summary.json").exists():
    bench("hyb", "hyb-qwen2.5vl-3b", agree=False)
    O["ehyb_s"] = f"{raw['perc_s'] + raw['hyb_s']:.2f}"; O["ehyb_j"] = f"{raw['perc_j'] + raw['hyb_j']:.1f}"
if (D / "hyb-qwen2.5vl-3b-lr/summary.json").exists():
    bench("hyblr", "hyb-qwen2.5vl-3b-lr", agree=False)
    O["ehyblr_s"] = f"{raw['perc_s'] + raw['hyblr_s']:.2f}"; O["ehyblr_j"] = f"{raw['perc_j'] + raw['hyblr_j']:.1f}"
for tag, d in (("fr15", "full-qwen2.5-1.5b"), ("fr3", "full-qwen2.5-3b"), ("fr7", "full-qwen2.5-7b"), ("fvlr", "full-qwen2.5vl-3b-lr"), ("fvl", "full-qwen2.5vl-3b")):
    if (D / d / "summary.json").exists() and json.load(open(D / d / "summary.json", encoding="utf-8")).get("n") == 1328:
        if any(json.loads(l)["raw"] == "????????" for l in open(D / d / "items.jsonl", encoding="utf-8")):
            # amendments/A7_addendum2.md: part of this run is the output of a failed server process.
            # Time and energy come from rev2_analysis.py, which uses the answers of the repeat run
            # for the failed questions; without the repeat run the arm has no numbers.
            _a = json.load(open(HERE / "rev2_results.json", encoding="utf-8"))["onboard"]["arms"].get({"fvl": "vlm_full"}[tag], {})
            if "acc" not in _a:
                continue
            O.update({f"{tag}_s": f"{_a['time_mean_s']:.2f}", f"{tag}_med": f"{_a['time_median_s']:.2f}", f"{tag}_w": f"{_a['power_w']:.1f}",
                      f"{tag}_j": f"{_a['energy_j']:.1f}", f"{tag}_acc": f"{_a['acc']:.2f}", f"{tag}_parse": f"{_a['parse']:.2f}", f"{tag}_agree": "---"})
            raw[f"{tag}_s"] = _a["time_mean_s"]; raw[f"{tag}_j"] = _a["energy_j"]
            continue
        bench(tag, d, agree=False)
        if tag.startswith("fr"):                     # serialized system = detector pair (per frame) + reader, full bank
            e = "fe" + tag[2:]
            raw[f"{e}_s"] = raw["perc_s"] + raw[f"{tag}_s"]; raw[f"{e}_j"] = raw["perc_j"] + raw[f"{tag}_j"]
            O[f"{e}_s"] = f"{raw[f'{e}_s']:.2f}"; O[f"{e}_j"] = f"{raw[f'{e}_j']:.1f}"
_d = "full-hyb-qwen2.5vl-3b-lr"                     # A7 addendum 1: VLM with reduced image and serialized text, whole bank
if (D / _d / "summary.json").exists() and json.load(open(D / _d / "summary.json", encoding="utf-8")).get("n") == 1328:
    bench("fhyblr", _d, agree=False)
    raw["efhyblr_s"] = raw["perc_s"] + raw["fhyblr_s"]; raw["efhyblr_j"] = raw["perc_j"] + raw["fhyblr_j"]
    O["efhyblr_s"] = f"{raw['efhyblr_s']:.2f}"; O["efhyblr_j"] = f"{raw['efhyblr_j']:.1f}"
    O["ratio_s_efhyblr_fe3"] = f"{raw['efhyblr_s'] / raw['fe3_s']:.1f}"
for a, b in (("fvlr", "fe3"), ("fvl", "fe3")):
    if f"{a}_s" in raw and f"{b}_s" in raw:
        O[f"ratio_s_{a}_{b}"] = f"{raw[f'{a}_s'] / raw[f'{b}_s']:.1f}"; O[f"ratio_j_{a}_{b}"] = f"{raw[f'{a}_j'] / raw[f'{b}_j']:.1f}"
_other("orin_nano_e2e_mintok")                      # 2026-11-15: 980 x 840, the smallest size above 1024 image tokens
if (D / "MINTOK_DONE").exists():
    bench("mr", "qwen2.5vl-3b-mr", agree=False); series("mr", "series_qwen2.5vl-3b-mr")
    _mr = {json.loads(l)["qa_id"]: json.loads(l)["prompt_tokens"] for l in open(D / "qwen2.5vl-3b-mr/items.jsonl", encoding="utf-8")}
    _d = {_full[k] - _mr[k] for k in _full}
    assert len(_d) == 1, _d
    O["mr_visual_tokens"] = f"{1628 - _d.pop()}"
    O["mr_correct50"] = f"{sum(json.loads(l)['correct'] for l in open(D / 'qwen2.5vl-3b-mr/items.jsonl', encoding='utf-8'))}/50"
D = D0
json.dump(O, open(HERE / "b10_e2e_numbers.json", "w", encoding="utf-8"), indent=1)
for k, v in O.items():
    print(f"{k:22s} {v}")
