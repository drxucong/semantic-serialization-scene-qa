"""v12: the serializer finally computes the functions the questions ask about.

WHY. Reading the gold definitions out of scripts/coda/make_coda_qa.py showed
that three of the five emitted fields are DIFFERENT FUNCTIONS from the ones the
benchmark scores, and have been since v1. Measured offline against gold on the
same perceived states the readers see (analysis/v12_rule_fix.py):

  direction    gold sectors the IMAGE COLUMN u (u<1224/3 left, <2*1224/3 center,
               else right). The serializer sectored the BEARING at +-15 deg.
               field accuracy .5534 -> .7605   (+.2071)
  counting     gold counts every visible object of the class; GT has no
               confidence notion at all. The serializer headlined the CONFIDENT
               count and demoted uncertain detections to a "+N?" footnote.
               field accuracy .2651 -> .4631   (+.1980)
               closest-option ceiling .5000 -> .5805
  path_object  gold takes the corridor {x > 1, |y| <= 2} and the nearest object
               in it. The serializer scored lateral + dist/10, a soft blend.
               field accuracy .6250 -> .6728   (+.0478)

Corridor width was checked for sensitivity, not tuned: |y|<=2 (gold's own
value) .6728, |y|<=1.5 .6324, |y|<=3 .6066. A recall-corrected count was also
probed and is WORSE on closest-option (.5403), besides being fitted on this
bank; it is not used.

nearest_class and nearest_dist already match gold; their .644 / .778 is pure
perception error and no rule change can touch it.

Everything else is v11b: both arg-mins ship their runner-up (the appeal
evidence, confirmed at 3B by M1 +.0762* and M2 +.0685*), the confidence split
survives (P0 says it is the reader's one field), renderings stay on v9's single
lines. Bearing wording now uses the bank's own option strings ("in the center",
not "center side") -- vocabulary alignment as a correctness matter.

New file; v10 / v11 / v11b / v9 are all untouched.
Usage: python scripts/paper/run_serializer_v12.py --depth 5 --model qwen2.5:7b --out <dir>
"""
import argparse, collections, json, math, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
for p in ("", "scripts/pilot", "scripts/coda", "scripts/paper"):
    sys.path.insert(0, str(ROOT / p) if p else str(ROOT))
from run_pilot_phase0 import forced_choices, parse_letter  # noqa: E402
import run_coda_text_v9 as V9  # noqa: E402

SYSTEM = V9.SYSTEM
EPS = 0.5                       # the serializer's own frozen boundary tolerance
IMG_W = 1224.0                  # CODa cam0 width, same constant the bank uses


def xy(g):
    r = math.radians(g["bearing"])
    return g["dist"] * math.cos(r), g["dist"] * math.sin(r)


def sector(g):
    """gold's own rule: sector the image column, in the bank's own wording"""
    u = g.get("u")
    if u is None:                                   # fall back to bearing
        b = g["bearing"]
        return ("on the left side" if b > 15 else
                "in the center" if b >= -15 else "on the right side")
    return ("on the left side" if u < IMG_W / 3 else
            "in the center" if u < 2 * IMG_W / 3 else "on the right side")


def in_corridor(g):
    x, y = xy(g)
    return x > 1.0 and abs(y) <= 2.0


def nearest_by_cls(ags):
    n = {}
    for g in ags:
        n.setdefault(g["cls"], g)
    return n


def top2(cands, keyfn):
    order, seen = [], set()
    for a in sorted(cands, key=keyfn):
        if a["cls"] not in seen:
            seen.add(a["cls"])
            order.append(a)
    if not order:
        return None, None, False
    if len(order) == 1:
        return order[0]["cls"], None, False
    return order[0]["cls"], order[1]["cls"], (keyfn(order[1]) - keyfn(order[0])) < EPS


def line(prefix, cands, keyfn, nextword):
    a, b, close = top2(cands, keyfn)
    if a is None:
        return None
    s = f"{prefix}: {a}"
    if b:
        s += f" (next {nextword}: {b}" + ("; too close to call)" if close else ")")
    return s


def counts_line(ags):
    tot = collections.Counter(g["cls"] for g in ags)
    unc = collections.Counter(g["cls"] for g in ags if g.get("lowconf"))
    parts = []
    for k in sorted(tot):
        parts.append(f"{k}={tot[k]}" + (f" ({unc[k]} uncertain)" if unc.get(k) else ""))
    return "Counts by type: " + (", ".join(parts) or "none")


def serialize_v12(st, depth=5):
    ags = st["agents"]
    near = nearest_by_cls(ags)
    lines = []

    if depth >= 1 and ags:                       # S1 corridor arg-min
        corr = [g for g in ags if in_corridor(g)]
        if corr:
            lines.append(line("Closest to the robot's forward path",
                              corr, lambda g: g["dist"], "closest"))
        else:
            lines.append("Closest to the robot's forward path: "
                         "nothing in the forward corridor")
    if depth >= 2 and near:                      # S2 cross-class arg-min
        lines.append(line("Nearest object overall", list(near.values()),
                          lambda g: g["dist"], "nearest"))
    if depth >= 3 and near:                      # S3/S4 per-class band + sector
        parts = []
        for k in sorted(near):
            g = near[k]
            if depth >= 4:
                parts.append(f"{k}: {V9.band(g['dist'])} away, {sector(g)}")
            else:
                parts.append(f"{k}: {sector(g)}")
        lines.append("Nearest of each type: " + "; ".join(parts))
    if depth >= 5:                               # S5 counts, total first
        lines.insert(0, counts_line(ags))
    return "\n".join(l for l in lines if l)


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
    render = lambda st: serialize_v12(st, args.depth)  # noqa: E731
    ln = sorted(len(render(st)) for st in states.values())
    v9ln = sorted(len(V9.typed_text(st)) for st in states.values())
    print(f"[v12] stream chars median {ln[len(ln)//2]} P95 {ln[int(.95*len(ln))]}"
          f"   (v9: {v9ln[len(v9ln)//2]} / {v9ln[int(.95*len(v9ln))]})", flush=True)

    from openai import OpenAI
    client = OpenAI(base_url=args.base_url, api_key=args.api_key)
    items = [json.loads(l) for l in open(ROOT / args.qa, encoding="utf-8")]
    outdir = ROOT / args.out
    outdir.mkdir(parents=True, exist_ok=True)
    fp = outdir / "state_typed__clean__forced.jsonl"
    done = set()
    if fp.exists():
        done = {json.loads(l)["qa_id"] for l in open(fp, encoding="utf-8")}
        print(f"[v12] resume {len(done)}", flush=True)
    f = open(fp, "a", encoding="utf-8")
    tag = f"v12_d{args.depth}"
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


if __name__ == "__main__":
    main()
