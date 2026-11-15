#!/usr/bin/env python3
"""B10 (Orin) end to end, part 2: several questions on one frame.

For each of 10 frames, five questions (one per family) are asked in a row of the
same frame, with llama-server's default prompt cache on. The first question of a
frame pays for whatever is new (for a VLM: encoding the image; for the reader: the
frame's serialized state); later questions reuse the cached prefix where the prompt
allows it. Records per-turn wall time and the server's own timings, mean board
power (tegrastats VDD_IN) over the run, and the lowest MemAvailable.

usage: b10_series.py --name NAME --model models/X.gguf [--mmproj models/Y.gguf]
                     [--pixel] [--ollama-moondream] [--ngl 99]
Workload: ~/rev1/data/series_onboard.jsonl (built by b10_orin_perceive.py prompts).
"""
import argparse, base64, json, os, re, signal, subprocess, sys, threading, time, urllib.request
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import b10_board_bench as BB  # post(), healthy(), PORT

HERE = Path.home() / "rev1"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--name", required=True); ap.add_argument("--model", required=True)
    ap.add_argument("--mmproj"); ap.add_argument("--pixel", action="store_true")
    ap.add_argument("--ollama-moondream", action="store_true")
    ap.add_argument("--ngl", type=int, default=99); ap.add_argument("--threads", type=int, default=6)
    ap.add_argument("--ctx", type=int, default=4096)
    a = ap.parse_args()
    out = HERE / os.environ.get("B10_E2E_OUT", "out_e2e") / f"series_{a.name}"; out.mkdir(parents=True, exist_ok=True)
    frames = [json.loads(l) for l in open(HERE / "data/series_onboard.jsonl", encoding="utf-8")]
    avail0 = int(re.search(r"MemAvailable:\s+(\d+)", open("/proc/meminfo").read()).group(1))
    cmd = [str(BB.SERVER), "-m", str(HERE / a.model), "-t", str(a.threads), "-c", str(a.ctx), "--port", str(BB.PORT),
           "--host", "127.0.0.1", "--load-mode", "none", "-np", "1", "--cache-ram", "0", "-ngl", str(a.ngl)]
    if a.mmproj:
        cmd += ["--mmproj", str(HERE / a.mmproj)]
    power, minav, stop = [], {"kb": avail0}, {"v": False}
    tg = subprocess.Popen(["tegrastats", "--interval", "100"], stdout=subprocess.PIPE, text=True, preexec_fn=os.setsid)

    def pw():
        for line in tg.stdout:
            m = re.search(r"VDD_IN (\d+)mW", line)
            if m:
                power.append((time.time(), int(m.group(1))))

    def mem():
        while not stop["v"]:
            minav["kb"] = min(minav["kb"], int(re.search(r"MemAvailable:\s+(\d+)", open("/proc/meminfo").read()).group(1)))
            time.sleep(0.1)
    threading.Thread(target=pw, daemon=True).start(); threading.Thread(target=mem, daemon=True).start()
    log = open(out / "server.log", "w")
    proc = subprocess.Popen(cmd, stdout=log, stderr=subprocess.STDOUT, preexec_fn=os.setsid)
    t0 = time.time()
    while not BB.healthy():
        if proc.poll() is not None or time.time() - t0 > 600:
            raise SystemExit("server failed to load")
        time.sleep(0.5)
    marker = "<__media__>"
    if a.pixel:
        marker = json.loads(urllib.request.urlopen(f"http://127.0.0.1:{BB.PORT}/props", timeout=10).read()).get("media_marker", marker)

    def ask(fr, q, img):
        if a.pixel and a.ollama_moondream:
            body = {"prompt": {"prompt_string": " Question: " + marker + q["px_user"] + "\n\n Answer: ", "multimodal_data": [img]},
                    "temperature": 0, "n_predict": 8, "stop": ["<|endoftext|>", "Question:"]}
            t = time.time(); r = BB.post("/completion", body); dt = time.time() - t
            return dt, r.get("timings", {}), r.get("tokens_evaluated")
        if a.pixel:
            msgs = [{"role": "system", "content": fr["px_system"]},
                    {"role": "user", "content": [{"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img}"}},
                                                 {"type": "text", "text": q["px_user"]}]}]
        else:
            msgs = [{"role": "system", "content": fr["text_system"]}, {"role": "user", "content": q["text_user"]}]
        t = time.time(); r = BB.post("/v1/chat/completions", {"messages": msgs, "temperature": 0, "max_tokens": 8}); dt = time.time() - t
        return dt, r.get("timings", {}), r.get("usage", {}).get("prompt_tokens")

    # warm-up on the LAST frame (never adjacent to a reuse of its image or state)
    wimg = base64.b64encode((HERE / "data" / frames[-1]["image"]).read_bytes()).decode() if a.pixel else None
    ask(frames[-1], frames[-1]["questions"][0], wimg)
    rows, tm0 = [], time.time()
    for fi, fr in enumerate(frames):
        img = base64.b64encode((HERE / "data" / fr["image"]).read_bytes()).decode() if a.pixel else None
        for qi, q in enumerate(fr["questions"]):
            dt, tim, ptok = ask(fr, q, img)
            rows.append({"frame": fi, "turn": qi + 1, "family": q["family"], "latency_s": round(dt, 3), "prompt_tokens": ptok,
                         "prompt_ms": tim.get("prompt_ms"), "prompt_n": tim.get("prompt_n"), "cache_n": tim.get("cache_n"),
                         "predicted_ms": tim.get("predicted_ms")})
            print(f"[{a.name}] frame {fi + 1}/{len(frames)} turn {qi + 1}: {dt:.2f}s", flush=True)
    tm1 = time.time(); stop["v"] = True
    for p in (proc, tg):
        try:
            os.killpg(os.getpgid(p.pid), signal.SIGTERM)
        except Exception:
            pass
    med = lambda v: sorted(v)[len(v) // 2]
    first = [r["latency_s"] for r in rows if r["turn"] == 1]; later = [r["latency_s"] for r in rows if r["turn"] > 1]
    pw_run = [w for t, w in power if tm0 <= t <= tm1]
    res = {"name": a.name, "model": a.model, "mmproj": a.mmproj, "frames": len(frames), "questions_per_frame": 5,
           "first_turn_median_s": med(first), "first_turn_mean_s": sum(first) / len(first),
           "later_turn_median_s": med(later), "later_turn_mean_s": sum(later) / len(later),
           "per_frame_5q_mean_s": sum(r["latency_s"] for r in rows) / len(frames),
           "vdd_in_mean_mw": round(sum(pw_run) / len(pw_run)) if pw_run else None,
           "mem_available_before_kb": avail0, "min_avail_kb": minav["kb"], "window_s": tm1 - tm0}
    json.dump(res, open(out / "summary.json", "w"), indent=1)
    with open(out / "turns.jsonl", "w") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")
    print(json.dumps(res), flush=True)


if __name__ == "__main__":
    main()
