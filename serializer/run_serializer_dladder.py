"""D-ladder serializer arms (Amendment A3, frozen commit dca34c1).

One code path, four distance representations, switched by --mode:

  d0  SCOPED (reference)  band vocabulary, epsilon flags   -- byte-identical to
      serialize_v15; PROVEN by the --check self-test, not promised.
  d1  NUMERIC             one-decimal metres ("4.7 m"), all selections and
      runner-ups retained and annotated with their numeric distance, all
      epsilon borderline flags dropped (the value carries boundary proximity).
  d2  NUMERIC+ALT         d1 plus a coarse tag with vocabulary and boundaries
      disjoint from the option set: close range (<4 m), mid range (4-12 m),
      far range (>12 m). Tag computed from the DISPLAYED one-decimal value so
      label and printed number can never disagree at a boundary.
  d3  ALT-ONLY            the d2 tags without the numeric value (neg. control).

Side words (left/center/right sectors) are unchanged in every arm; A3 scopes
to distance vocabulary only. The confirmatory D0 arm is NOT re-run: the
existing results_cf_v15_* predictions are the D0/SCOPED arm.

--check runs the three frozen assertions of d_ladder_spec.md over the full
development bank (all four arms serialized for every item):
  A0  d0 == serialize_v15 byte-identical (anchor, implied by spec item 2)
  A1  d1/d2/d3 contain no beta-vocabulary substring (under 5 / 5 to 15 / over 15)
  A2  d1 == d0 after deleting distance fields, byte-identical (single variable).
      Deleting means: d0 loses band tokens + "; too close to call" + row metre
      values; d1 loses its numeric tokens. Residual skeletons must match.
  A3  every d2 numeric carries a tag and every tag agrees with the 4/12 m
      boundaries recomputed from the printed value.

New file; run_serializer_v9..v16 and everything committed in dca34c1 untouched.
Usage:
  python scripts/paper/run_serializer_dladder.py --check
  python scripts/paper/run_serializer_dladder.py --mode d1 --qa outputs/coda/qa_confirm.jsonl \
      --states outputs/coda/states_confirm_v9.json --model qwen2.5:7b --out exp1_runs/...
"""
import argparse, json, re, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
for p in ("", "scripts/pilot", "scripts/coda", "scripts/paper"):
    sys.path.insert(0, str(ROOT / p) if p else str(ROOT))
from run_pilot_phase0 import forced_choices, parse_letter  # noqa: E402
import run_coda_text_v9 as V9  # noqa: E402
import run_serializer_v12 as V12  # noqa: E402
from run_serializer_v15 import serialize_v15, NEEDS_ROWS  # noqa: E402

SYSTEM = V9.SYSTEM
MODES = ("d0", "d1", "d2", "d3")
BETA = ("under 5", "5 to 15", "over 15")

# N1 bank families -> repo categories (for the counting-rows scope switch);
# N2 sub-families mapped to the nearest-matching family, fixed before any run.
FAMILY_TO_CATEGORY = {
    "counting": "counting", "direction": "direction",
    "nearest-class": "nearest_class", "nearest-distance": "nearest_dist",
    "path-object": "path_object",
    "N2A-novelband": "nearest_dist", "N2B-ordinal": "nearest_class",
    "N2C-radius": "counting",
}


def alt_tag(d):
    """close/mid/far tag from the DISPLAYED one-decimal value (4/12 m edges)."""
    v = float(f"{d:.1f}")
    return "close range" if v < 4.0 else ("mid range" if v <= 12.0 else "far range")


def dist_field(d, mode):
    """the per-class distance field ('<field> away' slot minus the ' away')."""
    if mode == "d0":
        return V9.band(d)
    if mode == "d1":
        return f"{d:.1f} m"
    if mode == "d2":
        return f"{d:.1f} m ({alt_tag(d)})"
    return alt_tag(d)


def sel_field(d, mode):
    """distance annotation on S1/S2 selections and runner-ups (none in d0)."""
    if mode == "d1":
        return f"{d:.1f} m"
    if mode == "d2":
        return f"{d:.1f} m ({alt_tag(d)})"
    return alt_tag(d)


def top2_objs(cands, keyfn):
    order, seen = [], []
    for a in sorted(cands, key=keyfn):
        if a["cls"] not in seen:
            seen.append(a["cls"])
            order.append(a)
    return order


def line_dl(prefix, cands, nextword, mode):
    order = top2_objs(cands, lambda g: g["dist"])
    if not order:
        return None
    w = order[0]
    r = order[1] if len(order) > 1 else None
    if mode == "d0":                       # V12.line verbatim
        s = f"{prefix}: {w['cls']}"
        if r:
            close = (r["dist"] - w["dist"]) < V12.EPS
            s += (f" (next {nextword}: {r['cls']}"
                  + ("; too close to call)" if close else ")"))
        return s
    s = f"{prefix}: {w['cls']}, {sel_field(w['dist'], mode)}"
    if r:
        s += f" (next {nextword}: {r['cls']}, {sel_field(r['dist'], mode)})"
    return s


def object_rows(st, mode):
    """v14 object_list (V9 raw rows + header), distance representation switched."""
    ags = st["agents"]
    if not ags:
        return ""
    lines = ["Visible objects (nearest first):"]
    for g in ags:
        if mode == "d0":
            dtxt = f"dist={g['dist']}m"
        elif mode == "d1":
            dtxt = f"dist={g['dist']:.1f} m"
        elif mode == "d2":
            dtxt = f"dist={g['dist']:.1f} m ({alt_tag(g['dist'])})"
        else:
            dtxt = f"dist={alt_tag(g['dist'])}"
        vs = V9.view_sector(g.get("u"))
        vtxt = f" view={vs}" if vs else ""
        un = " (uncertain)" if g.get("lowconf") else ""
        lines.append(f"{g['id']} [{g['cls']}] {dtxt} "
                     f"bearing={g['bearing']}deg ({V9.side(g['bearing'])})"
                     f"{vtxt}{un}")
    return "\n".join(lines)


def serialize_dl(st, category, mode):
    """v15 structure exactly; only the distance representation moves with mode."""
    ags = st["agents"]
    near = V12.nearest_by_cls(ags)
    lines = []
    if ags:                                          # S1 corridor arg-min
        corr = [g for g in ags if V12.in_corridor(g)]
        if corr:
            lines.append(line_dl("Closest to the robot's forward path",
                                 corr, "closest", mode))
        else:
            lines.append("Closest to the robot's forward path: "
                         "nothing in the forward corridor")
    if near:                                         # S2 cross-class arg-min
        lines.append(line_dl("Nearest object overall", list(near.values()),
                             "nearest", mode))
    if near:                                         # S3/S4 per-class line
        parts = [f"{k}: {dist_field(near[k]['dist'], mode)} away, "
                 f"{V12.sector(near[k])}" for k in sorted(near)]
        lines.append("Nearest of each type: " + "; ".join(parts))
    lines.insert(0, V12.counts_line(ags))            # S5 counts, total first
    head = "\n".join(l for l in lines if l)
    if category in NEEDS_ROWS:
        body = object_rows(st, mode)
        head = head + ("\n" + body if body else "")
    return head


# ---------------------------------------------------------------- assertions
def strip_d0(t):
    t = re.sub(r"(under 5|5 to 15|over 15) meters", "", t)
    t = t.replace("; too close to call", "")
    t = re.sub(r"dist=\d+(?:\.\d+)?m", "dist=", t)
    return t


def strip_d1(t):
    t = re.sub(r"dist=\d+\.\d m", "dist=", t)
    t = re.sub(r", \d+\.\d m", "", t)
    t = re.sub(r"\d+\.\d m", "", t)
    return t


TAGGED = re.compile(r"(\d+\.\d) m(?: away)? \((close|mid|far) range\)")
NUMERIC = re.compile(r"\d+\.\d m")


def check(qa_path, states_path):
    states = json.load(open(ROOT / states_path, encoding="utf-8"))
    items = [json.loads(l) for l in open(ROOT / qa_path, encoding="utf-8")]
    items = [i for i in items if i["sample_id"] in states]
    n = len(items)
    fail = {k: 0 for k in ("A0", "A1", "A2", "A3")}
    examples = {}
    for it in items:
        st = states[it["sample_id"]]
        cat = it["category"]
        out = {m: serialize_dl(st, cat, m) for m in MODES}
        if out["d0"] != serialize_v15(st, cat):
            fail["A0"] += 1
            examples.setdefault("A0", (it["qa_id"], out["d0"],
                                       serialize_v15(st, cat)))
        for m in ("d1", "d2", "d3"):
            if any(b in out[m] for b in BETA):
                fail["A1"] += 1
                examples.setdefault("A1", (it["qa_id"], m, out[m]))
                break
        if strip_d0(out["d0"]) != strip_d1(out["d1"]):
            fail["A2"] += 1
            examples.setdefault("A2", (it["qa_id"], strip_d0(out["d0"]),
                                       strip_d1(out["d1"])))
        d2 = out["d2"]
        pairs = TAGGED.findall(d2)
        n_num = len(NUMERIC.findall(d2))
        bad = [p for p in pairs if f"{p[1]} range" != alt_tag(float(p[0]))]
        if bad or len(pairs) != n_num:
            fail["A3"] += 1
            examples.setdefault("A3", (it["qa_id"], bad, len(pairs), n_num))
    print(f"[dladder --check] development bank: {n} items x 4 arms")
    print(f"  A0 d0==serialize_v15 byte-identical : {n - fail['A0']}/{n}"
          f"  ({'PASS' if not fail['A0'] else 'FAIL'})")
    print(f"  A1 no beta substring in d1/d2/d3    : "
          f"{n - fail['A1']}/{n}  ({'PASS' if not fail['A1'] else 'FAIL'})")
    print(f"  A2 d1==d0 after field deletion      : "
          f"{n - fail['A2']}/{n}  ({'PASS' if not fail['A2'] else 'FAIL'})")
    print(f"  A3 d2 tag/value agree at 4/12 m     : "
          f"{n - fail['A3']}/{n}  ({'PASS' if not fail['A3'] else 'FAIL'})")
    for k, v in examples.items():
        print(f"  [example {k}] {v}")
    if any(fail.values()):
        sys.exit(1)
    print("[dladder --check] ALL ASSERTIONS PASS")


# ------------------------------------------------------------------- runner
def load_bank(path, bank_format):
    items = [json.loads(l) for l in open(ROOT / path, encoding="utf-8")]
    out = []
    for it in items:
        if bank_format == "repo":
            fch, fans = forced_choices(it)
            if fans is None:
                continue
            out.append({"qa_id": it["qa_id"], "sample_id": it["sample_id"],
                        "scene_name": it["scene_name"],
                        "category": it["category"], "family": it["category"],
                        "question": it["question"], "choices": fch,
                        "answer": fans})
        else:                                   # schema (frozen N1/N2 banks)
            out.append({"qa_id": it["question_id"],
                        "sample_id": it["frame_id"],
                        "scene_name": it["sequence_id"],
                        "category": FAMILY_TO_CATEGORY[it["family"]],
                        "family": it["family"],
                        "question": it["stem"], "choices": it["options"],
                        "answer": it["gold"]})
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true",
                    help="run the three frozen assertions on the dev bank")
    ap.add_argument("--mode", choices=MODES)
    ap.add_argument("--qa", default="outputs/coda/qa_coda.jsonl")
    ap.add_argument("--states", default="outputs/coda/states_kf_v9.json")
    ap.add_argument("--bank-format", choices=("repo", "schema"), default="repo")
    ap.add_argument("--model", default="qwen2.5:7b")
    ap.add_argument("--base-url", default="http://localhost:11434/v1")
    ap.add_argument("--api-key", default="ollama")
    ap.add_argument("--out")
    args = ap.parse_args()

    if args.check:
        check(args.qa, args.states)
        return
    if not (args.mode and args.out):
        ap.error("--mode and --out required unless --check")

    states = json.load(open(ROOT / args.states, encoding="utf-8"))
    items = load_bank(args.qa, args.bank_format)
    skip = [i for i in items if i["sample_id"] not in states]
    if skip:
        print(f"[dladder] WARNING {len(skip)} items without a state, skipped",
              flush=True)
    items = [i for i in items if i["sample_id"] in states]

    from openai import OpenAI
    client = OpenAI(base_url=args.base_url, api_key=args.api_key)
    outdir = ROOT / args.out
    outdir.mkdir(parents=True, exist_ok=True)
    fp = outdir / "state_typed__clean__forced.jsonl"
    done = set()
    if fp.exists():
        done = {json.loads(l)["qa_id"] for l in open(fp, encoding="utf-8")}
        print(f"[dladder {args.mode}] resume {len(done)}", flush=True)
    f = open(fp, "a", encoding="utf-8")
    t0 = time.time()
    for i, it in enumerate(items):
        if it["qa_id"] in done:
            continue
        scene = serialize_dl(states[it["sample_id"]], it["category"], args.mode)
        try:
            r = client.chat.completions.create(
                model=args.model, temperature=0, max_tokens=8, timeout=180,
                messages=[{"role": "system", "content": SYSTEM},
                          {"role": "user",
                           "content": V9.build_prompt(scene, it, it["choices"])}])
            raw = r.choices[0].message.content or ""
        except Exception as e:  # noqa: BLE001
            raw = f"__ERROR__ {e}"
        pred = parse_letter(raw or "", set(it["choices"]))
        f.write(json.dumps({
            "qa_id": it["qa_id"], "sample_id": it["sample_id"],
            "scene_name": it["scene_name"], "category": it["category"],
            "family": it["family"], "arm": f"dladder_{args.mode}",
            "protocol": "clean", "track": "forced", "model": args.model,
            "pred": pred, "answer": it["answer"], "correct": pred == it["answer"],
            "abstained": False, "raw_head": (raw or "")[:40],
            "scene_chars": len(scene)}) + "\n")
        f.flush()
        if (i + 1) % 400 == 0:
            print(f"[dladder {args.mode}|{args.model}] {i+1}/{len(items)} "
                  f"({(time.time()-t0)/60:.1f}min)", flush=True)
    f.close()
    print(f"[dladder {args.mode}|{args.model}] done -> {fp}", flush=True)


if __name__ == "__main__":
    main()
