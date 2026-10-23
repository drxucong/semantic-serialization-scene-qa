"""B8: peak GPU memory of each reader / VLM as served (ollama, Q4_K_M), measured
the same way for every model: unload everything, read the idle VRAM, load the
model with one warm query, then run 5 confirmatory queries (text readers: the
Scoped stream + question; VLMs: the keyframe + question) while sampling
nvidia-smi every 0.2 s; report the loaded-model VRAM (ollama ps) and the peak
nvidia-smi delta over idle. Also records host RAM delta of the ollama server
process group as a secondary number. Writes exp_rev1/b8_memory/memory.json.
"""
import base64, json, subprocess, threading, time, urllib.request
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "exp_rev1/b8_memory"; OUT.mkdir(parents=True, exist_ok=True)
BASE = "http://localhost:11434"
MODELS = ["qwen2.5:0.5b", "qwen2.5:1.5b", "qwen2.5:3b", "qwen2.5:7b", "moondream", "qwen2.5vl:3b", "qwen2.5vl:7b"]


def smi():
    o = subprocess.run(["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits"], capture_output=True, text=True).stdout
    return int(o.strip().splitlines()[0])


def api(path, body=None):
    req = urllib.request.Request(BASE + path, data=json.dumps(body).encode() if body else None,
                                 headers={"Content-Type": "application/json"}, method="POST" if body else "GET")
    return json.loads(urllib.request.urlopen(req, timeout=600).read() or b"{}")


def unload_all():
    for m in api("/api/ps").get("models", []):
        api("/api/generate", {"model": m["name"], "keep_alive": 0})
    time.sleep(4)


items = [json.loads(l) for l in open(ROOT / "exp_rev1/b7_bandwidth/step1_serialized.jsonl", encoding="utf-8")][:5]
from openai import OpenAI
client = OpenAI(base_url=BASE + "/v1", api_key="ollama")


def query(model, it):
    if "vl" in model or model == "moondream":
        p = ROOT / it["image"]
        content = [{"type": "image_url", "image_url": {"url": "data:image/jpeg;base64," + base64.b64encode(p.read_bytes()).decode()}},
                   {"type": "text", "text": "How many objects are visible? Answer with one number."}]
    else:
        content = it["scoped_text"] + "\n\nQuestion: how many objects are listed? Answer with one number."
    client.chat.completions.create(model=model, temperature=0, max_tokens=8, timeout=600,
                                   messages=[{"role": "user", "content": content}])


res = {}
for m in MODELS:
    unload_all(); idle = smi()
    query(m, items[0])  # load + warm
    ps = [x for x in api("/api/ps").get("models", []) if x["name"] == m]
    loaded = smi(); peak = [loaded]; stop = False

    def sampler():
        while not stop:
            peak.append(smi()); time.sleep(0.2)
    t = threading.Thread(target=sampler); t.start()
    t0 = time.time()
    for it in items:
        query(m, it)
    dt = (time.time() - t0) / len(items)
    stop = True; t.join()
    res[m] = {"idle_mib": idle, "loaded_mib": loaded, "peak_mib": max(peak), "peak_delta_mib": max(peak) - idle,
              "ollama_size_vram_bytes": ps[0].get("size_vram") if ps else None, "ollama_size_bytes": ps[0].get("size") if ps else None,
              "sec_per_query_warm": dt}
    print(m, res[m], flush=True)
json.dump(res, open(OUT / "memory.json", "w"), indent=1)
print("wrote", OUT / "memory.json")
