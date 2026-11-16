#!/usr/bin/env python3
"""B10 (Orin), 2026-11-16 (amendments/A7_addendum3.md): the image arm of b10_board_bench.py
with the reload rule of the paper (Section VI; scripts/pilot/run_pixel_robust.py on the laptop).

Why. With the full image, one question of the confirmatory bank (position 991,
coda_3_12072_counting) makes this llama-server build return the string "????????", and the
server then returns that string for every later request, text-only requests included, until
it is started again (b10_diag_fault.py). The 337 questions after it in the first run failed
for that reason and not for their own content.

Rule. An output is degenerate if, stripped, it has at least four characters and at most two
distinct ones. After a degenerate output the server is stopped and started again and the
question is asked once more. If the output is degenerate again, the question is recorded as
failed (it counts as wrong) and the server is started again before the next question.

Same server command, prompts, images, decoding and warm-up as b10_board_bench.py. Each item
records its attempts and its own time window; power is averaged over the windows of the
recorded attempts only, so that the loading of the server does not enter it. Items are
written as they are answered.
usage: python3 b10_board_bench_guard.py --name N --probe data/X.jsonl --out-root out_e2e_full1328
"""
import argparse, base64, bisect, json, os, re, shutil, signal, subprocess, threading, time
from b10_board_bench import HERE, SERVER, PORT, post, healthy, parse_letter


def degenerate(txt):
    s = (txt or "").strip()
    return len(s) >= 4 and len(set(s)) <= 2


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--name", required=True); ap.add_argument("--probe", required=True)
    ap.add_argument("--out-root", default="out_e2e_full1328"); ap.add_argument("--laptop-key", default="qwen2.5vl-3b")
    ap.add_argument("--model", default="models/Qwen2.5-VL-3B-Instruct-Q4_K_M.gguf")
    ap.add_argument("--mmproj", default="models/mmproj-Qwen2.5-VL-3B-Instruct-f16.gguf")
    ap.add_argument("--threads", type=int, default=6); ap.add_argument("--ngl", type=int, default=99)
    ap.add_argument("--ctx", type=int, default=4096); ap.add_argument("--load-timeout", type=int, default=600)
    ap.add_argument("--max-restarts", type=int, default=40)
    a = ap.parse_args()
    out = HERE / a.out_root / a.name; out.mkdir(parents=True, exist_ok=True)
    items = [json.loads(l) for l in open(HERE / a.probe, encoding="utf-8")]
    cmd = [str(SERVER), "-m", str(HERE / a.model), "-t", str(a.threads), "-c", str(a.ctx), "--port", str(PORT), "--host", "127.0.0.1",
           "--load-mode", "none", "-np", "1", "--cache-ram", "0", "--mmproj", str(HERE / a.mmproj), "-ngl", str(a.ngl)]
    avail0 = int(re.search(r"MemAvailable:\s+(\d+)", open("/proc/meminfo").read()).group(1))
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
    state = {"proc": None, "loads": []}

    def start_server():
        logf = open(out / "server.log", "a")
        logf.write(f"\n===== server start {time.strftime('%H:%M:%S')} =====\n"); logf.flush()
        t0 = time.time()
        state["proc"] = subprocess.Popen(cmd, stdout=logf, stderr=subprocess.STDOUT, preexec_fn=os.setsid)
        while not healthy():
            if state["proc"].poll() is not None:
                raise RuntimeError(f"server exited during load (rc={state['proc'].returncode})")
            if time.time() - t0 > a.load_timeout:
                raise RuntimeError("load timeout")
            time.sleep(0.5)
        state["loads"].append(round(time.time() - t0, 1))

    def stop_server():
        try:
            os.killpg(os.getpgid(state["proc"].pid), signal.SIGTERM); state["proc"].wait(timeout=30)
        except Exception:
            pass
        t0 = time.time()
        while healthy() and time.time() - t0 < 20:
            time.sleep(0.5)

    def ask(it, user=None, image=None):
        img = base64.b64encode((HERE / "data" / (image or it["image"])).read_bytes()).decode()
        msgs = [{"role": "system", "content": it["px_system"]},
                {"role": "user", "content": [{"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img}"}},
                                             {"type": "text", "text": user or it["px_user"]}]}]
        t0 = time.time()
        r = post("/v1/chat/completions", {"messages": msgs, "temperature": 0, "max_tokens": 8})
        t1 = time.time()
        return (r["choices"][0]["message"].get("content") or ""), t0, t1, r.get("usage", {}), r.get("timings", {})

    def warm_up():
        # as in b10_board_bench.py: the shared system prompt, an unrelated user turn, and the image of the
        # first item, which the first run answered in a healthy server (never the image of a neighbouring item)
        for _ in range(2):
            txt = ask(items[0], user="Warm-up. Reply with the letter A.", image=WARM_IMAGE)[0]
        return txt

    WARM_IMAGE = json.loads(open(HERE / "data/full_onboard.jsonl", encoding="utf-8").readline())["image"]
    res = {"name": a.name, "model": a.model, "mmproj": a.mmproj, "threads": a.threads, "server": str(SERVER), "mem_max": "none",
           "mem_available_before_kb": avail0, "rule": "restart after a degenerate output, ask once more"}
    rows, restarts = [], 0
    fitems = open(out / "items.jsonl", "w")
    try:
        start_server()
        w = warm_up()
        assert not degenerate(w), f"degenerate output in the warm-up: {w!r}"
        res["t_measure_start"] = time.time()
        for it in items:
            txt, t0, t1, usage, timings = ask(it)
            attempts, first_raw = 1, txt[:20]
            if degenerate(txt):
                print(f"[{a.name}] degenerate output {txt[:12]!r} at {it['qa_id']}: server restarted, question asked once more", flush=True)
                stop_server(); start_server(); restarts += 1
                w = warm_up()
                assert not degenerate(w), f"degenerate output in the warm-up after a restart: {w!r}"
                txt, t0, t1, usage, timings = ask(it); attempts = 2
                if degenerate(txt):
                    print(f"[{a.name}] degenerate again at {it['qa_id']}: recorded as failed, server restarted", flush=True)
                    stop_server(); start_server(); restarts += 1
                    w = warm_up()
                    assert not degenerate(w), f"degenerate output in the warm-up after a restart: {w!r}"
                if restarts > a.max_restarts:
                    raise RuntimeError("too many restarts")
            pred = parse_letter(txt, set(it["choices"]))
            lap = it["laptop_pred"].get(a.laptop_key)
            row = {"qa_id": it["qa_id"], "family": it["family"], "raw": txt[:20], "pred": pred, "correct": pred == it["gold"],
                   "laptop_pred": lap, "agree_laptop": pred == lap, "latency_s": round(t1 - t0, 3), "prompt_tokens": usage.get("prompt_tokens"),
                   "prompt_ms": timings.get("prompt_ms"), "predicted_ms": timings.get("predicted_ms"),
                   "attempts": attempts, "first_raw": first_raw, "degenerate": degenerate(txt), "t0": round(t0, 2), "t1": round(t1, 2)}
            rows.append(row); fitems.write(json.dumps(row) + "\n"); fitems.flush()
            print(f"[{a.name}] {len(rows)}/{len(items)} {t1 - t0:.2f}s pred={pred}", flush=True)
    except Exception as e:  # noqa: BLE001
        res["run_error"] = repr(e)[:300]
    res["t_measure_end"] = time.time()
    fitems.close()
    if power["proc"]:
        try:
            os.killpg(os.getpgid(power["proc"].pid), signal.SIGTERM)
        except Exception:
            pass
        S = power["samples"]; ts = [t for t, _ in S]

        def mean_rails(rs):
            keys = sorted({k for r in rs for k in r})
            return {k: round(sum(r.get(k, 0) for r in rs) / len(rs)) for k in keys} if rs else {}
        run = []
        for r in rows:
            run += [S[i][1] for i in range(bisect.bisect_left(ts, r["t0"]), bisect.bisect_right(ts, r["t1"]))]
        res["power_idle_mw"] = mean_rails([r for t, r in S if t <= t_idle_end]); res["power_run_mw"] = mean_rails(run)
        res["power_samples"] = {"idle": sum(t <= t_idle_end for t in ts), "run": len(run)}
        with open(out / "power.jsonl", "w") as f:
            for t, r in S:
                f.write(json.dumps({"t": round(t, 2), **r}) + "\n")
    stop_server()
    try:
        res["nvpmodel"] = subprocess.run(["nvpmodel", "-q"], capture_output=True, text=True, timeout=10).stdout.strip()[:200]
    except Exception:
        pass
    res["restarts"] = restarts; res["load_s"] = state["loads"]
    if rows:
        lat = sorted(r["latency_s"] for r in rows)
        res.update({"n": len(rows), "acc": sum(r["correct"] for r in rows) / len(rows), "parse": sum(r["pred"] is not None for r in rows) / len(rows),
                    "agree_laptop": sum(r["agree_laptop"] for r in rows) / len(rows), "n_degenerate": sum(r["degenerate"] for r in rows),
                    "n_asked_twice": sum(r["attempts"] == 2 for r in rows),
                    "latency_median_s": lat[len(lat) // 2], "latency_p95_s": lat[int(0.95 * len(lat)) - 1], "latency_mean_s": sum(lat) / len(lat)})
    json.dump(res, open(out / "summary.json", "w"), indent=1)
    print(json.dumps(res), flush=True)


if __name__ == "__main__":
    main()
