#!/usr/bin/env python3
"""B10 on-board benchmark (stdlib only; runs on the board).

For one model configuration: start llama-server (the board's existing build,
read-only) inside a user systemd scope with a hard MemoryMax so an overrun kills
only this process; wait for /health; 3 warm-up queries; then every probe item
once (T=0, max_tokens 8, exact shipped prompts); record per-query wall time,
the answer, parse, and peak server RSS (sampled every 0.1 s from /proc). A load
that fails or is OOM-killed is recorded as such -- that is a result.

usage: b10_board_bench.py --name qwen2.5-1.5b --model models/qwen2.5-1.5b-q4km.gguf
       [--mmproj models/x.gguf --pixel] [--mem-max 1600M] [--threads 4] [--limit N]
"""
import argparse, base64, json, os, re, shutil, signal, subprocess, threading, time, urllib.request
from pathlib import Path

HERE = Path.home() / "rev1"
SERVER = Path(os.environ.get("B10_SERVER", str(Path.home() / "src/llama.cpp/build/bin/llama-server")))
PORT = 8099


def post(path, body, timeout=900):
    req = urllib.request.Request(f"http://127.0.0.1:{PORT}{path}", data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=timeout).read())


def healthy():
    try:
        return json.loads(urllib.request.urlopen(f"http://127.0.0.1:{PORT}/health", timeout=2).read()).get("status") == "ok"
    except Exception:
        return False


def server_pid():
    o = subprocess.run(["pgrep", "-f", f"llama-server.*--port {PORT}"], capture_output=True, text=True).stdout.split()
    return int(o[0]) if o else None


def rss_kb(pid):
    try:
        for l in open(f"/proc/{pid}/status"):
            if l.startswith("VmRSS:"):
                return int(l.split()[1])
    except Exception:
        return None


def parse_letter(text, valid):
    m = re.search(r"\b([A-D])\b", text or "")
    return m.group(1) if m and m.group(1) in valid else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--name", required=True); ap.add_argument("--model", required=True)
    ap.add_argument("--mmproj"); ap.add_argument("--pixel", action="store_true")
    ap.add_argument("--mem-max", default="1600M"); ap.add_argument("--threads", type=int, default=4)
    ap.add_argument("--ctx", type=int, default=4096); ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--load-timeout", type=int, default=600)
    ap.add_argument("--cpus", default="", help="taskset CPU list, e.g. 2,3 for the A76 pair")
    # Orin additions (2026-10-23): GPU offload, an explicit key for the laptop answers,
    # system-wide memory (CUDA allocations on Jetson are not in the server's RSS) and
    # board power from tegrastats (VDD_IN etc.), sampled during the measured queries.
    ap.add_argument("--ngl", type=int, default=0, help="layers offloaded to the GPU (-ngl)")
    ap.add_argument("--laptop-key", default="", help="probe50 laptop_pred key to compare with")
    # moondream: the paper's runs went through ollama, whose moondream template is
    # '{{ if .Prompt }} Question: {{ .Prompt }}\n\n{{ end }} Answer: {{ .Response }}'
    # (no system prompt; the image is prefixed to the user content) with stop strings
    # <|endoftext|> and 'Question:'. llama-server's chat endpoint applies a different
    # format and moondream answered with an immediate end-of-text, so this mode sends
    # the ollama-rendered prompt to the raw /completion endpoint instead.
    ap.add_argument("--ollama-moondream", action="store_true")
    a = ap.parse_args()
    out = HERE / "out" / a.name; out.mkdir(parents=True, exist_ok=True)
    items = [json.loads(l) for l in open(HERE / "data/probe50.jsonl", encoding="utf-8")]
    if a.limit:
        items = items[: a.limit]
    meminfo = open("/proc/meminfo").read()
    avail0 = int(re.search(r"MemAvailable:\s+(\d+)", meminfo).group(1))
    scope = ["systemd-run", "--scope", "--quiet"] if os.geteuid() == 0 else ["systemd-run", "--user", "--scope", "--quiet"]
    pin = ["taskset", "-c", a.cpus] if a.cpus else []
    # --mem-max none: no systemd scope (Jetson: GPU allocations are not charged to the
    # cgroup, so a cap would not bound them; and a user scope needs the user manager)
    wrap = [] if a.mem_max == "none" else scope + ["-p", f"MemoryMax={a.mem_max}", "-p", "MemorySwapMax=0"]
    cmd = wrap + pin + [
           str(SERVER), "-m", str(HERE / a.model), "-t", str(a.threads), "-c", str(a.ctx), "--port", str(PORT),
           "--host", "127.0.0.1", "--load-mode", "none", "-np", "1",
           # host-RAM prompt cache (default 8192 MiB) stores every past prompt and made
           # RSS grow per question until the memory cap killed the 1.5B runs; disable it.
           # In-slot prefix reuse (the shared system prompt) is unaffected.
           "--cache-ram", "0"]
    if a.mmproj:
        cmd += ["--mmproj", str(HERE / a.mmproj)]
    if a.ngl:
        cmd += ["-ngl", str(a.ngl)]
    # tegrastats (Jetson only): idle power for 5 s before the server starts, then
    # timestamped samples until the run ends
    power = {"samples": [], "proc": None}
    tegra = shutil.which("tegrastats")

    def power_reader(p):
        for line in p.stdout:
            rails = {k: int(v) for k, v in re.findall(r"(VDD_[A-Z0-9_]+|VIN_[A-Z0-9_]+) (\d+)mW", line)}
            if rails:
                power["samples"].append((time.time(), rails))
    if tegra:
        power["proc"] = subprocess.Popen([tegra, "--interval", "100"], stdout=subprocess.PIPE, text=True, preexec_fn=os.setsid)
        threading.Thread(target=power_reader, args=(power["proc"],), daemon=True).start()
        time.sleep(5)
    t_idle_end = time.time()
    log = open(out / "server.log", "w")
    t_load0 = time.time()
    proc = subprocess.Popen(cmd, stdout=log, stderr=subprocess.STDOUT, preexec_fn=os.setsid)
    peak = {"kb": 0, "min_avail_kb": avail0}; stop = {"v": False}

    def sampler():
        while not stop["v"]:
            pid = server_pid()
            if pid:
                r = rss_kb(pid)
                if r: peak["kb"] = max(peak["kb"], r)
            m = re.search(r"MemAvailable:\s+(\d+)", open("/proc/meminfo").read())
            if m: peak["min_avail_kb"] = min(peak["min_avail_kb"], int(m.group(1)))
            time.sleep(0.1)
    th = threading.Thread(target=sampler, daemon=True); th.start()
    status = "ok"
    while not healthy():
        if proc.poll() is not None:
            status = f"server exited during load (rc={proc.returncode})"; break
        if time.time() - t_load0 > a.load_timeout:
            status = "load timeout"; break
        time.sleep(0.5)
    load_s = time.time() - t_load0
    res = {"name": a.name, "model": a.model, "mmproj": a.mmproj, "threads": a.threads, "cpus": a.cpus, "server": str(SERVER), "mem_max": a.mem_max,
           "mem_available_before_kb": avail0, "load_status": status, "load_s": round(load_s, 1)}
    rows = []
    if status == "ok":
        # this llama-server build draws a random media marker per process; read it
        marker = "<__media__>"
        if a.ollama_moondream:
            marker = json.loads(urllib.request.urlopen(f"http://127.0.0.1:{PORT}/props", timeout=10).read())["media_marker"]

        def ask(it):
            if a.pixel and a.ollama_moondream:
                img = base64.b64encode((HERE / "data" / it["image"]).read_bytes()).decode()
                body = {"prompt": {"prompt_string": " Question: " + marker + it["px_user"] + "\n\n Answer: ",
                                   "multimodal_data": [img]},
                        "temperature": 0, "n_predict": 8, "stop": ["<|endoftext|>", "Question:"]}
                t0 = time.time()
                r = post("/completion", body)
                dt = time.time() - t0
                return (r.get("content") or ""), dt, {"prompt_tokens": r.get("tokens_evaluated")}, r.get("timings", {})
            if a.pixel:
                img = base64.b64encode((HERE / "data" / it["image"]).read_bytes()).decode()
                msgs = [{"role": "system", "content": it["px_system"]},
                        {"role": "user", "content": [{"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img}"}},
                                                     {"type": "text", "text": it["px_user"]}]}]
            else:
                msgs = [{"role": "system", "content": it["text_system"]}, {"role": "user", "content": it["text_user"]}]
            t0 = time.time()
            r = post("/v1/chat/completions", {"messages": msgs, "temperature": 0, "max_tokens": 8})
            dt = time.time() - t0
            return (r["choices"][0]["message"].get("content") or ""), dt, r.get("usage", {}), r.get("timings", {})
        try:
            # Warm-up must not share a prompt with any measured item: llama-server
            # caches the longest matching prefix, so re-asking a warm-up item
            # returns in ~0.4 s instead of ~20 s (seen in the first run, set aside
            # as invalid_cachehit_*). Warm up with the system prompt + an unrelated
            # user turn; only the shared system-prompt prefix can be reused, which
            # is the realistic deployment case (same instructions, new state).
            warm = dict(items[0]); warm["text_user"] = "Warm-up. Reply with the letter A."
            warm["px_user"] = "Warm-up. Reply with the letter A."
            # pixel runs: the image follows the system prompt, so warming up on item 1's
            # image let item 1 reuse the encoded image (0.5 s instead of 10 s on the Orin);
            # warm up on the last item's image, which is never adjacent to a reuse
            warm["image"] = items[-1]["image"]
            for _ in range(2):
                ask(warm)
            res["t_measure_start"] = time.time()
            for it in items:
                txt, dt, usage, timings = ask(it)
                pred = parse_letter(txt, set(it["choices"]))
                lap = it["laptop_pred"].get(a.laptop_key or ("moondream" if a.pixel else a.name))
                rows.append({"qa_id": it["qa_id"], "family": it["family"], "raw": txt[:20], "pred": pred,
                             "correct": pred == it["gold"], "laptop_pred": lap, "agree_laptop": pred == lap,
                             "latency_s": round(dt, 3), "prompt_tokens": usage.get("prompt_tokens"),
                             "prompt_ms": timings.get("prompt_ms"), "predicted_ms": timings.get("predicted_ms")})
                print(f"[{a.name}] {len(rows)}/{len(items)} {dt:.2f}s pred={pred}", flush=True)
        except Exception as e:  # noqa: BLE001
            res["run_error"] = repr(e)[:300]
        res["t_measure_end"] = time.time()
    stop["v"] = True; th.join(timeout=2)
    if power["proc"]:
        try:
            os.killpg(os.getpgid(power["proc"].pid), signal.SIGTERM)
        except Exception:
            pass
        S = power["samples"]
        idle = [r for t, r in S if t <= t_idle_end]
        run = [r for t, r in S if res.get("t_measure_start", 1e18) <= t <= res.get("t_measure_end", 0)]
        def mean_rails(rows):
            keys = sorted({k for r in rows for k in r})
            return {k: round(sum(r.get(k, 0) for r in rows) / len(rows)) for k in keys} if rows else {}
        res["power_idle_mw"] = mean_rails(idle); res["power_run_mw"] = mean_rails(run)
        res["power_samples"] = {"idle": len(idle), "run": len(run)}
        with open(out / "power.jsonl", "w") as f:
            for t, r in S:
                f.write(json.dumps({"t": round(t, 2), **r}) + "\n")
    res["peak_sys_used_mb"] = round((avail0 - peak["min_avail_kb"]) / 1024, 1)  # MiB, MemAvailable drop
    try:
        res["nvpmodel"] = subprocess.run(["nvpmodel", "-q"], capture_output=True, text=True, timeout=10).stdout.strip()[:200]
    except Exception:
        pass
    try:
        os.killpg(os.getpgid(proc.pid), signal.SIGTERM); proc.wait(timeout=30)
    except Exception:
        pass
    jl = subprocess.run(["journalctl", "-k", "-n", "40", "--no-pager"] if os.geteuid() == 0 else ["journalctl", "--user", "-n", "40", "--no-pager"], capture_output=True, text=True).stdout
    res["oom_in_journal"] = bool(re.search(r"oom|Out of memory|memory\.max", jl, re.I))
    res["peak_rss_mb"] = round(peak["kb"] / 1024, 1)
    if rows:
        lat = sorted(r["latency_s"] for r in rows)
        res.update({"n": len(rows), "acc": sum(r["correct"] for r in rows) / len(rows),
                    "parse": sum(r["pred"] is not None for r in rows) / len(rows),
                    "agree_laptop": sum(r["agree_laptop"] for r in rows) / len(rows),
                    "latency_median_s": lat[len(lat) // 2], "latency_p95_s": lat[int(0.95 * len(lat)) - 1],
                    "latency_mean_s": sum(lat) / len(lat)})
    json.dump(res, open(out / "summary.json", "w"), indent=1)
    with open(out / "items.jsonl", "w") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")
    print(json.dumps(res), flush=True)


if __name__ == "__main__":
    main()
