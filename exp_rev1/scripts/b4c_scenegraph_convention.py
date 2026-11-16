"""B4c (added 2026-11-15 after a simulated review): the object-list scene graphs of
b4_scenegraph.py with the sign convention of the bearing stated.

b4_scenegraph.py writes the bearing of every object as a signed number of degrees and says
nowhere that positive means left. In the direction family the readers then score below the
reader that is given no scene. This control prepends two sentences to the same graph:

  NOTE: bearing_deg is positive for an object to the left of the camera axis and negative for
  an object to the right. An object is on the left side if its bearing is above 15, on the
  right side if it is below -15, and in the center otherwise.

The second sentence is the rule that the VLM receives in the arm with the answer vocabulary
(b123_vlm_aids.py --mode taskinfo). Everything else is b4_scenegraph.py: same states, same
system prompt, same question format, temperature 0, 8 output tokens, same parser.

  --mode sgc_triples | sgc_json
Resume-safe by qa_id.
"""
import argparse, json, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
for p in ("scripts/paper", "scripts/pilot", "scripts/coda", "scripts/rev1"):
    sys.path.insert(0, str(ROOT / p))
import run_serializer_dladder as DL  # noqa: E402
from run_pilot_phase0 import parse_letter  # noqa: E402
import b4_scenegraph as B4  # noqa: E402
V9 = DL.V9

NOTE = ("NOTE: bearing_deg is positive for an object to the left of the camera axis and negative for an "
        "object to the right. An object is on the left side if its bearing is above 15, on the right side "
        "if it is below -15, and in the center otherwise.\n")
SER = {"sgc_triples": lambda st: NOTE + B4.sg_triples(st), "sgc_json": lambda st: NOTE + B4.sg_json(st)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=list(SER), required=True)
    ap.add_argument("--qa", default="outputs/coda/qa_confirm.jsonl")
    ap.add_argument("--states", default="outputs/coda/states_confirm_v9.json")
    ap.add_argument("--model", default="qwen2.5:7b")
    ap.add_argument("--base-url", default="http://localhost:11434/v1")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    states = json.load(open(ROOT / a.states, encoding="utf-8"))
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
