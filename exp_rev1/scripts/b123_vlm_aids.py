"""B1-B3 (Access resubmission): strengthen the zero-shot pixel baseline on
the confirmatory bank, keeping everything else identical to the shipped
pixel arm (scripts/pilot/run_pilot_pixel_ollama.py: same SYSTEM prompt, same
option formatting, T=0, 8 output tokens, same parse_letter, same ollama
model tags, same PNG bytes).

  --mode stereo    B1: cam0 AND cam1 keyframes as two images (sensor parity)
  --mode taskinfo  B2: cam0 + the decision vocabulary and scope in the prompt
                       (band boundaries 5/15 m, sector rule +-15 deg, 40 m
                       field-of-view scope, one-line family description)
  --mode hybrid    B3: cam0 + the shipped Scoped serialized state as text
  --mode pixel     control: re-run of the shipped pixel arm (same-machine
                       pairing check; expected within +-0.0015 of the archived run)

Serialized text for 'hybrid' is read from exp_rev1/b7_bandwidth/
step1_serialized.jsonl (regenerated with the frozen serializer path).
Resume-safe by qa_id. Declared in exp_rev1/B123_PREREG.md before any run.
"""
import argparse, base64, json, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "scripts/pilot"))
from run_pilot_phase0 import forced_choices, parse_letter  # noqa: E402
from run_pilot_pixel_ollama import SYSTEM, build_prompt  # noqa: E402

TASKINFO = (
    "Scope and vocabulary used by the questions:\n"
    "- Only objects inside the camera's field of view and within 40 m count.\n"
    "- Distance bands: 'under 5 meters' (< 5 m), '5 to 15 meters', 'over 15 meters'.\n"
    "- Sides: 'left' if the object's bearing is more than 15 degrees left of the optical axis, "
    "'right' if more than 15 degrees right, otherwise 'center'.\n"
    "- Question families: counting (how many of a type), direction (which side the nearest of a "
    "type is on), nearest-class (which type is nearest), nearest-distance (band of the nearest "
    "of a type), path-object (which type is closest to the robot's forward path).")

FAMILY_HINT = {
    "counting": "This is a counting question.",
    "direction": "This is a direction (left/center/right) question.",
    "nearest_class": "This is a nearest-class question.",
    "nearest_dist": "This is a nearest-distance (band) question.",
    "path_object": "This is a path-object question.",
}


def b64(p):
    return base64.b64encode(Path(p).read_bytes()).decode()


def call(client, model, content, max_tokens=8):
    t0 = time.time()
    try:
        r = client.chat.completions.create(model=model, temperature=0, max_tokens=max_tokens, timeout=300,
                                           messages=[{"role": "system", "content": SYSTEM},
                                                     {"role": "user", "content": content}])
        return r.choices[0].message.content or "", time.time() - t0
    except Exception as e:  # noqa: BLE001
        return f"__ERROR__ {e}", time.time() - t0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=("pixel", "stereo", "taskinfo", "hybrid"), required=True)
    ap.add_argument("--model", required=True)
    ap.add_argument("--qa", default="outputs/coda/qa_confirm.jsonl")
    ap.add_argument("--serialized", default="exp_rev1/b7_bandwidth/step1_serialized.jsonl")
    ap.add_argument("--base-url", default="http://localhost:11434/v1")
    ap.add_argument("--out", required=True)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--reload-each", action="store_true",
                    help="unload the model after every query (serving-state fault workaround: "
                         "qwen2.5vl:3b on 1600x900 nuScenes frames degenerates to '8888' from the "
                         "second query after a load; a fresh load answers correctly)")
    a = ap.parse_args()

    from openai import OpenAI
    client = OpenAI(base_url=a.base_url, api_key="ollama")
    items = [json.loads(l) for l in open(ROOT / a.qa, encoding="utf-8")]
    if a.limit:
        items = items[:a.limit]
    ser = {}
    if a.mode == "hybrid":
        ser = {json.loads(l)["qa_id"]: json.loads(l)["scoped_text"] for l in open(ROOT / a.serialized, encoding="utf-8")}
    outdir = ROOT / a.out; outdir.mkdir(parents=True, exist_ok=True)
    fp = outdir / f"{a.mode}__clean__forced.jsonl"
    done = {json.loads(l)["qa_id"] for l in open(fp)} if fp.exists() else set()
    f = open(fp, "a")
    cache = {}
    import urllib.request
    consec_null = 0

    def unload_model():
        """Degenerate-output guard (the paper's reload-on-degenerate instrument):
        unload the model so ollama reloads it fresh, then retry the item."""
        try:
            req = urllib.request.Request(a.base_url.replace("/v1", "") + "/api/generate",
                                         data=json.dumps({"model": a.model, "keep_alive": 0}).encode(),
                                         headers={"Content-Type": "application/json"})
            urllib.request.urlopen(req, timeout=60).read()
        except Exception as e:  # noqa: BLE001
            print(f"[guard] unload failed: {e}", flush=True)
        time.sleep(8)

    for it in items:
        if it["qa_id"] in done:
            continue
        fch, fans = forced_choices(it)
        if fans is None:
            continue
        sid = it["sample_id"]
        p0 = ROOT / it["cam_front"]
        if sid not in cache:
            cache[sid] = {"cam0": b64(p0)}
            if a.mode == "stereo":
                cache[sid]["cam1"] = b64(str(p0).replace("cam0", "cam1"))
        prompt = build_prompt(it, fch)
        content = [{"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{cache[sid]['cam0']}"}}]
        if a.mode == "stereo":
            content.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{cache[sid]['cam1']}"}})
            prompt = "The two images are the left and right cameras of a stereo pair taken at the same instant.\n" + prompt
        elif a.mode == "taskinfo":
            prompt = TASKINFO + "\n" + FAMILY_HINT[it["category"]] + "\n\n" + prompt
        elif a.mode == "hybrid":
            prompt = ("A perception system produced the following description of the same image; it may "
                      "contain errors.\n" + ser[it["qa_id"]] + "\n\n" + prompt)
        content.append({"type": "text", "text": prompt})
        raw, dt = call(client, a.model, content)
        # server down: wait for it instead of logging error records (max ~2 h)
        waited = 0
        while raw.startswith("__ERROR__") and ("Connection" in raw or "connect" in raw.lower()) and waited < 7200:
            if waited == 0:
                print(f"[guard] ollama unreachable ({raw[:60]!r}); waiting", flush=True)
            time.sleep(30); waited += 30
            raw, dt = call(client, a.model, content)
        pred = parse_letter(raw or "", set(fch))
        if a.reload_each:
            if pred is None:           # even a fresh load failed: one more try, then record
                unload_model(); raw, dt = call(client, a.model, content); pred = parse_letter(raw or "", set(fch))
            unload_model()
        if pred is None:
            consec_null += 1
            if consec_null >= 4:          # 4 unparsed in a row = serving fault, not format non-compliance
                print(f"[guard] {consec_null} consecutive unparsed (last raw={raw[:20]!r}); reloading model", flush=True)
                unload_model()
                raw, dt = call(client, a.model, content)
                pred = parse_letter(raw or "", set(fch))
                consec_null = 0 if pred is not None else consec_null
        else:
            consec_null = 0
        rec = {"qa_id": it["qa_id"], "sample_id": sid, "scene_name": it["scene_name"], "category": it["category"],
               "arm": a.mode, "protocol": "clean", "track": "forced", "model": a.model, "pred": pred,
               "answer": fans, "correct": pred == fans, "raw_head": (raw or "")[:60], "latency_s": round(dt, 2)}
        f.write(json.dumps(rec) + "\n"); f.flush()
    f.close()
    n = sum(1 for _ in open(fp)); c = sum(json.loads(l)["correct"] for l in open(fp))
    print(f"[{a.mode}|{a.model}] {c}/{n} = {c/max(n,1):.4f} -> {fp}", flush=True)


if __name__ == "__main__":
    main()
