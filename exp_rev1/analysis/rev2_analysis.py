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
# object-list scene graphs with the sign convention of the bearing stated (control of 2026-11-15)
for name in ("sgc_triples_3b", "sgc_triples_7b", "sgc_json_3b", "sgc_json_7b"):
    ps = glob.glob(str(E / "b4c_scenegraph_convention" / name / "*forced.jsonl"))
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

# ------------------------------------------------------------------ A0. the first criterion, on the development bank
# (history reported in Section VI) 7B only: system minus VLM, bootstrap over the 21 recordings,
# lower end of the 95% interval above zero. Applied first to system v8, then to v9 (Flat).
devd = {it["qa_id"]: it for it in dev}
def dev_contrast(pa, pb):
    A_, B_ = arm_jsonl(pa), arm_jsonl(pb)
    common = [i for i in devd if i in A_ and i in B_]
    d = pd.DataFrame({"seq": [int(devd[i]["scene_name"]) for i in common], "diff": [float(A_[i]["correct"]) - float(B_[i]["correct"]) for i in common]})
    cs = RB.cluster_stats(d); bs = RB.paired_cluster_bootstrap(cs, B=B, seed=SEED); lo, hi = np.percentile(bs, [2.5, 97.5])
    return {"delta": float(d["diff"].mean()), "lo": float(lo), "hi": float(hi), "n": len(d), "star": bool(lo > 0 or hi < 0),
            "acc_a": float(np.mean([A_[i]["correct"] for i in common])), "acc_b": float(np.mean([B_[i]["correct"] for i in common]))}
fc = {}
P10 = REL / "results/phase10"
for key, a_dir in (("v8_vs_vlm_7b", "results_system8_kf_7b"), ("flat_vs_vlm_7b", "results_system9_kf_7b")):
    if glob.glob(str(P10 / a_dir / "*forced.jsonl")) and glob.glob(str(P10 / "results_qwen2.5vl_7b" / "*forced.jsonl")):
        fc[key] = dev_contrast(P10 / a_dir / "*forced.jsonl", P10 / "results_qwen2.5vl_7b" / "*forced.jsonl")
out["first_criterion"] = fc

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
for sc in ("3b", "7b"):
    for m in ("triples", "json"):
        if f"sgc_{m}_{sc}" in ARMS:
            pairs[f"sgc_{m}_vs_sg_{sc}"] = (f"sgc_{m}_{sc}", f"sg_{m}_{sc}")
            pairs[f"sgc_{m}_vs_pixelrerun_{sc}"] = (f"sgc_{m}_{sc}", f"pixel_rerun_{sc}")
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

# ------------------------------------------------------------------ E. accuracy balanced over gold answers (A6 part 3, post hoc)
# Within a family the accuracy is computed for each gold answer that has at least MINN
# questions in the bank, and these are averaged; the balanced accuracy is the mean of the
# five family values. A rule that always gives the most frequent answer of a family scores
# 1/K in that family. Paired bootstrap over the 21 recordings, B = 20000.
gold_txt = {i: cfd[i]["choices"][cfd[i]["answer"]] for i in ids}
clusters = sorted(set(seq.values()))
cidx = np.array([clusters.index(seq[i]) for i in ids])
rngE = np.random.default_rng(SEED)
WE = np.zeros((B, len(clusters)))
for b_, draw in enumerate(rngE.integers(0, len(clusters), size=(B, len(clusters)))):
    np.add.at(WE[b_], draw, 1.0)


def bal_setup(minn):
    cells = collections.Counter((fam[i], gold_txt[i]) for i in ids)
    keep = sorted(k for k, n in cells.items() if n >= minn)
    col = {k: j for j, k in enumerate(keep)}
    M = np.zeros((len(ids), len(keep)))
    for r_, i in enumerate(ids):
        j = col.get((fam[i], gold_txt[i]))
        if j is not None:
            M[r_, j] = 1.0
    Cn = np.zeros((len(clusters), len(keep)))
    np.add.at(Cn, cidx, M)
    fam_cols = {f: [j for j, k in enumerate(keep) if k[0] == f] for f in FAMS}
    return keep, M, Cn, fam_cols


def bal_value(S, N, fam_cols):
    """S, N: (..., cells) sums of correct answers and of questions -> balanced accuracy (...)."""
    with np.errstate(invalid="ignore", divide="ignore"):
        acc = np.where(N > 0, S / N, np.nan)
    return np.nanmean(np.stack([np.nanmean(acc[..., cols], axis=-1) for cols in fam_cols.values()], axis=-1), axis=-1)


def bal_arm(name, setup):
    keep, M, Cn, fam_cols = setup
    v = np.array([float(ARMS[name][i]) for i in ids])
    Cs = np.zeros_like(Cn); np.add.at(Cs, cidx, M * v[:, None])
    return float(bal_value(Cs.sum(0), Cn.sum(0), fam_cols)), bal_value(WE @ Cs, WE @ Cn, fam_cols)


bal_pairs = {"primary_3b": ("scoped_3b", "pixel_3b"), "primary_7b": ("scoped_7b", "pixel_7b"),
             "fttext_vs_ftvlm_3b": ("fttext_3b", "ftvlm_3b"), "ftvlm_vs_scoped_3b": ("ftvlm_3b", "scoped_3b"),
             "flat_vs_pixel_3b": ("flat_3b", "pixel_3b"), "flat_vs_pixel_7b": ("flat_7b", "pixel_7b"),
             "nostereo_vs_pixel_3b": ("nostereo_3b", "pixel_3b"), "nostereo_vs_pixel_7b": ("nostereo_7b", "pixel_7b"),
             "d1_vs_pixel_3b": ("d1_3b", "pixel_3b"), "d1_vs_pixel_7b": ("d1_7b", "pixel_7b"),
             "scoped1.5b_vs_q3vl2b_think": ("scoped_1.5b", "q3vl2b_think")}
for sc in ("3b", "7b"):
    if f"ctrl_scoped_{sc}" in ARMS:
        bal_pairs[f"hybrid_vs_ctrl_scoped_{sc}"] = (f"hybrid_{sc}", f"ctrl_scoped_{sc}")
        bal_pairs[f"ctrl_scoped_vs_pixelrerun_{sc}"] = (f"ctrl_scoped_{sc}", f"pixel_rerun_{sc}")
    bal_pairs[f"light1_vs_pixelrerun_{sc}"] = (f"light1_{sc}", f"pixel_rerun_{sc}")
    bal_pairs[f"rfdetr_vs_pixelrerun_{sc}"] = (f"rfdetr_{sc}", f"pixel_rerun_{sc}")
# A6 part 3 names "the pairs of Table 9 of the manuscript": add the pairs of that table that are not yet in the list
for k in ("hybrid_vs_pixelrerun_3b", "hybrid_vs_pixelrerun_7b", "scoped_vs_flat_3b", "scoped_vs_flat_7b", "ftvlm_vs_scoped_7b",
          "scoped1.5b_vs_moondream", "q3txt4b_vs_q3vl4b", "q3txt8b_vs_q3vl8b"):
    bal_pairs[k] = pairs[k]
out["balanced"] = {}
for minn in (5, 1, 10):
    setup = bal_setup(minn)
    cache = {}
    def ba(name):
        if name not in cache:
            cache[name] = bal_arm(name, setup)
        return cache[name]
    res = {"cells": {f: len(c) for f, c in setup[3].items()}, "n_in_cells": int(setup[1].sum()), "acc": {}, "contrast": {}}
    for name in ("prior", "blind_3b", "blind_7b", "pixel_3b", "pixel_7b", "scoped_3b", "scoped_7b", "flat_3b", "flat_7b",
                 "ftvlm_3b", "ftvlm_7b", "fttext_3b", "gt_3b", "gt_7b", "hybrid_3b", "hybrid_7b", "nostereo_3b", "nostereo_7b"):
        res["acc"][name] = ba(name)[0]
    for k, (a_, b_) in bal_pairs.items():
        (pa, ra), (pb, rb) = ba(a_), ba(b_)
        lo, hi = np.percentile(ra - rb, [2.5, 97.5])
        res["contrast"][k] = {"delta": pa - pb, "lo": float(lo), "hi": float(hi), "star": bool(lo > 0 or hi < 0)}
    out["balanced"][f"min{minn}"] = res


# ------------------------------------------------------------------ F. protocol R and the Transformers back end (A6 part 1)
def rows_of(pattern):
    ps = glob.glob(str(pattern))
    return {r["qa_id"]: r for r in jl(ps[0])} if ps else None


RR = {"vlmR_3b": "c3_reason/cf_vlm_3b", "vlmR_7b": "c3_reason/cf_vlm_7b", "readerR_3b": "c3_reason/cf_text_3b",
      "readerR_7b": "c3_reason/cf_text_7b", "hfpixel_3b": "c2_nusc/cf_hf_pixel_3b", "hfpixel_7b": "c2_nusc/cf_hf_pixel_7b"}
prot = {"arms": {}, "contrast": {}}
for name, d in RR.items():
    rows = rows_of(E / d / "*forced.jsonl")
    if rows is None or not set(ids) <= set(rows):
        continue
    ARMS[name] = {i: bool(rows[i]["correct"]) for i in ids}
    parsed = [rows[i].get("pred") is not None for i in ids]
    a_ = {"acc": float(np.mean([ARMS[name][i] for i in ids])), "parse": float(np.mean(parsed)), "n_unparsed": int(len(ids) - sum(parsed)),
          "acc_parsed": float(np.mean([ARMS[name][i] for i, p in zip(ids, parsed) if p])),
          "family": {f: float(np.mean([ARMS[name][i] for i in ids if fam[i] == f])) for f in FAMS},
          "parse_family": {f: float(np.mean([p for i, p in zip(ids, parsed) if fam[i] == f])) for f in FAMS}}
    if "raw" in rows[ids[0]]:
        a_["cut_at_limit"] = int(sum(rows[i].get("finish") == "length" for i in ids))
        un = [rows[i] for i in ids if rows[i].get("pred") is None]
        a_["unparsed_error"] = int(sum(r_["raw"].startswith("__ERROR__") for r_ in un))
        a_["unparsed_cut"] = int(sum(r_.get("finish") == "length" and not r_["raw"].startswith("__ERROR__") for r_ in un))
        a_["unparsed_other"] = len(un) - a_["unparsed_error"] - a_["unparsed_cut"]
        a_["median_chars"] = float(np.median([len(rows[i]["raw"]) for i in ids]))
        a_["median_latency_s"] = float(np.median([rows[i]["latency_s"] for i in ids]))
    prot["arms"][name] = a_
for sc in ("3b", "7b"):
    for key, (a_, b_) in {f"readerR_vs_vlmR_{sc}": (f"readerR_{sc}", f"vlmR_{sc}"), f"scoped_vs_vlmR_{sc}": (f"scoped_{sc}", f"vlmR_{sc}"),
                          f"vlmR_vs_vlm_{sc}": (f"vlmR_{sc}", f"pixel_{sc}"), f"readerR_vs_scoped_{sc}": (f"readerR_{sc}", f"scoped_{sc}"),
                          f"hfpixel_vs_vlm_{sc}": (f"hfpixel_{sc}", f"pixel_{sc}"), f"scoped_vs_hfpixel_{sc}": (f"scoped_{sc}", f"hfpixel_{sc}"),
                          # against the control runs on the present installation of the serving software (Section VI)
                          f"vlmR_vs_ctrlvlm_{sc}": (f"vlmR_{sc}", f"pixel_rerun_{sc}"), f"readerR_vs_ctrlscoped_{sc}": (f"readerR_{sc}", f"ctrl_scoped_{sc}"),
                          f"ctrlscoped_vs_vlmR_{sc}": (f"ctrl_scoped_{sc}", f"vlmR_{sc}")}.items():
        if a_ in ARMS and b_ in ARMS:
            prot["contrast"][key] = battery(a_, b_)
            prot["contrast"][key]["family"] = {f: contrast(a_, b_, [i for i in ids if fam[i] == f])[2] for f in FAMS}
out["protocol_r"] = prot

# ------------------------------------------------------------------ G. nuScenes, second bank (A6 part 2 and addendum 1)
n2 = {}
qa2p = REL / "exp_rev1/c2_nusc/qa_nusc2.jsonl"
if qa2p.exists():
    b2 = {r["qa_id"]: r for r in jl(qa2p)}
    ids2 = list(b2); fam2 = {i: b2[i]["category"] for i in ids2}; sc2 = {i: b2[i]["scene_name"] for i in ids2}
    meta2 = json.load(open(REL / "exp_rev1/c2_nusc/scene_meta_nusc2.json", encoding="utf-8"))
    loc2 = {i: meta2[sc2[i]]["location"] for i in ids2}
    n2 = {"n": len(ids2), "scenes": len(set(sc2.values())), "n_family": {f: sum(fam2[i] == f for i in ids2) for f in FAMS},
          "n_location": dict(collections.Counter(loc2.values())), "arms": {}, "contrast": {}}
    A2 = {}
    for name in ("s_3b", "s_7b", "sraw_3b", "sraw_7b", "gt_3b", "gt_7b", "blind_3b", "blind_7b", "pixel_ollama_7b",
                 "hf_pixel_3b", "hf_pixel_7b", "hf_hybrid_3b", "hf_hybrid_7b", "hf_reason_3b", "hf_reason_7b", "readerR_3b", "readerR_7b",
                 "d1_3b", "d1_7b", "sg_triples_3b", "sg_triples_7b"):          # the last four: amendment A8
        rows = rows_of(E / f"c2_nusc/{name}/*forced.jsonl")
        if rows is None or not set(ids2) <= set(rows):
            continue
        A2[name] = rows
        best = cur = 0
        for i in ids2:
            cur = cur + 1 if rows[i].get("pred") is None else 0
            best = max(best, cur)
        if "raw" in rows[ids2[0]]:
            n2.setdefault("cut_at_limit", {})[name] = int(sum(rows[i].get("finish") == "length" for i in ids2))
        n2["arms"][name] = {"acc": float(np.mean([rows[i]["correct"] for i in ids2])),
                            "parse": float(np.mean([rows[i].get("pred") is not None for i in ids2])), "longest_unparsed": best,
                            "family": {f: float(np.mean([rows[i]["correct"] for i in ids2 if fam2[i] == f])) for f in FAMS},
                            "location": {l: float(np.mean([rows[i]["correct"] for i in ids2 if loc2[i] == l])) for l in sorted(set(loc2.values()))}}

    def c2(a_, b_, sel=None, full=False):
        sel = sel or ids2
        d = pd.DataFrame({"seq": [sc2[i] for i in sel], "diff": [float(A2[a_][i]["correct"]) - float(A2[b_][i]["correct"]) for i in sel]})
        cs = RB.cluster_stats(d); bs = RB.paired_cluster_bootstrap(cs, B=B, seed=SEED); lo, hi = np.percentile(bs, [2.5, 97.5])
        r = {"delta": float(d["diff"].mean()), "lo": float(lo), "hi": float(hi), "n": len(d), "clusters": len(cs),
             "net_items": int(round(d["diff"].sum())), "star": bool(lo > 0 or hi < 0)}
        if full:
            sums = cs["sum"].to_numpy() if "sum" in cs else (cs["mean"] * cs["n"]).to_numpy()
            rg = np.random.default_rng(SEED)
            flips = rg.choice([-1.0, 1.0], size=(20000, len(sums))) @ sums
            r["signflip_p"] = float((np.sum(np.abs(flips) >= abs(sums.sum()) - 1e-12) + 1) / (20000 + 1))
            r["leave_location_out"] = {}
            for l in sorted(set(loc2.values())):
                keep = [i for i in sel if loc2[i] != l]
                r["leave_location_out"][l] = c2(a_, b_, keep)
            r["firm"] = bool(r["star"] and r["signflip_p"] < 0.05 and all(v["lo"] > 0 or v["hi"] < 0 for v in r["leave_location_out"].values()))
            r["family"] = {f: c2(a_, b_, [i for i in sel if fam2[i] == f]) for f in FAMS}
            r["location"] = {l: c2(a_, b_, [i for i in sel if loc2[i] == l]) for l in sorted(set(loc2.values()))}
            for word in ("night", "rain"):
                w = [i for i in sel if word in meta2[sc2[i]]["description"].lower()]
                r[word] = c2(a_, b_, w) if w else None
        return r

    for key, (a_, b_, full) in {"E1_s_vs_vlm_3b": ("s_3b", "hf_pixel_3b", True), "E2_s_vs_vlm_7b": ("s_7b", "hf_pixel_7b", True),
                                "s_vs_ollama_vlm_7b": ("s_7b", "pixel_ollama_7b", True),
                                "sraw_vs_vlm_3b": ("sraw_3b", "hf_pixel_3b", False), "sraw_vs_vlm_7b": ("sraw_7b", "hf_pixel_7b", False),
                                "s_vs_sraw_3b": ("s_3b", "sraw_3b", False), "s_vs_sraw_7b": ("s_7b", "sraw_7b", False),
                                "gt_vs_s_3b": ("gt_3b", "s_3b", False), "gt_vs_s_7b": ("gt_7b", "s_7b", False),
                                "gt_vs_vlm_3b": ("gt_3b", "hf_pixel_3b", False), "gt_vs_vlm_7b": ("gt_7b", "hf_pixel_7b", False),
                                "hybrid_vs_s_3b": ("hf_hybrid_3b", "s_3b", False), "hybrid_vs_s_7b": ("hf_hybrid_7b", "s_7b", False),
                                "hybrid_vs_vlm_3b": ("hf_hybrid_3b", "hf_pixel_3b", False), "hybrid_vs_vlm_7b": ("hf_hybrid_7b", "hf_pixel_7b", False),
                                "hf_vs_ollama_vlm_7b": ("hf_pixel_7b", "pixel_ollama_7b", False), "vlm_7b_vs_3b": ("hf_pixel_7b", "hf_pixel_3b", False),
                                "s_vs_vlmR_3b": ("s_3b", "hf_reason_3b", False), "s_vs_vlmR_7b": ("s_7b", "hf_reason_7b", False),
                                "readerR_vs_vlmR_3b": ("readerR_3b", "hf_reason_3b", False), "readerR_vs_vlmR_7b": ("readerR_7b", "hf_reason_7b", False),
                                "vlmR_vs_vlm_3b": ("hf_reason_3b", "hf_pixel_3b", False), "vlmR_vs_vlm_7b": ("hf_reason_7b", "hf_pixel_7b", False),
                                "readerR_vs_s_3b": ("readerR_3b", "s_3b", False), "readerR_vs_s_7b": ("readerR_7b", "s_7b", False),
                                # amendment A8: two less answer-aligned texts on this bank (exploratory)
                                "d1_vs_vlm_3b": ("d1_3b", "hf_pixel_3b", True), "d1_vs_vlm_7b": ("d1_7b", "hf_pixel_7b", True),
                                "d1_vs_s_3b": ("d1_3b", "s_3b", True), "d1_vs_s_7b": ("d1_7b", "s_7b", True),
                                "sg_vs_vlm_3b": ("sg_triples_3b", "hf_pixel_3b", True), "sg_vs_vlm_7b": ("sg_triples_7b", "hf_pixel_7b", True),
                                "sg_vs_s_3b": ("sg_triples_3b", "s_3b", True), "sg_vs_s_7b": ("sg_triples_7b", "s_7b", True)}.items():
        if a_ in A2 and b_ in A2:
            n2["contrast"][key] = c2(a_, b_, full=full)
    # nearest-distance: does an arm choose a nearer or a farther band than the correct one?
    band_rank = {"under 5 meters away": 0, "5 to 15 meters away": 1, "over 15 meters away": 2}
    n2["band_bias"] = {}
    for name in ("hf_pixel_3b", "hf_pixel_7b", "s_3b", "s_7b"):
        if name not in A2:
            continue
        near_ = far_ = tot_ = 0
        for i in ids2:
            if fam2[i] != "nearest_dist":
                continue
            texts = [v for k_, v in sorted(b2[i]["choices"].items()) if k_ != b2[i]["abstain_letter"]]
            pred = A2[name][i].get("pred"); tot_ += 1
            if pred is None:
                continue
            d_ = band_rank[texts["ABC".index(pred)]] - band_rank[b2[i]["choices"][b2[i]["answer"]]]
            near_ += d_ < 0; far_ += d_ > 0
        n2["band_bias"][name] = {"n": tot_, "nearer": int(near_), "farther": int(far_)}
    # a rule that also looks at the option set, learned on the other scenes (5 folds over scenes)
    scn_sorted = sorted(set(sc2.values())); fold_of = {s_: k_ % 5 for k_, s_ in enumerate(scn_sorted)}
    def okey(i):
        return (fam2[i], tuple(sorted(forced(b2[i]).values())))
    hit = []
    for fo in range(5):
        tr = [i for i in ids2 if fold_of[sc2[i]] != fo]
        by_set = collections.defaultdict(collections.Counter); by_fam = collections.defaultdict(collections.Counter)
        for i in tr:
            g_ = b2[i]["choices"][b2[i]["answer"]]; by_set[okey(i)][g_] += 1; by_fam[fam2[i]][g_] += 1
        for i in ids2:
            if fold_of[sc2[i]] != fo:
                continue
            o = forced(b2[i]); c_ = by_set.get(okey(i)) or by_fam[fam2[i]]
            hit.append((i, max(sorted(o), key=lambda k_: (c_[o[k_]], by_fam[fam2[i]][o[k_]])) == b2[i]["answer"]))
    hd = dict(hit)
    n2["prior_optionset_cv"] = {"acc": float(np.mean([hd[i] for i in ids2])), "family": {f: float(np.mean([hd[i] for i in ids2 if fam2[i] == f])) for f in FAMS}}
    # answer-prior rule: answer frequencies of the mini bank, applied to the new bank
    c1cnt = collections.defaultdict(collections.Counter)
    for j in nids:
        c1cnt[nfam[j]][nb[j]["choices"][nb[j]["answer"]]] += 1
    pr2 = {}
    for i in ids2:
        o = forced(b2[i]); pr2[i] = max(sorted(o), key=lambda k: c1cnt[fam2[i]][o[k]]) == b2[i]["answer"]
    n2["prior_from_mini"] = {"acc": float(np.mean(list(pr2.values()))), "family": {f: float(np.mean([pr2[i] for i in ids2 if fam2[i] == f])) for f in FAMS}}
    n2["night_rain"] = {w: {"questions": sum(w in meta2[sc2[i]]["description"].lower() for i in ids2),
                            "scenes": len({sc2[i] for i in ids2 if w in meta2[sc2[i]]["description"].lower()})} for w in ("night", "rain")}
    # the first check (v1.0-mini) with the corrected camera constant
    fixm = {}
    for name in ("fix_d0_rfdetr_3b", "fix_d0_rfdetr_7b", "fix_d0_gt_3b", "fix_d0_gt_7b"):
        rows = rows_of(E / f"c1_nusc/{name}/*forced.jsonl")
        if rows is not None and set(nids) <= set(rows):
            NA[name] = rows
            fixm[name] = {"acc": float(np.mean([rows[i]["correct"] for i in nids])),
                          "family": {f: float(np.mean([rows[i]["correct"] for i in nids if nfam[i] == f])) for f in FAMS}}
    if "fix_d0_rfdetr_7b" in NA:
        fixm["contrast"] = {"fix_vs_pixel_7b": ncontrast("fix_d0_rfdetr_7b", "pixel_7b", nids), "fix_vs_first_7b": ncontrast("fix_d0_rfdetr_7b", "d0_rfdetr_7b", nids),
                            "fix_vs_first_3b": ncontrast("fix_d0_rfdetr_3b", "d0_rfdetr_3b", nids),
                            "family_fix_vs_pixel_7b": {f: ncontrast("fix_d0_rfdetr_7b", "pixel_7b", [i for i in nids if nfam[i] == f]) for f in FAMS}}
    n2["mini_fixed"] = fixm
out["nuscenes2"] = n2

# ------------------------------------------------------------------ H. nearest-distance family: answer key and choices
# (added after a simulated review, 2026-11-15) The key is the band of the ground distance from the
# sensor to the CENTER of the box. key_audit.py recomputed the distance to the NEAREST POINT of the
# box footprint; questions whose band differs between the two definitions are left out here.
BANDS3 = ["under 5 meters away", "5 to 15 meters away", "over 15 meters away"]


def nd_choices(bank, order, famof, rows):
    """what an arm chooses in the nearest-distance family: by band and by option letter"""
    band_c = collections.Counter(); letter_c = collections.Counter(); gold_c = collections.Counter(); goldletter_c = collections.Counter()
    for i in order:
        if famof[i] != "nearest_dist":
            continue
        it = bank[i]
        texts = [v for k_, v in sorted(it["choices"].items()) if k_ != it.get("abstain_letter")]
        gold_c[it["choices"][it["answer"]]] += 1; goldletter_c["ABC"[texts.index(it["choices"][it["answer"]])]] += 1
        pred = rows[i].get("pred")
        if pred is None:
            band_c["none"] += 1; letter_c["none"] += 1
        else:
            band_c[texts["ABC".index(pred)]] += 1; letter_c[pred] += 1
    return {"chosen_band": {b_: band_c.get(b_, 0) for b_ in BANDS3 + ["none"]}, "chosen_letter": {l_: letter_c.get(l_, 0) for l_ in ("A", "B", "C", "none")},
            "gold_band": {b_: gold_c.get(b_, 0) for b_ in BANDS3}, "gold_letter": {l_: goldletter_c.get(l_, 0) for l_ in ("A", "B", "C")}}


ka = {}
kp = REL / "exp_rev1/key_audit/nearest_dist_key_audit.jsonl"
if kp.exists():
    rowsK = jl(kp)
    for bname in ("confirm", "nusc2"):
        rs = [r for r in rowsK if r["bank"] == bname]
        ka[bname] = {"n": len(rs), "key_is_center_band": int(sum(r["gold"] == r["band_center"] for r in rs)),
                     "band_changes": int(sum(r["band_center"] != r["band_nearest"] for r in rs)),
                     "median_gap_m": float(np.median([r["d_center"] - r["d_nearest"] for r in rs]))}
    amb = {r["qa_id"] for r in rowsK if r["band_center"] != r["band_nearest"]}
    keep = [i for i in ids if i not in amb]
    ka["confirm"]["n_kept"] = len(keep)
    for sc in ("3b", "7b"):
        ka["confirm"][f"primary_{sc}"] = contrast(f"scoped_{sc}", f"pixel_{sc}", keep)[2]
        ka["confirm"][f"nd_{sc}"] = contrast(f"scoped_{sc}", f"pixel_{sc}", [i for i in keep if fam[i] == "nearest_dist"])[2]
    if n2:
        keep2 = [i for i in ids2 if i not in amb]
        ka["nusc2"]["n_kept"] = len(keep2)
        for sc, key_ in (("3b", "E1"), ("7b", "E2")):
            ka["nusc2"][f"{key_}_{sc}"] = c2(f"s_{sc}", f"hf_pixel_{sc}", keep2)
            ka["nusc2"][f"nd_{sc}"] = c2(f"s_{sc}", f"hf_pixel_{sc}", [i for i in keep2 if fam2[i] == "nearest_dist"])
            # the difference without the nearest-distance family
            ka["nusc2"][f"without_nd_{sc}"] = c2(f"s_{sc}", f"hf_pixel_{sc}", [i for i in ids2 if fam2[i] != "nearest_dist"])
    for sc in ("3b", "7b"):
        ka["confirm"][f"without_nd_{sc}"] = contrast(f"scoped_{sc}", f"pixel_{sc}", [i for i in ids if fam[i] != "nearest_dist"])[2]
out["key_audit"] = ka
ndc = {"confirm": {}, "nusc2": {}}
for name, rel_ in (("pixel_3b", "results/phase10/results_cf_px3b_robust"), ("pixel_7b", "results/phase10/results_cf_px_7b"),
                   ("scoped_3b", "results/phase10/results_cf_v15_3b"), ("scoped_7b", "results/phase10/results_cf_v15_7b")):
    ndc["confirm"][name] = nd_choices(cfd, ids, fam, arm_jsonl(REL / rel_ / "*forced.jsonl"))
if n2:
    for name in ("hf_pixel_3b", "hf_pixel_7b", "s_3b", "s_7b", "blind_3b", "blind_7b"):
        if name in A2:
            ndc["nusc2"][name] = nd_choices(b2, ids2, fam2, A2[name])
out["nd_choices"] = ndc

# ------------------------------------------------------------------ I. the confirmatory bank on the board (amendment A7)
# Source: exp_rev1/b10_boards/orin_nano_fullbank/ (copy of ~/rev1/out_e2e_full1328 on the board,
# written by scripts/rev1/run_b10_orin_fullbank.sh). An arm enters only when all 1328 answers exist.
OBD = E / "b10_boards/orin_nano_fullbank"
OB_ARMS = {"s_3b": "full-qwen2.5-3b", "s_1.5b": "full-qwen2.5-1.5b", "s_7b": "full-qwen2.5-7b",
           "vlm_lr": "full-qwen2.5vl-3b-lr", "vlm_full": "full-qwen2.5vl-3b",
           "hyb_lr": "full-hyb-qwen2.5vl-3b-lr"}          # A7 addendum 1 (exploratory)
OB_LAPTOP = {"s_3b": E / "b5_light/infer/cf_d0_light1_3b/*forced.jsonl", "s_7b": E / "b5_light/infer/cf_d0_light1_7b/*forced.jsonl",
             "vlm_full": REL / "results/phase10/results_cf_px3b_robust/*forced.jsonl"}
# amendments/A7_addendum2.md and A7_addendum3.md: a server that has failed returns this string for
# every question. It is not an answer. The failed questions take the answers of the run with the
# reload rule (<dir>-guard: the server is restarted after a degenerate output and the question is
# asked once more; a question that fails again counts as wrong). An arm with failed answers and
# no such run is not used.
OB_FAIL = "????????"
ob = {"arms": {}, "contrast": {}, "balanced_min5": {}, "first_process": {}}
OB_FIRST = {}
for name, d in OB_ARMS.items():
    pth = OBD / d / "items.jsonl"
    if not pth.exists():
        continue
    order = [r["qa_id"] for r in jl(pth)]
    rows = {r["qa_id"]: r for r in jl(pth)}
    if set(rows) != set(ids):
        ob["arms"][name] = {"incomplete": len(rows)}
        continue
    sm = json.load(open(OBD / d / "summary.json", encoding="utf-8"))
    watt = {i: sm["power_run_mw"]["VDD_IN"] / 1000 for i in ids}
    failed = [i for i in order if rows[i]["raw"] == OB_FAIL]
    fail = None
    if failed:
        rp = OBD / (d + "-guard")
        if not (rp / "items.jsonl").exists():
            ob["arms"][name] = {"failed_answers": len(failed), "repeat_run": "pending"}
            continue
        rr = {r["qa_id"]: r for r in jl(rp / "items.jsonl")}
        rsm = json.load(open(rp / "summary.json", encoding="utf-8"))
        first = order.index(failed[0])
        assert failed == order[first:], name                       # the failure runs from one question to the end
        overlap = [i for i in order if i in rr and i not in set(failed)]
        assert set(failed) <= set(rr) and overlap == order[first - len(overlap):first], name   # the questions just before the failure
        again = [i for i in failed if rr[i]["degenerate"]]         # failed again after a restart: these count as wrong
        assert all(rr[i]["pred"] is None and not rr[i]["correct"] for i in again), name
        assert not any(rr[i]["degenerate"] for i in overlap), name
        ok = order[:first]
        fail = {"n_failed": len(failed), "n_first": first, "repeat_n": len(rr), "overlap_n": len(overlap),
                "overlap_same_answer": int(sum(rr[i]["pred"] == rows[i]["pred"] for i in overlap)),
                "overlap_acc_first": float(np.mean([rows[i]["correct"] for i in overlap])),
                "overlap_acc_repeat": float(np.mean([rr[i]["correct"] for i in overlap])),
                "first_acc": float(np.mean([rows[i]["correct"] for i in ok])),
                "first_time_mean_s": float(np.mean([rows[i]["latency_s"] for i in ok])),
                "failed_time_mean_s": float(np.mean([rows[i]["latency_s"] for i in failed])),
                "repeat_acc_failed": float(np.mean([rr[i]["correct"] for i in failed])),
                "repeat_time_mean_s": float(np.mean([rr[i]["latency_s"] for i in rr])),
                "first_power_w": sm["power_run_mw"]["VDD_IN"] / 1000, "repeat_power_w": rsm["power_run_mw"]["VDD_IN"] / 1000,
                "acc_failed_counted_wrong": float(np.mean([rows[i]["correct"] for i in ids])),
                "still_failed": again, "restarts": int(rsm["restarts"]), "asked_twice": int(sum(rr[i]["attempts"] == 2 for i in rr)),
                "overlap_same_correct": int(sum(bool(rr[i]["correct"]) == bool(rows[i]["correct"]) for i in overlap)),
                "first_recordings": sorted({seq[i] for i in ok}), "failed_recordings": sorted({seq[i] for i in failed})}
        OB_FIRST[name] = ok
        for i in failed:
            rows[i] = rr[i]; watt[i] = rsm["power_run_mw"]["VDD_IN"] / 1000
    ARMS["ob_" + name] = {i: bool(rows[i]["correct"]) for i in ids}
    w = float(np.mean([watt[i] for i in ids]))
    lat = np.array([rows[i]["latency_s"] for i in ids])
    a = {"n": len(ids), "acc": float(np.mean([rows[i]["correct"] for i in ids])),
         "parse": float(np.mean([rows[i]["pred"] is not None for i in ids])),
         "family": {f: float(np.mean([rows[i]["correct"] for i in ids if fam[i] == f])) for f in FAMS},
         "time_mean_s": float(lat.mean()), "time_median_s": float(np.median(lat)), "time_p95_s": float(np.percentile(lat, 95)),
         "time_max_s": float(lat.max()), "power_w": w, "energy_j": float(np.mean([watt[i] * rows[i]["latency_s"] for i in ids])),
         "prompt_tokens_median": float(np.median([rows[i]["prompt_tokens"] for i in ids])),
         "peak_sys_used_mb": sm.get("peak_sys_used_mb"), "load_status": sm.get("load_status"), "oom": sm.get("oom_in_journal")}
    if fail is None:
        assert abs(a["acc"] - sm["acc"]) < 1e-9 and abs(a["time_mean_s"] - sm["latency_mean_s"]) < 1e-6, name
        assert abs(a["energy_j"] - w * a["time_mean_s"]) < 1e-9, name
    else:
        a["fail"] = fail
    if name in OB_LAPTOP:
        lp = arm_jsonl(OB_LAPTOP[name])
        same = [i for i in ids if rows[i]["pred"] == lp[i].get("pred")]
        assert all(bool(rows[i]["correct"]) == bool(lp[i]["correct"]) for i in same if rows[i]["pred"] is not None), name   # same key on board and laptop
        a["agree_laptop"] = len(same); a["laptop_acc"] = float(np.mean([bool(lp[i]["correct"]) for i in ids]))
    ob["arms"][name] = a
OB_PAIRS = {"O1_s3b_vs_vlm_lr": ("ob_s_3b", "ob_vlm_lr"), "O2_s3b_vs_vlm_full": ("ob_s_3b", "ob_vlm_full"),
            "s1.5b_vs_vlm_lr": ("ob_s_1.5b", "ob_vlm_lr"), "s1.5b_vs_vlm_full": ("ob_s_1.5b", "ob_vlm_full"),
            "s7b_vs_vlm_lr": ("ob_s_7b", "ob_vlm_lr"), "s7b_vs_vlm_full": ("ob_s_7b", "ob_vlm_full"),
            "vlm_lr_vs_vlm_full": ("ob_vlm_lr", "ob_vlm_full"),
            "hyb_lr_vs_s3b": ("ob_hyb_lr", "ob_s_3b"), "hyb_lr_vs_vlm_lr": ("ob_hyb_lr", "ob_vlm_lr"), "hyb_lr_vs_vlm_full": ("ob_hyb_lr", "ob_vlm_full"),
            "hyb_lr_vs_s7b": ("ob_hyb_lr", "ob_s_7b"), "s3b_vs_s1.5b": ("ob_s_3b", "ob_s_1.5b"), "s7b_vs_s3b": ("ob_s_7b", "ob_s_3b"),
            "s3b_board_vs_laptop": ("ob_s_3b", "light1_3b"), "s7b_board_vs_laptop": ("ob_s_7b", "light1_7b"),
            "vlm_full_board_vs_laptop": ("ob_vlm_full", "pixel_3b"), "vlm_lr_vs_laptop_vlm": ("ob_vlm_lr", "pixel_3b")}
_setup5 = bal_setup(5)
for k, (a_, b_) in OB_PAIRS.items():
    if a_ in ARMS and b_ in ARMS:
        r = battery(a_, b_)
        r["firm"] = bool(r["star"] and r["signflip_p"] < 0.05 and r["loso_cross_zero"] == 0)
        r["family"] = {f: contrast(a_, b_, [i for i in ids if fam[i] == f])[2] for f in FAMS}
        ob["contrast"][k] = r
        (pa, ra), (pb, rb) = bal_arm(a_, _setup5), bal_arm(b_, _setup5)
        lo, hi = np.percentile(ra - rb, [2.5, 97.5])
        ob["balanced_min5"][k] = {"a": pa, "b": pb, "delta": pa - pb, "lo": float(lo), "hi": float(hi), "star": bool(lo > 0 or hi < 0)}
# the comparisons with a repaired arm, on the questions that its first process answered (addendum 2, rule 5)
for name, ok in OB_FIRST.items():
    for k, (a_, b_) in OB_PAIRS.items():
        if "ob_" + name in (a_, b_) and a_ in ARMS and b_ in ARMS:
            ob["first_process"][k] = contrast(a_, b_, ok)[2]
            ob["first_process"][k]["acc_a"] = float(np.mean([ARMS[a_][i] for i in ok])); ob["first_process"][k]["acc_b"] = float(np.mean([ARMS[b_][i] for i in ok]))
pp = OBD / "fullbank_perception.json"
if pp.exists():
    fp = json.load(open(pp, encoding="utf-8"))
    ob["perception"] = {"n_frames": fp["n_frames"], "wall_s": fp["wall_s"], "n_folds": fp["n_folds"], "loop_s": fp.get("loop_s"),
                        "power_w": fp["whole"]["vdd_in_mean_mw"] / 1000, "min_avail_gb": fp["whole"]["min_avail_kb"] * 1024 / 1e9}
out["onboard"] = ob

json.dump(out, open(HERE / "rev2_results.json", "w"), indent=1, default=float)

# ------------------------------------------------------------------ print
print(f"prior rule: {out['acc']['prior']:.4f}; strata {out['prior_strata']}")
print("on board:", {k: (round(a["acc"], 4), round(a["time_mean_s"], 2), a.get("agree_laptop")) if "acc" in a else a for k, a in out["onboard"]["arms"].items()})
for k, r in out["onboard"]["contrast"].items():
    print(f"  {k:26s} {r['delta']:+.4f} [{r['lo']:+.4f},{r['hi']:+.4f}]{'*' if r['star'] else ' '} p={r['signflip_p']:.4f} loso0={r['loso_cross_zero']:2d}/21 firm={r['firm']}  balanced {out['onboard']['balanced_min5'][k]['delta']:+.4f} [{out['onboard']['balanced_min5'][k]['lo']:+.4f},{out['onboard']['balanced_min5'][k]['hi']:+.4f}]")
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
