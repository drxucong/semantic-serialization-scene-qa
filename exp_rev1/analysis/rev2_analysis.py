"""Second-round re-analyses (2026-11-14), all from existing per-item logs.

A. Answer priors on the confirmatory bank: a scene-blind rule built from
   development-bank answer frequencies; absolute per-family accuracy of every main
   arm next to it; primary and supervised contrasts split by whether the prior rule
   is right; nearest-distance accuracy by gold band; counting accuracy when the
   queried class is absent from the perceived state.
B. The sensitivity battery of Table 8 (exact sign-flip, leave-one-sequence-out,
   jackknife, per-sequence means) on the secondary contrasts the argument uses.
C. nuScenes external check reported to the paper's own standard: n and accuracy per
   family, parse rates, per-family contrasts with 10-cluster intervals, item-level
   decomposition of the 7B margin, a leave-one-scene-out answer prior.
D. Small VLMs of the current generation; the earlier (Flat) serializer on the
   confirmatory bank.
Paired cluster bootstrap everywhere: B=20000, seed 20260809, percentile, each
replicate divided by its own number of questions (the estimator behind the paper's
intervals). Writes rev2_results.json.
"""
import collections, glob, json, re
from pathlib import Path
import numpy as np, pandas as pd
import robustness_cf as RB

HERE = Path(__file__).resolve().parent
REL = Path(__file__).resolve().parents[2]  # repository root
LV = REL
B, SEED = 20000, 20260809
FAMS = ["counting", "direction", "nearest_class", "nearest_dist", "path_object"]
out = {}


def jl(p):
    return [json.loads(l) for l in open(p, encoding="utf-8")]


def arm_jsonl(p):
    ps = glob.glob(str(p)) if any(c in str(p) for c in "*?") else [str(p)]
    return {r["qa_id"]: r for r in jl(ps[0])}


# ------------------------------------------------------------------ banks, arms
dev, cf = jl(REL / "banks/qa_coda.jsonl"), jl(REL / "banks/qa_confirm.jsonl")
cfd = {it["qa_id"]: it for it in cf}
ids = [it["qa_id"] for it in cf]
fam = {i: cfd[i]["category"] for i in ids}
seq = {i: int(cfd[i]["scene_name"]) for i in ids}   # int: numeric cluster order, as in robustness_cf.py


def forced(it):
    return {k: v for k, v in it["choices"].items() if k != it.get("abstain_letter")}


csv = pd.read_csv(REL / "results/exp3_predictions/predictions3_cf_v2.csv")
ns = pd.read_csv(REL / "results/exp35/preds_nostereo.csv")
C = {a: dict(zip(g.question_id, g.correct.astype(bool))) for a, g in pd.concat([csv, ns]).groupby("arm")}


def corr(p):
    return {k: bool(v["correct"]) for k, v in arm_jsonl(p).items()}


E = LV / "exp_rev1"
ARMS = {
    "blind_3b": C["BLIND_3b"], "blind_7b": C["BLIND_7b"],
    "pixel_3b": C["PIXEL_3b"], "pixel_7b": C["PIXEL_7b"],
    "scoped_3b": C["D0_3b"], "scoped_7b": C["D0_7b"],
    "ftvlm_3b": C["FT3B_low"], "ftvlm_7b": C["FT7B_low"], "fttext_3b": C["FTTEXT_3b"],
    "nostereo_3b": C["D0NS_3b"], "nostereo_7b": C["D0NS_7b"],
    "gt_3b": corr(REL / "results/phase10/results_cf_gt_3b/*forced.jsonl"),
    "gt_7b": corr(REL / "results/phase10/results_cf_gt_7b/*forced.jsonl"),
    "flat_3b": corr(REL / "results/phase10/results_cf_v9_3b/*forced.jsonl"),
    "flat_7b": corr(REL / "results/phase10/results_cf_v9_7b/*forced.jsonl"),
    "scoped_0.5b": corr(REL / "results/exp2_infer/cf_d0_0.5b/*forced.jsonl"),
    "scoped_1.5b": corr(REL / "results/exp2_infer/cf_d0_1.5b/*forced.jsonl"),
    "moondream": corr(REL / "results/exp2_infer/px_moondream_cf/*forced.jsonl"),
    "llavaphi3": corr(REL / "results/exp2_infer/px_llava-phi3_cf/*forced.jsonl"),
    "q3vl2b_direct": corr(REL / "results/exp2_infer/px_q3vl2b_cf/*forced.jsonl"),
    "q3vl2b_think": C["PXDEV_t1024"],
    "q3txt4b": C["Q3TXT4B_D0"], "q3vl4b": C["Q3VL4B"], "q3txt8b": C["Q3TXT8B_D0"], "q3vl8b": C["Q3VL8B"],
    "zs3b_hf_fullres": C["ZS3B_full_hf"],
    "zs3b_lowres": C["ZS3B_low"],
    "gt_0.5b": corr(REL / "results/exp2_infer/gtcf_d0_0.5b/*forced.jsonl"), "gt_1.5b": corr(REL / "results/exp2_infer/gtcf_d0_1.5b/*forced.jsonl"),
    "d1_3b": corr(REL / "results/exp1_infer/cf_d1_3b/*forced.jsonl"), "d1_7b": corr(REL / "results/exp1_infer/cf_d1_7b/*forced.jsonl"),
    "d2_3b": corr(REL / "results/exp1_infer/cf_d2_3b/*forced.jsonl"), "d2_7b": corr(REL / "results/exp1_infer/cf_d2_7b/*forced.jsonl"),
    "d3_3b": corr(REL / "results/exp1_infer/cf_d3_3b/*forced.jsonl"), "d3_7b": corr(REL / "results/exp1_infer/cf_d3_7b/*forced.jsonl"),
    "pixel_rerun_3b": corr(E / "b123_vlm_aids/pixel_3b/*forced.jsonl"), "pixel_rerun_7b": corr(E / "b123_vlm_aids/pixel_7b/*forced.jsonl"),
    "stereo2_3b": corr(E / "b123_vlm_aids/stereo_3b/*forced.jsonl"), "stereo2_7b": corr(E / "b123_vlm_aids/stereo_7b/*forced.jsonl"),
    "taskinfo_3b": corr(E / "b123_vlm_aids/taskinfo_3b/*forced.jsonl"), "taskinfo_7b": corr(E / "b123_vlm_aids/taskinfo_7b/*forced.jsonl"),
    "hybrid_3b": corr(E / "b123_vlm_aids/hybrid_3b/*forced.jsonl"), "hybrid_7b": corr(E / "b123_vlm_aids/hybrid_7b/*forced.jsonl"),
    "light1_3b": corr(E / "b5_light/infer/cf_d0_light1_3b/*forced.jsonl"), "light1_7b": corr(E / "b5_light/infer/cf_d0_light1_7b/*forced.jsonl"),
    "light2_3b": corr(E / "b5_light/infer/cf_d0_light2_3b/*forced.jsonl"), "light2_7b": corr(E / "b5_light/infer/cf_d0_light2_7b/*forced.jsonl"),
    "light3_3b": corr(E / "b5_light/infer/cf_d0_light3_3b/*forced.jsonl"), "light3_7b": corr(E / "b5_light/infer/cf_d0_light3_7b/*forced.jsonl"),
    "rfdetr_3b": corr(E / "b6_rfdetr/infer/cf_d0_rfdetr_3b/*forced.jsonl"), "rfdetr_7b": corr(E / "b6_rfdetr/infer/cf_d0_rfdetr_7b/*forced.jsonl"),
    "sg_json_3b": corr(E / "b4_scenegraph/sg_json_3b/*forced.jsonl"), "sg_json_7b": corr(E / "b4_scenegraph/sg_json_7b/*forced.jsonl"),
    "sg_triples_3b": corr(E / "b4_scenegraph/sg_triples_3b/*forced.jsonl"), "sg_triples_7b": corr(E / "b4_scenegraph/sg_triples_7b/*forced.jsonl"),
}
for name, pat in {"ctrl_scoped_3b": "ctrl_text/d0_3b", "ctrl_scoped_7b": "ctrl_text/d0_7b",
                  "sga_json_3b": "b4b_scenegraph_aligned/sga_json_3b", "sga_json_7b": "b4b_scenegraph_aligned/sga_json_7b",
                  "sga_triples_3b": "b4b_scenegraph_aligned/sga_triples_3b", "sga_triples_7b": "b4b_scenegraph_aligned/sga_triples_7b"}.items():
    ps = glob.glob(str(E / pat / "*forced.jsonl"))
    if ps and sum(1 for _ in open(ps[0], encoding="utf-8")) == len(ids):
        ARMS[name] = corr(ps[0])
for k, v in ARMS.items():
    assert set(ids) <= set(v), (k, len(v))
out["acc"] = {k: float(np.mean([v[i] for i in ids])) for k, v in ARMS.items()}
out["acc_family"] = {k: {f: float(np.mean([v[i] for i in ids if fam[i] == f])) for f in FAMS} for k, v in ARMS.items()}
out["n_family"] = {f: sum(fam[i] == f for i in ids) for f in FAMS}


def contrast(a, b, sel=None, B=B):
    """paired cluster bootstrap on the items in sel (default: all), plus the battery."""
    sel = sel or ids
    d = pd.DataFrame({"seq": [seq[i] for i in sel], "diff": [float(ARMS[a][i]) - float(ARMS[b][i]) for i in sel]})
    cs = RB.cluster_stats(d)
    bs = RB.paired_cluster_bootstrap(cs, B=B, seed=SEED)
    lo, hi = np.percentile(bs, [2.5, 97.5])
    return d, cs, {"delta": float(d["diff"].mean()), "lo": float(lo), "hi": float(hi), "n": len(d), "clusters": len(cs),
                   "star": bool(lo > 0 or hi < 0)}


def battery(a, b):
    d, cs, r = contrast(a, b)
    obs, p2, p1, mode, nperm = RB.sign_flip_test(cs)
    lo_df = RB.loso(cs)
    full, se, jlo, jhi = RB.jackknife(cs)
    r.update(signflip_p=float(p2), loso_cross_zero=int(((lo_df.ci_lo <= 0) & (lo_df.ci_hi >= 0)).sum()),
             loso_min_lo=float(lo_df.ci_lo.min()), loso_max_hi=float(lo_df.ci_hi.max()),
             jackknife=[float(jlo), float(jhi)], cluster_mean=float(cs["mean"].mean()),
             pos=int((cs["mean"] > 0).sum()), neg=int((cs["mean"] < 0).sum()))
    return r


# ------------------------------------------------------------------ A. priors
cnt = collections.defaultdict(collections.Counter)
for it in dev:
    cnt[it["category"]][it["choices"][it["answer"]]] += 1
prior_right = {}
for it in cf:
    o = forced(it)
    prior_right[it["qa_id"]] = max(o, key=lambda k: cnt[it["category"]][o[k]]) == it["answer"]
ARMS["prior"] = prior_right
out["acc"]["prior"] = float(np.mean([prior_right[i] for i in ids]))
out["acc_family"]["prior"] = {f: float(np.mean([prior_right[i] for i in ids if fam[i] == f])) for f in FAMS}
right = [i for i in ids if prior_right[i]]; wrong = [i for i in ids if not prior_right[i]]
out["prior_strata"] = {"right": len(right), "wrong": len(wrong),
                       "wrong_by_family": {f: sum(fam[i] == f for i in wrong) for f in FAMS}}
out["stratified"] = {}
for a, b in (("scoped_7b", "pixel_7b"), ("scoped_3b", "pixel_3b"), ("ftvlm_3b", "pixel_3b"), ("fttext_3b", "scoped_3b"),
             ("fttext_3b", "ftvlm_3b")):
    out["stratified"][f"{a}-{b}"] = {k: contrast(a, b, s)[2] for k, s in (("all", ids), ("prior_right", right), ("prior_wrong", wrong))}
out["acc_by_stratum"] = {k: {"prior_right": float(np.mean([ARMS[k][i] for i in right])), "prior_wrong": float(np.mean([ARMS[k][i] for i in wrong]))}
                         for k in ("pixel_3b", "pixel_7b", "scoped_3b", "scoped_7b", "ftvlm_3b", "fttext_3b")}
# gold concentration
gc = {}
for f in FAMS:
    c = collections.Counter(cfd[i]["choices"][cfd[i]["answer"]] for i in ids if fam[i] == f)
    gc[f] = c.most_common(3)
out["gold_top"] = gc
# counting: gold rank among the three forced options; zero offered
rank = collections.Counter(); zero_off = zero_gold = 0
for i in ids:
    if fam[i] != "counting":
        continue
    o = forced(cfd[i]); vals = sorted(int(v) for v in o.values()); g = int(cfd[i]["choices"][cfd[i]["answer"]])
    rank[vals.index(g)] += 1; zero_off += (0 in vals); zero_gold += (g == 0)
out["counting_gold_rank"] = {"smallest": rank[0], "middle": rank[1], "largest": rank[2], "zero_offered": zero_off, "zero_gold": zero_gold}
cg = collections.defaultdict(lambda: collections.defaultdict(list))
for i in ids:
    if fam[i] == "counting":
        g = int(cfd[i]["choices"][cfd[i]["answer"]])
        for k in ("scoped_3b", "scoped_7b", "pixel_3b", "pixel_7b"):
            cg[k][min(g, 4)].append(ARMS[k][i])
out["counting_by_gold"] = {k: {str(g): [float(np.mean(v)), len(v)] for g, v in sorted(d.items())} for k, d in cg.items()}
# nearest-distance accuracy by gold band
nd = {}
for k in ("pixel_3b", "pixel_7b", "scoped_3b", "scoped_7b"):
    by = collections.defaultdict(list)
    for i in ids:
        if fam[i] == "nearest_dist":
            by[cfd[i]["choices"][cfd[i]["answer"]]].append(ARMS[k][i])
    nd[k] = {b: [float(np.mean(v)), len(v)] for b, v in by.items()}
out["nearest_dist_by_gold"] = nd
# counting when the queried class is absent from the perceived state
states = json.load(open(REL / "states/states_confirm_v9.json", encoding="utf-8"))
miss = {"n_counting": 0, "class_absent": [], "absent_zero_offered": [], "absent_zero_not_offered": [], "count_equal_gold": [], "count_differs": []}
for i in ids:
    if fam[i] != "counting":
        continue
    it = cfd[i]; m = re.search(r"type '([^']+)'", it["question"]); cls = m.group(1)
    perceived = sum(g["cls"] == cls for g in states[it["sample_id"]]["agents"])
    gold = int(it["choices"][it["answer"]]); vals = [int(v) for v in forced(it).values()]
    miss["n_counting"] += 1
    (miss["count_equal_gold"] if perceived == gold else miss["count_differs"]).append(i)
    if perceived == 0 and gold > 0:
        miss["class_absent"].append(i)
        (miss["absent_zero_offered"] if 0 in vals else miss["absent_zero_not_offered"]).append(i)
out["counting_miss"] = {k: (v if isinstance(v, int) else {"n": len(v), **{a: (float(np.mean([ARMS[a][i] for i in v])) if v else None)
                                                                       for a in ("scoped_3b", "scoped_7b", "pixel_3b", "pixel_7b")}})
                        for k, v in miss.items()}

# ------------------------------------------------------------------ B. battery
pairs = {"primary_3b": ("scoped_3b", "pixel_3b"), "primary_7b": ("scoped_7b", "pixel_7b"),
         "nostereo_vs_pixel_3b": ("nostereo_3b", "pixel_3b"), "nostereo_vs_pixel_7b": ("nostereo_7b", "pixel_7b"),
         "stereo_cue_3b": ("scoped_3b", "nostereo_3b"), "stereo_cue_7b": ("scoped_7b", "nostereo_7b"),
         "hybrid_vs_pixelrerun_3b": ("hybrid_3b", "pixel_rerun_3b"), "hybrid_vs_pixelrerun_7b": ("hybrid_7b", "pixel_rerun_7b"),
         "hybrid_vs_scoped_3b": ("hybrid_3b", "scoped_3b"), "hybrid_vs_scoped_7b": ("hybrid_7b", "scoped_7b"),
         "light1_vs_pixelrerun_3b": ("light1_3b", "pixel_rerun_3b"), "light1_vs_pixelrerun_7b": ("light1_7b", "pixel_rerun_7b"),
         "light1_vs_scoped_3b": ("light1_3b", "scoped_3b"), "light1_vs_scoped_7b": ("light1_7b", "scoped_7b"),
         "rfdetr_vs_scoped_3b": ("rfdetr_3b", "scoped_3b"), "rfdetr_vs_scoped_7b": ("rfdetr_7b", "scoped_7b"),
         "rfdetr_vs_pixelrerun_3b": ("rfdetr_3b", "pixel_rerun_3b"), "rfdetr_vs_pixelrerun_7b": ("rfdetr_7b", "pixel_rerun_7b"),
         "fttext_vs_ftvlm_3b": ("fttext_3b", "ftvlm_3b"), "ftvlm_vs_scoped_3b": ("ftvlm_3b", "scoped_3b"), "ftvlm_vs_scoped_7b": ("ftvlm_7b", "scoped_7b"),
         "scoped_vs_flat_3b": ("scoped_3b", "flat_3b"), "scoped_vs_flat_7b": ("scoped_7b", "flat_7b"),
         "flat_vs_pixel_3b": ("flat_3b", "pixel_3b"), "flat_vs_pixel_7b": ("flat_7b", "pixel_7b"),
         "pixelrerun_vs_archived_3b": ("pixel_rerun_3b", "pixel_3b"), "pixelrerun_vs_archived_7b": ("pixel_rerun_7b", "pixel_7b"),
         "stereo2_vs_pixelrerun_3b": ("stereo2_3b", "pixel_rerun_3b"), "stereo2_vs_pixelrerun_7b": ("stereo2_7b", "pixel_rerun_7b"),
         "taskinfo_vs_pixelrerun_3b": ("taskinfo_3b", "pixel_rerun_3b"), "taskinfo_vs_pixelrerun_7b": ("taskinfo_7b", "pixel_rerun_7b"),
         "scoped1.5b_vs_moondream": ("scoped_1.5b", "moondream"), "scoped1.5b_vs_llavaphi3": ("scoped_1.5b", "llavaphi3"),
         "scoped1.5b_vs_q3vl2b_think": ("scoped_1.5b", "q3vl2b_think"), "scoped1.5b_vs_q3vl2b_direct": ("scoped_1.5b", "q3vl2b_direct"),
         "scoped3b_vs_q3vl2b_think": ("scoped_3b", "q3vl2b_think"), "scoped0.5b_vs_moondream": ("scoped_0.5b", "moondream"),
         "q3txt4b_vs_q3vl4b": ("q3txt4b", "q3vl4b"), "q3txt8b_vs_q3vl8b": ("q3txt8b", "q3vl8b"),
         "sg_json_vs_scoped_3b": ("sg_json_3b", "scoped_3b"), "sg_json_vs_scoped_7b": ("sg_json_7b", "scoped_7b"),
         "sg_triples_vs_scoped_3b": ("sg_triples_3b", "scoped_3b"), "sg_triples_vs_scoped_7b": ("sg_triples_7b", "scoped_7b")}
for sc in ("3b", "7b"):
    pairs[f"d1_vs_scoped_{sc}"] = (f"d1_{sc}", f"scoped_{sc}"); pairs[f"d2_vs_d1_{sc}"] = (f"d2_{sc}", f"d1_{sc}")
    pairs[f"d2_vs_scoped_{sc}"] = (f"d2_{sc}", f"scoped_{sc}"); pairs[f"d3_vs_scoped_{sc}"] = (f"d3_{sc}", f"scoped_{sc}")
    pairs[f"d1_vs_pixel_{sc}"] = (f"d1_{sc}", f"pixel_{sc}"); pairs[f"gt_vs_scoped_{sc}"] = (f"gt_{sc}", f"scoped_{sc}")
    pairs[f"ftvlm_vs_pixel_{sc}"] = (f"ftvlm_{sc}", f"pixel_{sc}")
pairs["fttext_vs_scoped_3b"] = ("fttext_3b", "scoped_3b"); pairs["ftvlm_7b_vs_3b"] = ("ftvlm_7b", "ftvlm_3b")
pairs["gt_vs_ftvlm_7b"] = ("gt_7b", "ftvlm_7b"); pairs["zs3b_lowres_vs_fullres"] = ("zs3b_lowres", "zs3b_hf_fullres")
pairs["scoped7b_vs_1.5b"] = ("scoped_7b", "scoped_1.5b"); pairs["gt1.5b_vs_0.5b"] = ("gt_1.5b", "gt_0.5b")
for sc in ("3b", "7b"):
    if f"ctrl_scoped_{sc}" in ARMS:
        pairs[f"ctrl_vs_archived_scoped_{sc}"] = (f"ctrl_scoped_{sc}", f"scoped_{sc}")
        pairs[f"ctrl_scoped_vs_pixelrerun_{sc}"] = (f"ctrl_scoped_{sc}", f"pixel_rerun_{sc}")
        pairs[f"hybrid_vs_ctrl_scoped_{sc}"] = (f"hybrid_{sc}", f"ctrl_scoped_{sc}")
    if f"ctrl_scoped_{sc}" in ARMS:
        for m in ("light1", "light2", "light3", "rfdetr", "sg_json", "sg_triples", "stereo2", "taskinfo", "pixel_rerun"):
            pairs[f"{m.replace('pixel_rerun', 'pixelrerun')}_vs_ctrl_scoped_{sc}"] = (f"{m}_{sc}", f"ctrl_scoped_{sc}")
        for m in ("light2", "light3", "sg_json", "sg_triples"):
            pairs[f"{m}_vs_pixelrerun_{sc}"] = (f"{m}_{sc}", f"pixel_rerun_{sc}")
    for m in ("sga_json", "sga_triples"):
        if f"{m}_{sc}" in ARMS:
            pairs[f"{m}_vs_scoped_{sc}"] = (f"{m}_{sc}", f"scoped_{sc}")
            pairs[f"{m}_vs_pixelrerun_{sc}"] = (f"{m}_{sc}", f"pixel_rerun_{sc}")
            if f"ctrl_scoped_{sc}" in ARMS:
                pairs[f"{m}_vs_ctrl_scoped_{sc}"] = (f"{m}_{sc}", f"ctrl_scoped_{sc}")
out["battery"] = {k: battery(a, b) for k, (a, b) in pairs.items()}
# per-family contrasts (same bootstrap, items of one family)
out["family_contrast"] = {}
for k in ("primary_3b", "primary_7b", "hybrid_vs_pixelrerun_3b", "hybrid_vs_pixelrerun_7b", "hybrid_vs_ctrl_scoped_3b", "hybrid_vs_ctrl_scoped_7b",
          "taskinfo_vs_pixelrerun_3b", "taskinfo_vs_pixelrerun_7b", "rfdetr_vs_pixelrerun_3b", "rfdetr_vs_pixelrerun_7b",
          "light1_vs_ctrl_scoped_3b", "light1_vs_ctrl_scoped_7b", "d1_vs_scoped_3b", "d1_vs_scoped_7b", "d1_vs_pixel_3b", "d1_vs_pixel_7b",
          "fttext_vs_ftvlm_3b", "scoped_vs_flat_3b", "scoped_vs_flat_7b",
          "sg_triples_vs_ctrl_scoped_3b", "sg_triples_vs_ctrl_scoped_7b", "sg_json_vs_ctrl_scoped_3b", "sg_json_vs_ctrl_scoped_7b"):
    if k in pairs:
        a_, b_ = pairs[k]
        out["family_contrast"][k] = {f: contrast(a_, b_, [i for i in ids if fam[i] == f])[2] for f in FAMS}

# errors of the serialized system: does the same reader answer correctly from ground-truth objects?
out["error_split"] = {}
for sc in ("3b", "7b"):
    err = [i for i in ids if not ARMS[f"scoped_{sc}"][i]]
    out["error_split"][sc] = {"errors": len(err), "right_with_gt": sum(ARMS[f"gt_{sc}"][i] for i in err),
                              "by_family": {f: [sum(1 for i in err if fam[i] == f), sum(ARMS[f"gt_{sc}"][i] for i in err if fam[i] == f)] for f in FAMS}}
# nearest-class: errors in which the gold class is not in the perceived state
nc = {}
for sc in ("3b", "7b"):
    err = [i for i in ids if fam[i] == "nearest_class" and not ARMS[f"scoped_{sc}"][i]]
    absent = sum(1 for i in err if not any(g["cls"] == cfd[i]["choices"][cfd[i]["answer"]] for g in states[cfd[i]["sample_id"]]["agents"]))
    nc[sc] = {"errors": len(err), "gold_class_absent": absent}
out["nearest_class_errors"] = nc

# is the class that the question names (or, for the two class families, the correct class)
# present in the perceived state?
qp = {}
for f in FAMS:
    n = k = 0; acc_in = []; acc_out = []
    for i in ids:
        if fam[i] != f:
            continue
        it = cfd[i]
        if f in ("nearest_class", "path_object"):
            cls = it["choices"][it["answer"]]
        else:
            cls = re.search(r"'([^']+)'", it["question"]).group(1)
        present = any(g["cls"] == cls for g in states[it["sample_id"]]["agents"])
        n += 1; k += present
        (acc_in if present else acc_out).append(ARMS["scoped_7b"][i])
    qp[f] = {"n": n, "present": k, "acc7b_present": float(np.mean(acc_in)) if acc_in else None,
             "acc7b_absent": float(np.mean(acc_out)) if acc_out else None}
out["queried_present"] = qp
out["queried_present_total"] = {"n": sum(v["n"] for v in qp.values()), "present": sum(v["present"] for v in qp.values())}
# net questions of the primary differences by family
out["net_by_family"] = {sc: {f: int(sum(int(ARMS[f"scoped_{sc}"][i]) - int(ARMS[f"pixel_{sc}"][i]) for i in ids if fam[i] == f)) for f in FAMS}
                        for sc in ("3b", "7b")}

# ------------------------------------------------------------------ C. nuScenes
nb = {r["qa_id"]: r for r in jl(LV / "exp_rev1/c1_nusc/qa_nusc.jsonl")}
nids = list(nb); nfam = {i: nb[i]["category"] for i in nids}; nseq = {i: nb[i]["scene_name"] for i in nids}
NA = {}
for name in ("pixel_3b", "pixel_7b", "d0_rfdetr_3b", "d0_rfdetr_7b", "d0_gt_3b", "d0_gt_7b", "blind_3b", "blind_7b"):
    NA[name] = arm_jsonl(E / f"c1_nusc/{name}/*forced.jsonl")
    assert set(nids) <= set(NA[name]), name


def longest_unparsed(rows):
    best = cur = 0
    for i in nids:
        cur = cur + 1 if rows[i].get("pred") is None else 0
        best = max(best, cur)
    return best


def ncontrast(a, b, sel):
    d = pd.DataFrame({"seq": [nseq[i] for i in sel], "diff": [float(NA[a][i]["correct"]) - float(NA[b][i]["correct"]) for i in sel]})
    cs = RB.cluster_stats(d); bs = RB.paired_cluster_bootstrap(cs, B=B, seed=SEED); lo, hi = np.percentile(bs, [2.5, 97.5])
    return {"delta": float(d["diff"].mean()), "lo": float(lo), "hi": float(hi), "n": len(d), "clusters": len(cs),
            "net_items": int(round(d["diff"].sum())), "star": bool(lo > 0 or hi < 0)}


nus = {"n": len(nids), "n_family": {f: sum(nfam[i] == f for i in nids) for f in FAMS}, "arms": {}}
for k, rows in NA.items():
    nus["arms"][k] = {"acc": float(np.mean([rows[i]["correct"] for i in nids])),
                      "parse": float(np.mean([rows[i].get("pred") is not None for i in nids])),
                      "longest_unparsed": longest_unparsed(rows),
                      "family": {f: float(np.mean([rows[i]["correct"] for i in nids if nfam[i] == f])) for f in FAMS}}
nus["contrast"] = {"ser_vs_pixel_7b": ncontrast("d0_rfdetr_7b", "pixel_7b", nids), "gt_vs_ser_7b": ncontrast("d0_gt_7b", "d0_rfdetr_7b", nids),
                   "gt_vs_ser_3b": ncontrast("d0_gt_3b", "d0_rfdetr_3b", nids)}
nus["contrast_family_7b"] = {f: ncontrast("d0_rfdetr_7b", "pixel_7b", [i for i in nids if nfam[i] == f]) for f in FAMS}
# leave-one-scene-out answer prior (no scene input)
pr = []
for i in nids:
    c = collections.Counter(nb[j]["choices"][nb[j]["answer"]] for j in nids if nseq[j] != nseq[i] and nfam[j] == nfam[i])
    o = forced(nb[i]); pr.append(max(o, key=lambda k: c[o[k]]) == nb[i]["answer"])
nus["prior_loso"] = {"acc": float(np.mean(pr)), "family": {f: float(np.mean([p for p, i in zip(pr, nids) if nfam[i] == f])) for f in FAMS}}
nus["nearest_dist_gold"] = collections.Counter(nb[i]["choices"][nb[i]["answer"]] for i in nids if nfam[i] == "nearest_dist").most_common()
out["nuscenes"] = nus

json.dump(out, open(HERE / "rev2_results.json", "w"), indent=1, default=float)

# ------------------------------------------------------------------ print
print(f"prior rule: {out['acc']['prior']:.4f}; strata {out['prior_strata']}")
print("error split:", json.dumps(out["error_split"]))
print("queried class present:", json.dumps(out["queried_present"]), out["queried_present_total"]); print("net by family:", out["net_by_family"]); print("nearest-class errors:", out["nearest_class_errors"])
hdr = ["prior", "blind_3b", "blind_7b", "pixel_3b", "pixel_7b", "scoped_3b", "scoped_7b", "ftvlm_3b", "fttext_3b", "gt_3b", "gt_7b"]
print("family        " + " ".join(f"{h[:9]:>9s}" for h in hdr))
for f in FAMS + ["all"]:
    print(f"{f:13s} " + " ".join(f"{(out['acc'][h] if f == 'all' else out['acc_family'][h][f]):9.3f}" for h in hdr))
for k, v in out["stratified"].items():
    print(k, {s: f"{c['delta']:+.4f} [{c['lo']:+.4f},{c['hi']:+.4f}]" for s, c in v.items()})
print("counting acc by gold (4 = 4+):", json.dumps(out["counting_by_gold"]))
print("counting gold rank:", out["counting_gold_rank"]); print("nearest-dist by gold:", json.dumps(out["nearest_dist_by_gold"]))
print("counting miss:", json.dumps(out["counting_miss"]))
print("\nbattery (delta [CI]  sign-flip p  LOSO cross-zero  per-seq mean  +/-):")
for k, r in out["battery"].items():
    print(f"  {k:32s} {r['delta']:+.4f} [{r['lo']:+.4f},{r['hi']:+.4f}]{'*' if r['star'] else ' '} p={r['signflip_p']:.4f} "
          f"loso0={r['loso_cross_zero']:2d}/21 mean={r['cluster_mean']:+.4f} {r['pos']}/{r['neg']}")
print("\nnuScenes:", json.dumps(nus["n_family"]))
for k, a in nus["arms"].items():
    print(f"  {k:14s} acc {a['acc']:.4f} parse {a['parse']:.3f} longest-unparsed {a['longest_unparsed']:3d} " + " ".join(f"{a['family'][f]:.3f}" for f in FAMS))
print("  contrasts:", {k: f"{c['delta']:+.4f} [{c['lo']:+.4f},{c['hi']:+.4f}] net {c['net_items']}" for k, c in nus["contrast"].items()})
print("  per-family 7B ser-pixel:", {f: f"{c['delta']:+.3f} [{c['lo']:+.3f},{c['hi']:+.3f}] net {c['net_items']:+d} (n={c['n']})" for f, c in nus["contrast_family_7b"].items()})
print("  LOSO prior:", json.dumps(nus["prior_loso"]), nus["nearest_dist_gold"])
print("small VLMs:", {k: round(out["acc"][k], 4) for k in ("scoped_0.5b", "scoped_1.5b", "moondream", "llavaphi3", "q3vl2b_direct", "q3vl2b_think", "q3txt4b", "q3vl4b", "q3txt8b", "q3vl8b", "zs3b_hf_fullres", "flat_3b", "flat_7b")})
