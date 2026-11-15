"""v9 text arm (amendment A2). Same protocol as run_coda_text.py
(information parity, forced track, temp 0, max_tokens 8). Serializer v4:
  - side() boundary fixed to +/-15 deg to MATCH the bank's gold sectors
    (v3 used 12 -> systematic borderline mislabels).
  - Confidence-split counts header (confident + uncertain) so the reader
    can discount low-confidence detections (over-detection fix, P2).
  - 'Nearest by type' closed-form block: per class, nearest distance with
    precomputed distance band and side; borderline flags within 10% of the
    5m/15m band edges or 2 deg of the sector edges (P1 + P4: rules compute
    what rules can, uncertainty made explicit).
"""
import argparse, json, sys, time
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "scripts" / "pilot"))
from run_pilot_phase0 import forced_choices, parse_letter  # noqa: E402

SYSTEM = ("You are a mobile robot's scene analyst. Use the scene description "
          "to answer the multiple-choice question. Reply with ONLY the "
          "option letter.")

def side(b):
    if b > 15: return "left"
    if b < -15: return "right"
    return "center"

def band(d):
    return ("under 5 meters" if d < 5 else
            "5 to 15 meters" if d <= 15 else "over 15 meters")

NO_BORDERLINE = False

def borderline(d, b):
    if NO_BORDERLINE:
        return []
    tags = []
    if abs(d-5) <= 0.5 or abs(d-15) <= 1.5:
        tags.append("near band edge")
    if abs(abs(b)-15) <= 2:
        tags.append("near sector edge")
    return tags

def view_sector(u):
    if u is None: return None
    return "left" if u < 408 else ("center" if u < 816 else "right")

def typed_text(st):
    ags = st["agents"]
    hi = Counter(g["cls"] for g in ags if not g.get("lowconf"))
    lo = Counter(g["cls"] for g in ags if g.get("lowconf"))
    keys = sorted(set(hi) | set(lo))
    csum = ", ".join(f"{k}={hi.get(k,0)}" + (f"+{lo[k]}?" if lo.get(k) else "")
                     for k in keys)
    lines = [f"Counts by type (confident, +uncertain?): {csum or 'none'}"]
    near = {}
    for g in ags:
        if g["cls"] not in near:
            near[g["cls"]] = g
    nb = []
    for k in sorted(near):
        g = near[k]
        tags = borderline(g["dist"], g["bearing"])
        t = f" ({', '.join(tags)})" if tags else ""
        nb.append(f"{k}: {g['dist']}m = {band(g['dist'])} away, "
                  f"{side(g['bearing'])} side{t}")
    lines.append("Nearest of each type: " + ("; ".join(nb) if nb else "none"))
    lines.append("Visible objects (nearest first):")
    for g in ags:
        vs = view_sector(g.get("u"))
        vtxt = f" view={vs}" if vs else ""
        un = " (uncertain)" if g.get("lowconf") else ""
        lines.append(f"{g['id']} [{g['cls']}] dist={g['dist']}m "
                     f"bearing={g['bearing']}deg ({side(g['bearing'])})"
                     f"{vtxt}{un}")
    return "\n".join(lines)

def build_prompt(scene, it, choices):
    lines = ([scene, ""] if scene else []) + \
        [f"Question: {it['question']}", "Options:"]
    for letter, tv in choices.items():
        lines.append(f"{letter}. {tv}")
    lines.append("Answer with ONLY the option letter.")
    return "\n".join(lines)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--qa", required=True)
    ap.add_argument("--states", required=True)
    ap.add_argument("--model", required=True)
    ap.add_argument("--base-url", default="http://localhost:11434/v1")
    ap.add_argument("--api-key", default="ollama")
    ap.add_argument("--out", required=True)
    ap.add_argument("--no-borderline", action="store_true",
                    help="ablation: drop P4 borderline annotations")
    args = ap.parse_args()
    global NO_BORDERLINE
    NO_BORDERLINE = args.no_borderline

    from openai import OpenAI
    client = OpenAI(base_url=args.base_url, api_key=args.api_key)
    items = [json.loads(l) for l in open(args.qa, encoding="utf-8")]
    states = json.load(open(args.states, encoding="utf-8"))
    outdir = Path(args.out); outdir.mkdir(parents=True, exist_ok=True)
    fp = outdir / "state_typed__clean__forced.jsonl"
    done = set()
    if fp.exists():
        done = {json.loads(l)["qa_id"] for l in open(fp)}
    f = open(fp, "a")
    for it in items:
        if it["qa_id"] in done:
            continue
        fch, fans = forced_choices(it)
        if fans is None:
            continue
        scene = typed_text(states[it["sample_id"]])
        t0 = time.time()
        try:
            r = client.chat.completions.create(
                model=args.model, temperature=0, max_tokens=8,
                timeout=180, messages=[
                    {"role": "system", "content": SYSTEM},
                    {"role": "user", "content": build_prompt(scene, it, fch)}])
            raw = r.choices[0].message.content or ""
        except Exception as e:  # noqa: BLE001
            raw = f"__ERROR__ {e}"
        pred = parse_letter(raw or "", set(fch))
        rec = {"qa_id": it["qa_id"], "sample_id": it["sample_id"],
               "scene_name": it["scene_name"], "category": it["category"],
               "arm": "state_typed", "protocol": "clean", "track": "forced",
               "model": args.model, "pred": pred, "answer": fans,
               "correct": pred == fans, "abstained": False,
               "raw_head": (raw or "")[:40],
               "latency_s": round(time.time()-t0, 2),
               "scene_chars": len(scene)}
        f.write(json.dumps(rec) + "\n"); f.flush()
    f.close()
    print(f"[state_typed|{args.model}] done -> {fp}")

if __name__ == "__main__":
    main()
