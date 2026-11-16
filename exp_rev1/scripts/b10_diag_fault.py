#!/usr/bin/env python3
"""B10 (Orin) diagnostic, 2026-11-16: the full-image run of Qwen2.5-VL 3B returns the string
"????????" from question 991 of the bank on, in two server processes with different histories.
This script starts a new server with the command line of b10_board_bench.py and asks the
questions whose bank positions are given, in the given order, and prints the raw outputs.
It measures nothing and writes only its log.
usage: python3 b10_diag_fault.py 990 991 989 990        (0-based positions in data/full_onboard.jsonl)
       python3 b10_diag_fault.py --no-start 990         (use a server that is already running)"""
import base64, json, os, signal, subprocess, sys, time, urllib.request
from pathlib import Path

HERE = Path.home() / "rev1"
SERVER = HERE / "llama.cpp-11fe021/build-cuda/bin/llama-server"
PORT = 8099
args = sys.argv[1:]
start = "--no-start" not in args
order = [int(a) for a in args if not a.startswith("--")]
items = [json.loads(l) for l in open(HERE / "data/full_onboard.jsonl", encoding="utf-8")]


def post(path, body, timeout=300):
    req = urllib.request.Request(f"http://127.0.0.1:{PORT}{path}", data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=timeout).read())


def healthy():
    try:
        return urllib.request.urlopen(f"http://127.0.0.1:{PORT}/health", timeout=2).status == 200
    except Exception:
        return False


def ask(it, text_only=False):
    if text_only:
        msgs = [{"role": "system", "content": it["px_system"]}, {"role": "user", "content": "Warm-up. Reply with the letter A."}]
    else:
        img = base64.b64encode((HERE / "data" / it["image"]).read_bytes()).decode()
        msgs = [{"role": "system", "content": it["px_system"]},
                {"role": "user", "content": [{"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img}"}}, {"type": "text", "text": it["px_user"]}]}]
    t0 = time.time()
    r = post("/v1/chat/completions", {"messages": msgs, "temperature": 0, "max_tokens": 8})
    return (r["choices"][0]["message"].get("content") or ""), time.time() - t0


proc = None
if start:
    cmd = [str(SERVER), "-m", str(HERE / "models/Qwen2.5-VL-3B-Instruct-Q4_K_M.gguf"), "-t", "6", "-c", "4096", "--port", str(PORT), "--host", "127.0.0.1",
           "--load-mode", "none", "-np", "1", "--cache-ram", "0", "--mmproj", str(HERE / "models/mmproj-Qwen2.5-VL-3B-Instruct-f16.gguf"), "-ngl", "99"]
    proc = subprocess.Popen(cmd, stdout=open(HERE / "diag_fault_server.log", "w"), stderr=subprocess.STDOUT, preexec_fn=os.setsid)
    t0 = time.time()
    while not healthy():
        if proc.poll() is not None or time.time() - t0 > 300:
            print("server did not start"); sys.exit(1)
        time.sleep(0.5)
    print(f"server started in {time.time() - t0:.0f} s", flush=True)
try:
    txt, dt = ask(items[0], text_only=True)
    print(f"text-only warm-up: {txt[:20]!r} ({dt:.1f} s)", flush=True)
    for i in order:
        txt, dt = ask(items[i])
        print(f"position {i} {items[i]['qa_id']}: {txt[:20]!r} ({dt:.1f} s) gold {items[i]['gold']}", flush=True)
    txt, dt = ask(items[0], text_only=True)
    print(f"text-only at the end: {txt[:20]!r} ({dt:.1f} s)", flush=True)
finally:
    if proc:
        try:
            os.killpg(os.getpgid(proc.pid), signal.SIGTERM); proc.wait(timeout=30)
        except Exception:
            pass
