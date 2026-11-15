"""v14 = v12's corrected compiled fields + v9's raw per-object list.

WHY THIS ARM EXISTS, AND WHY IT WAS NEVER RUN UNTIL NOW.
Every version from v10 on optimised two things at once: compile the right
quantities, AND compress the stream. That framing hid the cheapest experiment
in the whole series -- stop compressing, keep only the compilation fix.

The measurements that motivate it:
  * A2, the clean deletion: removing v9's object list is -.0249* at 7B and
    +.0293 at 3B. The list is what the big reader uses and what drowns the
    small one. It is raw evidence, not a computed field.
  * v12 (corrected rules, no list) is .7950 at 7B / .7518 at 3B, against v9's
    .8031 / .6969.
  * The compiled verdict is structurally weaker than the reader on selective
    families: it must pick a top-1 over a median of 8 classes and may not see
    the choices, so when it is wrong it names a class that is not even on the
    ballot 96.5% (path) / 97.6% (nearest_class) of the time. Compiler .665/.644
    vs v9 reader .9265/.9331 on the same states.
  * Emitting a RANKING instead of a verdict was checked and is already
    saturated: its ceiling is .8640 / .9079, and v12's readers already score
    .9118 / .9079. So that repair is not worth an arm, and is not in here.

So v14 gives the reader both: the corrected compiled fields it could not derive
cheaply, and the raw rows it demonstrably uses to adjudicate. It gives up
compression entirely -- median ~1950 chars against v9's 1842 -- which is the
honest cost, and is acceptable at this stage because the on-board budget is
explicitly out of scope until distillation.

Composition, chosen so nothing is stated twice or two ways:
  v12's block  (counts as totals, corridor arg-min + runner-up, cross-class
                arg-min + runner-up, per-class band + IMAGE-COLUMN sector)
  + v9's       "Visible objects (nearest first):" rows, verbatim
  - v9's own summary lines, which v12's versions strictly supersede (v9's
    direction word is the bearing sector, which is the wrong function).

Prediction, written before the run: 7B .7950 + .0249 ~ .820 (v9 .8031),
3B .7518 - .0293 ~ .723 (v9 .6969). Criteria stay F1-F4, frozen 13:20Z.

New file; v9 / v12 / v13 untouched.
Usage: python scripts/paper/run_serializer_v14.py --depth 5 --model qwen2.5:7b --out <dir>
"""
import argparse, json, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
for p in ("", "scripts/pilot", "scripts/coda", "scripts/paper"):
    sys.path.insert(0, str(ROOT / p) if p else str(ROOT))
from run_pilot_phase0 import forced_choices, parse_letter  # noqa: E402
import run_coda_text_v9 as V9  # noqa: E402
from run_serializer_v12 import serialize_v12  # noqa: E402

SYSTEM = V9.SYSTEM


def object_list(st):
    """v9's raw rows, verbatim, without v9's summary lines above them"""
    keep, on = [], False
    for l in V9.typed_text(st).split("\n"):
        s = l.strip()
        if s.startswith("Visible objects"):
            on = True
            keep.append(l)
            continue
        if on and s.startswith("#"):
            keep.append(l)
    return "\n".join(keep)


def serialize_v14(st, depth=5):
    head = serialize_v12(st, depth)
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
    render = lambda st: serialize_v14(st, args.depth)  # noqa: E731
    ln = sorted(len(render(st)) for st in states.values())
    v9ln = sorted(len(V9.typed_text(st)) for st in states.values())
    print(f"[v14] stream chars median {ln[len(ln)//2]} P95 {ln[int(.95*len(ln))]}"
          f"   (v9: {v9ln[len(v9ln)//2]} / {v9ln[int(.95*len(v9ln))]})", flush=True)
    if ln[len(ln) // 2] < 1200:
        print("[v14] ABORT: the object list did not make it into the stream "
              "-- refusing to burn an arm on a mislabelled v12.", flush=True)
        return 2

    from openai import OpenAI
    client = OpenAI(base_url=args.base_url, api_key=args.api_key)
    items = [json.loads(l) for l in open(ROOT / args.qa, encoding="utf-8")]
    outdir = ROOT / args.out
    outdir.mkdir(parents=True, exist_ok=True)
    fp = outdir / "state_typed__clean__forced.jsonl"
    done = set()
    if fp.exists():
        done = {json.loads(l)["qa_id"] for l in open(fp, encoding="utf-8")}
        print(f"[v14] resume {len(done)}", flush=True)
    f = open(fp, "a", encoding="utf-8")
    tag = f"v14_d{args.depth}"
    t0 = time.time()
    for i, it in enumerate(items):
        if it["qa_id"] in done:
            continue
        fch, fans = forced_choices(it)
        if fans is None:
            continue
        scene = render(states[it["sample_id"]])
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
            "arm": tag, "protocol": "clean", "track": "forced",
            "model": args.model, "pred": pred, "answer": fans,
            "correct": pred == fans, "abstained": False,
            "raw_head": (raw or "")[:40], "scene_chars": len(scene)}) + "\n")
        f.flush()
        if (i + 1) % 400 == 0:
            print(f"[{tag}|{args.model}] {i+1}/{len(items)} "
                  f"({(time.time()-t0)/60:.1f}min)", flush=True)
    f.close()
    print(f"[{tag}|{args.model}] done -> {fp}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
