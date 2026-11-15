"""B4 (Access resubmission, R3): scene-graph textualizations of the SAME perceived
state (frozen confirmatory states, v9), read by the same readers under the same
prompt/decoding/parser as the serializer ladder. Two common embodied-planning
formats, neither aligned to the decision vocabulary:

  --mode sg_triples  one line per relation:  (robot, sees, Bollard#1); (Bollard#1,
                     distance_m, 7.8); (Bollard#1, bearing_deg, 36.2); (Bollard#1,
                     confidence, low)   -- ConceptGraphs / SayPlan-style text graph
  --mode sg_json     a JSON scene graph: {"nodes":[{"id":"Bollard#1","class":...,
                     "distance_m":7.8,"bearing_deg":36.2,"confidence":"low"},...],
                     "edges":[{"from":"robot","rel":"sees","to":"Bollard#1"},...]}

Both carry exactly the fields of the D1 (numeric) stream: class, numeric range,
numeric bearing, confidence tag; no bands, no side words, no per-family selection
lines. Resume-safe; output format identical to run_serializer_dladder.py.
"""
import argparse, json, sys, time
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
for p in ("scripts/paper", "scripts/pilot", "scripts/coda"):
    sys.path.insert(0, str(ROOT / p))
import run_serializer_dladder as DL  # noqa: E402
from run_pilot_phase0 import parse_letter  # noqa: E402
V9 = DL.V9


def sg_triples(st):
    out = []
    for g in st["agents"]:
        nid = f"{g['cls'].replace(' ', '_')}{g['id']}"
        out.append(f"(robot, sees, {nid})")
        out.append(f"({nid}, distance_m, {g['dist']:.1f})")
        out.append(f"({nid}, bearing_deg, {g['bearing']:.1f})")
        out.append(f"({nid}, confidence, {'low' if g.get('lowconf') else 'high'})")
    return "Scene graph:\n" + ("\n".join(out) if out else "(no objects)")


def sg_json(st):
    nodes, edges = [], []
    for g in st["agents"]:
        nid = f"{g['cls'].replace(' ', '_')}{g['id']}"
        nodes.append({"id": nid, "class": g["cls"], "distance_m": round(g["dist"], 1),
                      "bearing_deg": round(g["bearing"], 1), "confidence": "low" if g.get("lowconf") else "high"})
        edges.append({"from": "robot", "rel": "sees", "to": nid})
    return "Scene graph (JSON):\n" + json.dumps({"nodes": nodes, "edges": edges}, separators=(",", ":"))


SER = {"sg_triples": sg_triples, "sg_json": sg_json}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=list(SER), required=True)
    ap.add_argument("--qa", default="outputs/coda/qa_confirm.jsonl")
    ap.add_argument("--states", default="outputs/coda/states_confirm_v9.json")
    ap.add_argument("--model", default="qwen2.5:7b")
    ap.add_argument("--base-url", default="http://localhost:11434/v1")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    sp = ROOT / a.states
    if not sp.exists():
        sp = Path(__file__).resolve().parents[1] / "states/states_confirm_v9.json"   # release layout
    states = json.load(open(sp, encoding="utf-8"))
    items = [i for i in DL.load_bank(a.qa, "repo") if i["sample_id"] in states]
    from openai import OpenAI
    client = OpenAI(base_url=a.base_url, api_key="ollama")
    outdir = ROOT / a.out; outdir.mkdir(parents=True, exist_ok=True)
    fp = outdir / "state_typed__clean__forced.jsonl"
    done = {json.loads(l)["qa_id"] for l in open(fp, encoding="utf-8")} if fp.exists() else set()
    f = open(fp, "a", encoding="utf-8"); t0 = time.time()
    for i, it in enumerate(items):
        if it["qa_id"] in done:
            continue
        scene = SER[a.mode](states[it["sample_id"]])
        try:
            r = client.chat.completions.create(model=a.model, temperature=0, max_tokens=8, timeout=180,
                                               messages=[{"role": "system", "content": DL.SYSTEM},
                                                         {"role": "user", "content": V9.build_prompt(scene, it, it["choices"])}])
            raw = r.choices[0].message.content or ""
        except Exception as e:  # noqa: BLE001
            raw = f"__ERROR__ {e}"
        pred = parse_letter(raw or "", set(it["choices"]))
        f.write(json.dumps({"qa_id": it["qa_id"], "sample_id": it["sample_id"], "scene_name": it["scene_name"],
                            "category": it["category"], "family": it["family"], "arm": a.mode, "protocol": "clean",
                            "track": "forced", "model": a.model, "pred": pred, "answer": it["answer"],
                            "correct": pred == it["answer"], "abstained": False, "raw_head": (raw or "")[:40],
                            "scene_chars": len(scene)}) + "\n"); f.flush()
        if (i + 1) % 400 == 0:
            print(f"[{a.mode}|{a.model}] {i+1}/{len(items)} ({(time.time()-t0)/60:.1f} min)", flush=True)
    f.close()
    n = sum(1 for _ in open(fp, encoding="utf-8")); c = sum(json.loads(l)["correct"] for l in open(fp, encoding="utf-8"))
    print(f"[{a.mode}|{a.model}] {c}/{n} = {c/max(n,1):.4f} -> {fp}", flush=True)


if __name__ == "__main__":
    main()
