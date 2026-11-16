#!/usr/bin/env python3
"""B10 (Orin), 2026-11-16: diagnostic, not a measurement of the paper's tables.

Question (raised by three internal reviews of the final manuscript): did the vision encoder of
the VLM run on the GPU of the board? The paper so far cites the help text of the server
("--mmproj-offload ... default: enabled"). This script answers from the device itself:

  1. default      : the server command of b10_board_bench.py, with log verbosity raised (-lv 4)
                    so that the server prints which backend the vision encoder uses and how long
                    the encoding of an image takes;
  2. no-offload   : the same command with --no-mmproj-offload (vision encoder on the CPU).

For each setting: one warm-up request and N questions of data/full_onboard.jsonl (the first N,
which the first full-image run answered in a healthy server), image at full size, at 980 x 840
(data/images_mr is made for the 50 timing frames only, so the reduced copies are made here in
memory) and at 672 x 560. Wall time per request and the server's own timings are recorded.
Nothing of this enters a comparison; the answers are not scored.

usage: python3 b10_diag_encoder.py [--n 3]     (writes out_e2e_full1328/diag_encoder/)
"""
import argparse, base64, io, json, os, signal, subprocess, time
from pathlib import Path
from PIL import Image
from b10_board_bench import HERE, SERVER, PORT, post, healthy

SIZES = {"full": None, "mr": (980, 840), "lr": (672, 560)}


def png_b64(path, size):
    if size is None:
        return base64.b64encode(Path(path).read_bytes()).decode()
    im = Image.open(path).convert("RGB").resize(size, Image.BICUBIC)
    buf = io.BytesIO(); im.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=3)
    ap.add_argument("--model", default="models/Qwen2.5-VL-3B-Instruct-Q4_K_M.gguf")
    ap.add_argument("--mmproj", default="models/mmproj-Qwen2.5-VL-3B-Instruct-f16.gguf")
    a = ap.parse_args()
    out = HERE / "out_e2e_full1328" / "diag_encoder"; out.mkdir(parents=True, exist_ok=True)
    items = [json.loads(l) for l in open(HERE / "data/full_onboard.jsonl", encoding="utf-8")][: a.n]
    base = [str(SERVER), "-m", str(HERE / a.model), "-t", "6", "-c", "4096", "--port", str(PORT), "--host", "127.0.0.1",
            "--load-mode", "none", "-np", "1", "--cache-ram", "0", "--mmproj", str(HERE / a.mmproj), "-ngl", "99", "-lv", "4"]
    res = {}
    for setting, extra in (("default", []), ("no-offload", ["--no-mmproj-offload"])):
        assert not healthy(), "a server is already running on the port; this diagnostic must run alone"
        logf = open(out / f"server_{setting}.log", "w")
        proc = subprocess.Popen(base + extra, stdout=logf, stderr=subprocess.STDOUT, preexec_fn=os.setsid)
        t0 = time.time()
        while not healthy():
            if proc.poll() is not None or time.time() - t0 > 600:
                raise SystemExit(f"server failed to load ({setting})")
            time.sleep(0.5)
        rows = []
        try:
            for size_name, size in SIZES.items():
                for k, it in enumerate([items[0]] + items):          # the first request of each size is a warm-up
                    img = png_b64(HERE / "data" / it["image"], size)
                    msgs = [{"role": "system", "content": it["px_system"]},
                            {"role": "user", "content": [{"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img}"}},
                                                         {"type": "text", "text": it["px_user"] if k else "Warm-up. Reply with the letter A."}]}]
                    t1 = time.time()
                    r = post("/v1/chat/completions", {"messages": msgs, "temperature": 0, "max_tokens": 8})
                    t2 = time.time()
                    row = {"setting": setting, "size": size_name, "warm_up": k == 0, "qa_id": it["qa_id"], "wall_s": round(t2 - t1, 3),
                           "raw": (r["choices"][0]["message"].get("content") or "")[:20], "prompt_tokens": r.get("usage", {}).get("prompt_tokens"),
                           "prompt_ms": r.get("timings", {}).get("prompt_ms"), "predicted_ms": r.get("timings", {}).get("predicted_ms")}
                    rows.append(row); print(json.dumps(row), flush=True)
        finally:
            try:
                os.killpg(os.getpgid(proc.pid), signal.SIGTERM); proc.wait(timeout=30)
            except Exception:
                pass
            t3 = time.time()
            while healthy() and time.time() - t3 < 20:
                time.sleep(0.5)
            logf.close()
        res[setting] = rows
    json.dump(res, open(out / "diag_encoder.json", "w"), indent=1)
    for setting, rows in res.items():
        for size_name in SIZES:
            w = [r["wall_s"] for r in rows if r["size"] == size_name and not r["warm_up"]]
            print(f"{setting:11s} {size_name:5s} mean wall {sum(w) / len(w):.2f} s over {len(w)} questions", flush=True)


if __name__ == "__main__":
    main()
