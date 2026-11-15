#!/usr/bin/env python3
"""B10 (Orin) end to end, part 1: the one-pass detector pair on the board.

Runs the UNCHANGED perceiver (scripts/coda/perceive_list.py with --no-unidepth
--no-auxdet --no-stereo, i.e. the 'light1' configuration of Section VIII-D: the two
fine-tuned YOLO11 detectors, one full-frame pass each, ground-plane and class-height
ranging) from a mirror of the lvcworld layout under ~/rev1/e2e, on the Orin GPU,
through the PyTorch already installed for another project (~/dv019, used read-only;
ultralytics is installed separately under ~/rev1/pylib).

Stages (stdlib only; this file is the driver, not the perceiver):
  timing  wall time of the perceiver on N = 1, 11, 41 frames of one fold; per-frame
          time = slope over N (the method of Table 14 on the laptop). tegrastats
          power and MemAvailable are sampled throughout; the frame-loop window is
          cut from the perceiver's own progress lines.
  probe   perceive the 50 probe frames (two folds) -> states for the reader runs.
  prompts build the reader prompts on the board from those states with the shipped
          serializer (stdlib-only modules), plus a same-frame series workload.
usage: python3 b10_orin_perceive.py timing|probe|prompts|coresident
"""
import json, os, re, signal, subprocess, sys, threading, time
from pathlib import Path

HOME = Path.home()
E = HOME / "rev1/e2e"                      # mirror of the lvcworld tree
OUT = HOME / "rev1" / os.environ.get("B10_E2E_OUT", "out_e2e"); OUT.mkdir(parents=True, exist_ok=True)
PY = str(HOME / "dv019/venv/bin/python")   # torch 2.8.0 + torchvision 0.23.0 (CUDA), read-only
LIBS = HOME / "dv019/libs"
ENV = {**os.environ,
       "PYTHONPATH": str(HOME / "rev1/pylib"),
       "LD_LIBRARY_PATH": ":".join([str(LIBS / "libcudss-linux-aarch64-0.7.1.4_cuda12-archive/lib"),
                                    str(LIBS / "libcusparse_lt-linux-aarch64-0.8.1.1_cuda12-archive/lib"),
                                    os.environ.get("LD_LIBRARY_PATH", "")]),
       "YOLO_CONFIG_DIR": str(HOME / "rev1/ultra_cfg"), "PYTHONUTF8": "1", "PYTHONUNBUFFERED": "1"}
LIGHT1 = ["--no-unidepth", "--no-auxdet", "--no-stereo"]


def avail_kb():
    return int(re.search(r"MemAvailable:\s+(\d+)", open("/proc/meminfo").read()).group(1))


class Sampler:
    """tegrastats rails (100 ms) and MemAvailable (100 ms), timestamped."""
    def __init__(self):
        self.power, self.mem, self.stop = [], [], False
        self.p = subprocess.Popen(["tegrastats", "--interval", "100"], stdout=subprocess.PIPE, text=True, preexec_fn=os.setsid)
        threading.Thread(target=self._pw, daemon=True).start()
        threading.Thread(target=self._mem, daemon=True).start()

    def _pw(self):
        for line in self.p.stdout:
            r = {k: int(v) for k, v in re.findall(r"(VDD_[A-Z0-9_]+) (\d+)mW", line)}
            if r:
                self.power.append((time.time(), r))

    def _mem(self):
        while not self.stop:
            self.mem.append((time.time(), avail_kb())); time.sleep(0.1)

    def close(self):
        self.stop = True
        try:
            os.killpg(os.getpgid(self.p.pid), signal.SIGTERM)
        except Exception:
            pass

    def window(self, t0, t1):
        pw = [r["VDD_IN"] for t, r in self.power if t0 <= t <= t1]
        mm = [m for t, m in self.mem if t0 <= t <= t1]
        return {"vdd_in_mean_mw": round(sum(pw) / len(pw)) if pw else None, "power_samples": len(pw),
                "min_avail_kb": min(mm) if mm else None}


def perceive(name, sids_rel, limit):
    """Run the unchanged perceiver; return wall time, frame-loop window and log lines."""
    out_rel = f"outputs/coda/{name}.json"
    for p in (E / "outputs/coda/kfold").glob(f"{name}_f*.json"):
        p.unlink()                                   # the perceiver caches per-fold parts; never reuse
    cmd = [PY, str(E / "scripts/coda/perceive_list.py"), *LIGHT1, "--sids", sids_rel, "--tag", name, "--out", out_rel]
    if limit:
        cmd += ["--limit", str(limit)]
    lines, t0 = [], time.time()
    pr = subprocess.Popen(cmd, cwd=E, env=ENV, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    for line in pr.stdout:
        lines.append((time.time(), line.rstrip()))
    rc = pr.wait(); t1 = time.time()
    if rc != 0:
        print("\n".join(l for _, l in lines[-25:])); raise SystemExit(f"perceiver failed rc={rc}")
    starts = [t for t, l in lines if re.match(r"\[fold\d\] 0/", l)]
    ends = [t for t, l in lines if re.match(r"fold \d done", l)]
    return {"wall_s": t1 - t0, "t0": t0, "t1": t1, "loop_start": starts[0] if starts else None,
            "loop_end": ends[-1] if ends else None, "n_folds": len(starts),
            "tail": [l for _, l in lines[-4:]], "states": str(E / out_rel)}


def stage_timing():
    S = Sampler(); time.sleep(5); idle_end = time.time()
    res = {"avail0_kb": avail_kb(), "runs": {}}
    idle = S.window(idle_end - 5, idle_end)
    for n in (1, 11, 41):
        r = perceive(f"t_light1_{n}", "outputs/coda/sids_fold3_41.txt", n)
        if r["loop_start"] and r["loop_end"]:
            r["loop"] = S.window(r["loop_start"], r["loop_end"]); r["loop_s"] = r["loop_end"] - r["loop_start"]
        r["whole"] = S.window(r["t0"], r["t1"])
        res["runs"][n] = r
        print(f"N={n}: wall {r['wall_s']:.1f} s, frame loop {r.get('loop_s', float('nan')):.2f} s", flush=True)
    S.close()
    xs = [1, 11, 41]; ys = [res["runs"][n]["wall_s"] for n in xs]
    mx, my = sum(xs) / 3, sum(ys) / 3
    slope = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sum((x - mx) ** 2 for x in xs)
    res.update(per_frame_s_slope=slope, fixed_s=my - slope * mx, idle=idle,
               per_frame_s_loop41=res["runs"][41].get("loop_s", 0) / 41,
               per_frame_s_loop_diff=(res["runs"][41].get("loop_s", 0) - res["runs"][11].get("loop_s", 0)) / 30)
    json.dump(res, open(OUT / "perception_timing.json", "w"), indent=1)
    with open(OUT / "perception_power.jsonl", "w") as f:
        for t, r in S.power:
            f.write(json.dumps({"t": round(t, 2), **r}) + "\n")
    print(json.dumps({k: res[k] for k in ("per_frame_s_slope", "fixed_s", "per_frame_s_loop41", "per_frame_s_loop_diff", "idle")}), flush=True)
    print("loop power/mem N=41:", res["runs"][41].get("loop"), flush=True)


def stage_probe():
    r = perceive("states_probe_light1_orin", "outputs/coda/sids_probe50.txt", 0)
    d = json.load(open(r["states"]))
    json.dump({"n_frames": len(d), "wall_s": r["wall_s"], "tail": r["tail"]}, open(OUT / "probe_perception.json", "w"), indent=1)
    print("probe states:", len(d), "frames;", r["tail"][-2:], flush=True)


def stage_coresident():
    """Memory with the reader's server already loaded (started by the caller): run 11 frames."""
    S = Sampler(); time.sleep(2); a0 = avail_kb()
    r = perceive("t_light1_cores", "outputs/coda/sids_fold3_41.txt", 11)
    w = S.window(r["t0"], r["t1"]); S.close()
    json.dump({"avail_before_kb": a0, **w, "wall_s": r["wall_s"]}, open(OUT / "coresident.json", "w"), indent=1)
    print("co-resident:", a0, w, flush=True)


def stage_prompts():
    """Reader prompts from the board's own states, with the shipped serializer (stdlib only)."""
    for p in ("scripts/paper", "scripts/pilot", "scripts/coda", "."):
        sys.path.insert(0, str(E / p))
    os.chdir(E)
    import run_serializer_dladder as DL
    states = json.load(open(E / "outputs/coda/states_probe_light1_orin.json"))
    bank = {it["qa_id"]: it for it in DL.load_bank("outputs/coda/qa_confirm.jsonl", "repo")}
    probe = [json.loads(l) for l in open(HOME / "rev1/data/probe50.jsonl", encoding="utf-8")]
    lap = json.load(open(HOME / "rev1/data/laptop_light1_preds.json"))
    t0 = time.perf_counter(); n = 0
    with open(HOME / "rev1/data/probe50_onboard.jsonl", "w", encoding="utf-8") as fo:
        for pr in probe:
            it = bank[pr["qa_id"]]
            scene = DL.serialize_dl(states[it["sample_id"]], it["category"], "d0"); n += 1
            fo.write(json.dumps({**{k: pr[k] for k in ("qa_id", "family", "gold", "choices", "image", "px_system", "px_user")},
                                 "text_system": DL.SYSTEM, "text_user": DL.V9.build_prompt(scene, it, it["choices"]),
                                 "laptop_pred": {k: v.get(pr["qa_id"]) for k, v in lap.items()}}) + "\n")
    ser_ms = (time.perf_counter() - t0) / n * 1e3
    # same-frame series: for each of the first 10 probe frames of sequence 0, five questions,
    # one per family, each with that frame's state scoped to the family (timing workload only)
    fams = ["counting", "nearest_dist", "direction", "path_object", "nearest_class"]
    byfam = {f: [p for p in probe if p["family"] == f] for f in fams}
    frames = [p for p in probe if p["qa_id"].split("_")[1] == "0"][:10]
    with open(HOME / "rev1/data/series_onboard.jsonl", "w", encoding="utf-8") as fo:
        for i, fr in enumerate(frames):
            sid = bank[fr["qa_id"]]["sample_id"]
            qs = []
            for f in fams:
                q = bank[byfam[f][i % len(byfam[f])]["qa_id"]]
                scene = DL.serialize_dl(states[sid], f, "d0")
                qs.append({"family": f, "text_user": DL.V9.build_prompt(scene, q, q["choices"]),
                           "px_user": byfam[f][i % len(byfam[f])]["px_user"]})
            fo.write(json.dumps({"sample_id": sid, "image": fr["image"], "text_system": DL.SYSTEM,
                                 "px_system": fr["px_system"], "questions": qs}) + "\n")
    json.dump({"serializer_ms_per_item": ser_ms, "n": n}, open(OUT / "serializer_onboard.json", "w"))
    print(f"prompts written; serializer {ser_ms:.3f} ms/item on the board", flush=True)


if __name__ == "__main__":
    {"timing": stage_timing, "probe": stage_probe, "prompts": stage_prompts, "coresident": stage_coresident}[sys.argv[1]]()
