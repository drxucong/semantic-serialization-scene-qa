"""v15: decision-scoped serialization -- the one serializer lever never pulled.

The design contract allows encode(state, QUESTION TYPE); it forbids the encoder
from seeing the answer or the choices. Every version v9-v14 ignored the type and
emitted one stream for all five families. That left money on the table in one
specific place, and the v14 arm measured exactly how much:

  counting  v12 (no object rows) -.047 vs v9 at 7B;  v14 (with rows) -.013.
            The raw rows are worth ~+.034 on counting alone.
  cost      v14 pays for those rows on EVERY question: 3B drops from .7518
            (v12) to .7350, because the rows are pure retrieval load for the
            four families that never needed them.

v15 pays only where it earns: the object rows are emitted for COUNTING
questions and nowhere else. Everything else is v12 verbatim. Nothing here
depends on the queried class or the option set -- only on the question family,
which is known at deployment time and carries no answer information.

Prediction, written before the run: 7B ~ v12 + .008 ~ .803 (v9 .8031),
3B ~ v12 + .009 ~ .761 (v9 .6969). Criteria stay F1-F4, frozen 13:20Z.

New file; v9-v14 untouched.
Usage: python scripts/paper/run_serializer_v15.py --depth 5 --model qwen2.5:7b --out <dir>
"""
import argparse, json, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
for p in ("", "scripts/pilot", "scripts/coda", "scripts/paper"):
    sys.path.insert(0, str(ROOT / p) if p else str(ROOT))
from run_pilot_phase0 import forced_choices, parse_letter  # noqa: E402
import run_coda_text_v9 as V9  # noqa: E402
from run_serializer_v12 import serialize_v12  # noqa: E402
from run_serializer_v14 import object_list  # noqa: E402

SYSTEM = V9.SYSTEM
NEEDS_ROWS = {"counting"}          # frozen before any v15 run


def serialize_v15(st, category, depth=5):
    head = serialize_v12(st, depth)
    if category not in NEEDS_ROWS:
        return head
    body = object_list(st)
    return head + ("\n" + body if body else "")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--depth", type=int, default=5, choices=(1, 2, 3, 4, 5))
    ap.add_argument("--qa", default="outputs/coda/qa_coda.jsonl")
    ap.add_argument("--states", default="outputs/coda/states_kf_v9.json")
    ap.add_argument("--model", default="qwen2.5:7b")
    ap.add_argument("--base-url", default="http://localhost:11434/v1")
    ap.add_argument("--api-key", default="ollama")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    states = json.load(open(ROOT / args.states, encoding="utf-8"))
    items = [json.loads(l) for l in open(ROOT / args.qa, encoding="utf-8")]

    ln_c = sorted(len(serialize_v15(states[i["sample_id"]], "counting", args.depth))
                  for i in items if i["sample_id"] in states and i["category"] == "counting")
    ln_o = sorted(len(serialize_v15(states[i["sample_id"]], "direction", args.depth))
                  for i in items if i["sample_id"] in states and i["category"] != "counting")
    print(f"[v15] counting stream median {ln_c[len(ln_c)//2]}   "
          f"other families median {ln_o[len(ln_o)//2]}   (v9: 1842)", flush=True)

    from openai import OpenAI
    client = OpenAI(base_url=args.base_url, api_key=args.api_key)
    outdir = ROOT / args.out
    outdir.mkdir(parents=True, exist_ok=True)
    fp = outdir / "state_typed__clean__forced.jsonl"
    done = set()
    if fp.exists():
        done = {json.loads(l)["qa_id"] for l in open(fp, encoding="utf-8")}
        print(f"[v15] resume {len(done)}", flush=True)
    f = open(fp, "a", encoding="utf-8")
    t0 = time.time()
    for i, it in enumerate(items):
        if it["qa_id"] in done:
            continue
        fch, fans = forced_choices(it)
        if fans is None:
            continue
        scene = serialize_v15(states[it["sample_id"]], it["category"], args.depth)
        try:
            r = client.chat.completions.create(
                model=args.model, temperature=0, max_tokens=8, timeout=180,
                messages=[{"role": "system", "content": SYSTEM},
                          {"role": "user",
                           "content": V9.build_prompt(scene, it, fch)}])
            raw = r.choices[0].message.content or ""
        except Exception as e:  # noqa: BLE001
            raw = f"__ERROR__ {e}"
        pred = parse_letter(raw or "", set(fch))
        f.write(json.dumps({
            "qa_id": it["qa_id"], "sample_id": it["sample_id"],
            "scene_name": it["scene_name"], "category": it["category"],
            "arm": "v15_d5", "protocol": "clean", "track": "forced",
            "model": args.model, "pred": pred, "answer": fans,
            "correct": pred == fans, "abstained": False,
            "raw_head": (raw or "")[:40], "scene_chars": len(scene)}) + "\n")
        f.flush()
        if (i + 1) % 400 == 0:
            print(f"[v15|{args.model}] {i+1}/{len(items)} "
                  f"({(time.time()-t0)/60:.1f}min)", flush=True)
    f.close()
    print(f"[v15|{args.model}] done -> {fp}", flush=True)


if __name__ == "__main__":
    main()
