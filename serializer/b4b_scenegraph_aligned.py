"""B4b (Access resubmission, second round of internal review): CONTENT-MATCHED scene
graphs. B4 (b4_scenegraph.py) wrote the raw object list as triples / JSON and so
changed content and format together. Here the content is held fixed: the graph
carries exactly what the shipped Scoped stream carries for the question family
(counts with uncertain counts, forward-path selection with runner-up, nearest object
with runner-up, per-class range band and sector, and, for counting only, the object
rows), and only the notation changes:

  --mode sga_triples   one relation triple per line
  --mode sga_json      one JSON object

Equality of content is enforced, not assumed: for every item the Scoped text is
re-rendered from the same intermediate structure and must equal
run_serializer_dladder.serialize_dl(state, family, "d0") byte for byte
(--check runs this over the whole bank and exits).
Resume-safe; output format identical to run_serializer_dladder.py.
"""
import argparse, collections, json, sys, time
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
for p in ("scripts/paper", "scripts/pilot", "scripts/coda"):
    sys.path.insert(0, str(ROOT / p))
import run_serializer_dladder as DL  # noqa: E402
from run_pilot_phase0 import parse_letter  # noqa: E402
V9, V12 = DL.V9, DL.V12


def struct(st, category):
    """The content of the Scoped (d0) stream as data. Mirrors serialize_dl(mode='d0')."""
    ags = st["agents"]
    near = V12.nearest_by_cls(ags)
    tot = collections.Counter(g["cls"] for g in ags)
    unc = collections.Counter(g["cls"] for g in ags if g.get("lowconf"))
    S = {"counts": [(k, tot[k], unc.get(k, 0)) for k in sorted(tot)], "path": None, "nearest": None,
         "per_class": [], "rows": None}

    def sel(cands):
        order = DL.top2_objs(cands, lambda g: g["dist"])
        if not order:
            return None
        w = order[0]; r = order[1] if len(order) > 1 else None
        return {"first": w["cls"], "next": r["cls"] if r else None,
                "close": bool(r) and (r["dist"] - w["dist"]) < V12.EPS}
    if ags:
        corr = [g for g in ags if V12.in_corridor(g)]
        S["path"] = sel(corr) if corr else "empty"
    if near:
        S["nearest"] = sel(list(near.values()))
        S["per_class"] = [(k, V9.band(near[k]["dist"]) + " away", V12.sector(near[k])) for k in sorted(near)]
    if category in DL.NEEDS_ROWS and ags:
        S["rows"] = [{"id": g["id"], "cls": g["cls"], "dist": g["dist"], "bearing": g["bearing"],
                      "side": V9.side(g["bearing"]), "view": V9.view_sector(g.get("u")),
                      "uncertain": bool(g.get("lowconf"))} for g in ags]
    return S


def render_scoped(S):
    """Re-render the Scoped text from the structure (used only for the equality check)."""
    lines = ["Counts by type: " + (", ".join(f"{k}={n}" + (f" ({u} uncertain)" if u else "") for k, n, u in S["counts"]) or "none")]

    def sel_line(prefix, s, nextword):
        t = f"{prefix}: {s['first']}"
        if s["next"]:
            t += f" (next {nextword}: {s['next']}" + ("; too close to call)" if s["close"] else ")")
        return t
    if S["path"] == "empty":
        lines.append("Closest to the robot's forward path: nothing in the forward corridor")
    elif S["path"]:
        lines.append(sel_line("Closest to the robot's forward path", S["path"], "closest"))
    if S["nearest"]:
        lines.append(sel_line("Nearest object overall", S["nearest"], "nearest"))
    if S["per_class"]:
        lines.append("Nearest of each type: " + "; ".join(f"{k}: {b}, {sec}" for k, b, sec in S["per_class"]))
    if S["rows"]:
        lines.append("Visible objects (nearest first):")
        for r in S["rows"]:
            lines.append(f"{r['id']} [{r['cls']}] dist={r['dist']}m bearing={r['bearing']}deg ({r['side']})"
                         + (f" view={r['view']}" if r["view"] else "") + (" (uncertain)" if r["uncertain"] else ""))
    return "\n".join(lines)


def sga_triples(S):
    out = []
    for k, n, u in S["counts"]:
        out.append(f"(scene, count_of_{k.replace(' ', '_')}, {n})")
        if u:
            out.append(f"(scene, uncertain_count_of_{k.replace(' ', '_')}, {u})")
    if not S["counts"]:
        out.append("(scene, count_of_objects, none)")
    for key, rel, nxt in (("path", "closest_on_forward_path", "next_closest_on_forward_path"),
                          ("nearest", "nearest_object", "next_nearest_object")):
        s = S[key]
        if s == "empty":
            out.append("(robot, closest_on_forward_path, nothing in the forward corridor)")
        elif s:
            out.append(f"(robot, {rel}, {s['first']})")
            if s["next"]:
                out.append(f"(robot, {nxt}, {s['next']})")
                if s["close"]:
                    out.append(f"(robot, {rel}_too_close_to_call, yes)")
    for k, b, sec in S["per_class"]:
        out.append(f"(nearest {k}, range, {b})")
        out.append(f"(nearest {k}, position, {sec})")
    for r in S["rows"] or []:
        nid = f"{r['cls'].replace(' ', '_')}{r['id']}"
        out.append(f"(robot, sees, {nid})")
        out.append(f"({nid}, distance_m, {r['dist']})")
        out.append(f"({nid}, bearing_deg, {r['bearing']})")
        out.append(f"({nid}, side, {r['side']})")
        if r["view"]:
            out.append(f"({nid}, view, {r['view']})")
        if r["uncertain"]:
            out.append(f"({nid}, confidence, uncertain)")
    return "Scene graph:\n" + "\n".join(out)


def sga_json(S):
    d = {"counts": {k: ({"total": n, "uncertain": u} if u else {"total": n}) for k, n, u in S["counts"]}}
    if S["path"] == "empty":
        d["forward_path"] = "nothing in the forward corridor"
    elif S["path"]:
        d["forward_path"] = {"closest": S["path"]["first"], **({"next_closest": S["path"]["next"]} if S["path"]["next"] else {}),
                             **({"too_close_to_call": True} if S["path"]["close"] else {})}
    if S["nearest"]:
        d["nearest_object"] = {"nearest": S["nearest"]["first"], **({"next_nearest": S["nearest"]["next"]} if S["nearest"]["next"] else {}),
                               **({"too_close_to_call": True} if S["nearest"]["close"] else {})}
    if S["per_class"]:
        d["nearest_of_each_type"] = {k: {"range": b, "position": sec} for k, b, sec in S["per_class"]}
    if S["rows"]:
        d["objects"] = [{"id": r["id"], "class": r["cls"], "distance_m": r["dist"], "bearing_deg": r["bearing"], "side": r["side"],
                         **({"view": r["view"]} if r["view"] else {}), **({"uncertain": True} if r["uncertain"] else {})} for r in S["rows"]]
    return "Scene graph (JSON):\n" + json.dumps(d, separators=(",", ":"))


SER = {"sga_triples": sga_triples, "sga_json": sga_json}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=list(SER))
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--qa", default="outputs/coda/qa_confirm.jsonl")
    ap.add_argument("--states", default="outputs/coda/states_confirm_v9.json")
    ap.add_argument("--model", default="qwen2.5:7b")
    ap.add_argument("--base-url", default="http://localhost:11434/v1")
    ap.add_argument("--out")
    a = ap.parse_args()
    sp = ROOT / a.states
    if not sp.exists():
        sp = Path(__file__).resolve().parents[1] / "states/states_confirm_v9.json"   # release layout
    states = json.load(open(sp, encoding="utf-8"))
    items = [i for i in DL.load_bank(a.qa, "repo") if i["sample_id"] in states]
    bad = 0
    for it in items:                                   # content equality, every item, every run
        st = states[it["sample_id"]]
        if render_scoped(struct(st, it["category"])) != DL.serialize_dl(st, it["category"], "d0"):
            bad += 1
            if bad <= 2:
                print("MISMATCH", it["qa_id"], "\n--- struct\n", render_scoped(struct(st, it["category"])),
                      "\n--- d0\n", DL.serialize_dl(st, it["category"], "d0"), flush=True)
    print(f"[b4b] content check: {len(items) - bad}/{len(items)} items re-render the Scoped stream exactly", flush=True)
    if bad:
        raise SystemExit("content check failed")
    if a.check:
        it = items[0]; S = struct(states[it["sample_id"]], it["category"])
        ln = {m: sorted(len(SER[m](struct(states[i["sample_id"]], i["category"]))) for i in items) for m in SER}
        d0 = sorted(len(DL.serialize_dl(states[i["sample_id"]], i["category"], "d0")) for i in items)
        print("median chars: scoped", d0[len(d0) // 2], {m: v[len(v) // 2] for m, v in ln.items()})
        print(sga_triples(S)[:900]); print(sga_json(S)[:900]); return
    from openai import OpenAI
    client = OpenAI(base_url=a.base_url, api_key="ollama")
    outdir = ROOT / a.out; outdir.mkdir(parents=True, exist_ok=True)
    fp = outdir / "state_typed__clean__forced.jsonl"
    done = {json.loads(l)["qa_id"] for l in open(fp, encoding="utf-8")} if fp.exists() else set()
    f = open(fp, "a", encoding="utf-8"); t0 = time.time()
    for i, it in enumerate(items):
        if it["qa_id"] in done:
            continue
        scene = SER[a.mode](struct(states[it["sample_id"]], it["category"]))
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
    rs = [json.loads(l) for l in open(fp, encoding="utf-8")]
    print(f"[{a.mode}|{a.model}] {sum(r['correct'] for r in rs)}/{len(rs)} = {sum(r['correct'] for r in rs)/max(len(rs),1):.4f}"
          f" errors {sum(str(r['raw_head']).startswith('__ERROR__') for r in rs)} -> {fp}", flush=True)


if __name__ == "__main__":
    main()
