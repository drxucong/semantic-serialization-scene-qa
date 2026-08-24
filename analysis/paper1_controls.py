"""Paper-1 control & ladder analysis (cloud-side, runs on staged per-item logs).

Computes, all with scene-cluster paired bootstrap (B=20000, seed 0):
  Control B : annotated-image VLM vs raw-image VLM (same prompt, same machine)
  Control A : Qwen2.5-VL-7B reading serialized text vs Qwen2.5-7B (same text)
  Ladder    : L0..L6 accuracies and consecutive increments; L7 = shipped v9
  3B        : real perceived state + 3B reader
  Cross-fam : Mac-side readers vs the Mac-side qwen2.5:7b anchor (never mixed
              with 5090 numbers -- iron rule 9)
Dedupes every file by qa_id (keeping the last record) because resumed runs can
append a duplicate row at the restart boundary.
Usage: python paper1_controls.py [uploads_root]
"""
import json, random, sys, collections
from pathlib import Path

ROOT = Path(sys.argv[1] if len(sys.argv) > 1
            else "/mnt/user-data/uploads/lvcworld/outputs")
B, SEED = 20000, 0


def load(rel, key="qa_id"):
    p = ROOT / rel
    if not p.exists():
        return None
    d = {}
    for line in open(p, encoding="utf-8"):
        r = json.loads(line)
        d[r[key]] = r
    return d


def scene_of(rec):
    return rec.get("scene_name") or rec["qa_id"].split("_")[1]


def boot(pairs):
    scenes = sorted({s for s, _ in pairs})
    by = {s: [] for s in scenes}
    for s, v in pairs:
        by[s].append(v)
    rng = random.Random(SEED)
    st = []
    for _ in range(B):
        acc = []
        for _ in scenes:
            acc.extend(by[rng.choice(scenes)])
        st.append(sum(acc) / len(acc))
    st.sort()
    d = sum(sum(v) for v in by.values()) / sum(len(v) for v in by.values())
    return d, st[int(.025 * B)], st[int(.975 * B)]


def contrast(A, B_, label, per_family=False):
    if A is None or B_ is None:
        print(f"{label:<44} [missing]")
        return None
    qs = sorted(set(A) & set(B_))
    pairs = [(scene_of(A[q]), int(bool(A[q]["correct"])) - int(bool(B_[q]["correct"])))
             for q in qs]
    d, lo, hi = boot(pairs)
    star = "*" if (lo > 0 or hi < 0) else " "
    aa = sum(bool(A[q]["correct"]) for q in qs) / len(qs)
    bb = sum(bool(B_[q]["correct"]) for q in qs) / len(qs)
    print(f"{label:<44} {aa:.4f} vs {bb:.4f}  {d:+.4f} [{lo:+.4f},{hi:+.4f}]{star} n={len(qs)}")
    out = {"label": label, "accA": round(aa, 4), "accB": round(bb, 4),
           "delta": round(d, 4), "ci": [round(lo, 4), round(hi, 4)],
           "n": len(qs), "sig": bool(lo > 0 or hi < 0)}
    if per_family:
        fam = {}
        for f in sorted({A[q].get("category") for q in qs}):
            fq = [q for q in qs if A[q].get("category") == f]
            fp = [(scene_of(A[q]),
                   int(bool(A[q]["correct"])) - int(bool(B_[q]["correct"])))
                  for q in fq]
            fd, flo, fhi = boot(fp)
            fam[f] = {"n": len(fq), "delta": round(fd, 4),
                      "ci": [round(flo, 4), round(fhi, 4)],
                      "accA": round(sum(bool(A[q]["correct"]) for q in fq)/len(fq), 4),
                      "accB": round(sum(bool(B_[q]["correct"]) for q in fq)/len(fq), 4)}
        out["by_family"] = fam
        for f, v in fam.items():
            print(f"    {f:<16} {v['accA']:.3f} vs {v['accB']:.3f} "
                  f"{v['delta']:+.4f} [{v['ci'][0]:+.4f},{v['ci'][1]:+.4f}] n={v['n']}")
    return out



def did(a7, a3, b7, b3, lab):
    """Difference-in-differences: (a7-a3) - (b7-b3), paired per item.
    Answers 'which interface degrades less when the reader is shrunk',
    which is the deployment question -- absolute cross-scale scores are not
    comparable, slopes are."""
    if not all([a7, a3, b7, b3]):
        print(f"{lab:<44} [missing]")
        return None
    qs = sorted(set(a7) & set(a3) & set(b7) & set(b3))
    def c(d, q):
        return int(bool(d[q]["correct"]))
    slope_a = sum(c(a7, q) - c(a3, q) for q in qs) / len(qs)
    slope_b = sum(c(b7, q) - c(b3, q) for q in qs) / len(qs)
    pairs = [(scene_of(a7[q]),
              (c(a7, q) - c(a3, q)) - (c(b7, q) - c(b3, q))) for q in qs]
    d, lo, hi = boot(pairs)
    star = "*" if (lo > 0 or hi < 0) else " "
    print(f"{lab}")
    print(f"    text  7B->3B loss {slope_a:+.4f}")
    print(f"    pixel 7B->3B loss {slope_b:+.4f}")
    print(f"    DiD (text loss - pixel loss) {d:+.4f} [{lo:+.4f},{hi:+.4f}]{star}  n={len(qs)}")
    return {"slope_text": round(slope_a, 4), "slope_pixel": round(slope_b, 4),
            "did": round(d, 4), "ci": [round(lo, 4), round(hi, 4)],
            "n": len(qs), "sig": bool(lo > 0 or hi < 0)}


def main():
    res = {}
    P = "phase10/coda/"
    v9 = load(P + "results_system9_kf_7b/state_typed__clean__forced.jsonl")
    px = load(P + "results_qwen2.5vl_7b/pixel__clean__forced.jsonl")

    print("=== Control B: annotated image vs raw image (same VLM, same prompt) ===")
    raw = load("anno_img/vlm_raw_7b.jsonl")
    ann = load("anno_img/vlm_anno_7b.jsonl")
    res["controlB"] = contrast(ann, raw, "anno-image - raw-image", per_family=True)
    if ann and v9:
        res["controlB_vs_v9"] = contrast(v9, ann, "v9 text - anno-image")
    # content-matched interface contrast: BOTH sides carry GT content on the
    # full bank; only the interface differs (annotated pixels vs v9 text).
    gtv9 = load(P + "results_gt_v9ser_7b/state_typed__clean__forced.jsonl")
    if gtv9:
        print(f"  GT-state + v9 serializer acc = "
              f"{sum(bool(r['correct']) for r in gtv9.values())/len(gtv9):.4f}")
        res["gtv9_vs_anno"] = contrast(gtv9, ann,
                                       "GT+v9 text - GT-anno image (content-matched)")
        res["gtv9_vs_raw"] = contrast(gtv9, raw, "GT+v9 text - raw image")
        res["gtv9_vs_v9"] = contrast(gtv9, v9, "GT+v9 text - real-perception v9")
        gtv3 = load(P + "results_qwen2.5_7b/state_typed__clean__forced.jsonl")
        res["gtv9_vs_gtv3"] = contrast(gtv9, gtv3,
                                       "GT+v9 serializer - GT+v3 serializer",
                                       per_family=True)

    print("\n=== Control A: same decoder, text interface ===")
    ca = load(P + "results_ctrlA_vl7b_text/state_typed__clean__forced.jsonl")
    res["controlA"] = contrast(ca, v9, "VL-7B on text - 7B on text (=v9)")
    if ca and px:
        res["controlA_vs_pixel"] = contrast(ca, px, "VL-7B on text - VL-7B on pixels")

    print("\n=== Real-state 3B reader ===")
    r3 = load(P + "results_v9_3b/state_typed__clean__forced.jsonl")
    res["real3b_vs_pixel"] = contrast(r3, px, "3B on real state - 7B VLM on pixels")
    res["real3b_vs_v9"] = contrast(r3, v9, "3B on real state - 7B on real state")

    print("\n=== Serializer operator ladder (L7 = shipped v9) ===")
    lad = {}
    for L in range(7):
        lad[L] = load(P + f"results_lad_L{L}/state_typed__clean__forced.jsonl")
    lad[7] = v9
    accs = {}
    for L in range(8):
        if lad[L]:
            qs = list(lad[L])
            accs[L] = sum(bool(lad[L][q]["correct"]) for q in qs) / len(qs)
            print(f"  L{L}: {accs[L]:.4f}  (n={len(qs)})")
    res["ladder_acc"] = {f"L{k}": round(v, 4) for k, v in accs.items()}
    print("  -- consecutive increments --")
    inc = {}
    names = {1: "+distance ordering", 2: "+side/view words",
             3: "+counts header", 4: "+nearest-of-type block",
             5: "+pre-banding", 6: "+confidence split", 7: "+boundary flags"}
    for L in range(1, 8):
        if lad.get(L) and lad.get(L - 1):
            r = contrast(lad[L], lad[L - 1], f"  L{L}-L{L-1} {names[L]}",
                         per_family=(L in (2, 5)))
            if r:
                inc[f"L{L}-L{L-1}"] = r
    res["ladder_increments"] = inc
    if lad.get(0) and px:
        res["L0_vs_pixel"] = contrast(lad[0], px, "  L0 (raw object list) - pixel VLM")

    print("\n=== Cross-family readers (Mac-internal pairing only) ===")
    anchor = load(P + "results_mac_v9_qwen7b/state_typed__clean__forced.jsonl")
    # PAPER CONTROL = llama3.1:8b only (same scale, same model class, other
    # family). gpt-oss (reasoning) and gemma4 (QAT MoE) differ from the anchor
    # on a second axis; the reasoning channel cannot be cleanly disabled on
    # this stack (think:false leaks), so they are logged, never reported.
    for tag, rel in (("llama3.1:8b  [PAPER CONTROL]", "results_mac_v9_llama31"),
                     ("gpt-oss:20b        [log only]", "results_mac_v9_gptoss_fix"),
                     ("gemma4:26b         [log only]", "results_mac_v9_gemma4_fix")):
        arm = load(P + rel + "/state_typed__clean__forced.jsonl")
        if arm:
            pr = sum(1 for q in arm if arm[q].get("pred")) / len(arm)
            print(f"  {tag} parse rate {pr:.3f}")
            res[f"xfam_{tag}"] = contrast(arm, anchor, f"  {tag} - Mac qwen2.5:7b anchor")

    print("\n=== Scale-degradation slopes (deployment question) ===")
    vl3 = load(P + "results_qwen2.5vl_3b/pixel__clean__forced.jsonl")
    t3_gt = load(P + "results_qwen2.5_3b/state_typed__clean__forced.jsonl")
    t7_gt = load(P + "results_qwen2.5_7b/state_typed__clean__forced.jsonl")
    print("  -- scale-matched interface contrasts (the 2x2 cells) --")
    res["m7"] = contrast(v9, px, "  7B: real-state text - pixel VLM")
    res["m3"] = contrast(r3, vl3, "  3B: real-state text - pixel VLM")
    print("  -- each interface's own 7B->3B loss, with CI --")
    res["slope_text"] = contrast(v9, r3, "  text  7B - text  3B")
    res["slope_pix"] = contrast(px, vl3, "  pixel 7B - pixel 3B")
    res["did_real_state"] = did(v9, r3, px, vl3,
                                "  real-perception text vs pixel VLM")
    res["did_gt_state"] = did(t7_gt, t3_gt, px, vl3,
                              "  GT-state text vs pixel VLM")


    print("\n=== Review-round-4 additions ===")
    print("-- leave-one-out from the FULL serializer (path-independent check) --")
    lb = load(P + "results_loo_noband/state_typed__clean__forced.jsonl")
    lr = load(P + "results_loo_nobear/state_typed__clean__forced.jsonl")
    res["loo_banding"] = contrast(v9, lb, "  v9 - (v9 minus pre-banding)", per_family=True)
    res["loo_bearing"] = contrast(v9, lr, "  v9 - (v9 minus bearing discretization)", per_family=True)

    print("-- instrument fix: BOTH pixel scales under the same retry ladder --")
    px7r = load(P + "results_qwen2.5vl_7b_retry/pixel__clean__forced.jsonl")
    px3r = load(P + "results_qwen2.5vl_3b_retry/pixel__clean__forced.jsonl")
    for tag, d in (("pixel7 retry", px7r), ("pixel3 retry", px3r)):
        if d:
            pr = sum(1 for r in d.values() if r.get("pred")) / len(d)
            esc = sum(1 for r in d.values() if r.get("attempts", 1) > 1)
            acc = sum(1 for r in d.values() if r["correct"]) / len(d)
            print(f"  {tag}: acc {acc:.4f}  parse {pr:.3f}  escalated {esc}")
    res["m7_retry"] = contrast(v9, px7r, "  7B: text - pixel (retry ladder)")
    res["m3_retry"] = contrast(r3, px3r, "  3B: text - pixel (retry ladder)")
    res["did_retry"] = did(v9, r3, px7r, px3r, "  DiD with fixed instrument")

    print("-- exact-content: same bytes as tokens vs as pixels, same decoder --")
    gtvl_txt = load(P + "results_gtv9_vl7b_text/state_typed__clean__forced.jsonl")
    gtvl_img = load(P + "results_serialimg_vl7b_gt/serial_image__clean__forced.jsonl")
    for tag, d in (("VL-7B on GT text (tokens)", gtvl_txt),
                   ("VL-7B on GT text (pixels)", gtvl_img)):
        if d:
            pr = sum(1 for r in d.values() if r.get("pred")) / len(d)
            acc = sum(1 for r in d.values() if r["correct"]) / len(d)
            print(f"  {tag}: acc {acc:.4f}  parse {pr:.3f}")
    res["exact_content"] = contrast(gtvl_txt, gtvl_img,
                                    "  same bytes: tokens - pixels (VL-7B)",
                                    per_family=True)
    if gtvl_txt and gtv9:
        res["gt_decoder_swap"] = contrast(gtv9, gtvl_txt,
                                          "  GT text: 7B text-only - VL-7B")

    out = Path("/home/claude/work/analysis/paper1_controls.json")
    json.dump(res, open(out, "w"), indent=1)
    print(f"\nwritten -> {out}")


if __name__ == "__main__":
    main()
