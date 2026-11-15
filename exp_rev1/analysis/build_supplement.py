#!/usr/bin/env python3
"""Build supplement.tex (Tables S1-S9, Sections S3 and S10) for the resubmission.

Computed here from the released files: Table S1 (parse rates), Table S2 (every contrast
with its interval, and per-family contrasts), parts of Section S3, Table S8 (Orin details),
Table S9 (nuScenes). Tables S4-S7 repeat tables of the previous version whose values come
from the files named in their captions.
  python analysis/build_supplement.py && pdflatex supplement.tex (twice)
"""
import glob, json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
REL = Path(__file__).resolve().parents[2]  # repository root
LV = REL
E = LV / "exp_rev1"
R = json.load(open(HERE / "rev2_results.json", encoding="utf-8"))
O = json.load(open(HERE / "b10_e2e_numbers.json", encoding="utf-8"))
PC = json.load(open(REL / "analysis/paper1_controls.json", encoding="utf-8"))
B, N = R["battery"], R["nuscenes"]
FAMS = ["counting", "direction", "nearest_class", "nearest_dist", "path_object"]
FN = {"counting": "counting", "direction": "direction", "nearest_class": "nearest-class", "nearest_dist": "nearest-distance", "path_object": "path-object"}
cf_order = [json.loads(l)["qa_id"] for l in open(REL / "banks/qa_confirm.jsonl", encoding="utf-8")]


def sgn(x, star=False):
    return f"${x:+.4f}" + ("^{*}$" if star else "$")


def ci(r):
    return f"$[{r['lo']:+.4f},\\,{r['hi']:+.4f}]$"


# ------------------------------------------------------------------ S1 parse rates
P10, X1, X2, X3 = REL / "results/phase10", REL / "results/exp1_infer", REL / "results/exp2_infer", REL / "results/exp3_infer"
ARMS = [
    ("\\textsc{Scoped}, 3B reader (primary)", P10 / "results_cf_v15_3b"), ("\\textsc{Scoped}, 7B reader (primary)", P10 / "results_cf_v15_7b"),
    ("VLM Qwen2.5-VL 3B (primary; run with the reload rule)", P10 / "results_cf_px3b_robust"), ("VLM Qwen2.5-VL 7B (primary)", P10 / "results_cf_px_7b"),
    ("VLM Qwen2.5-VL 3B, first run (serving fault; not used)", P10 / "results_cf_px_3b"),
    ("\\textsc{Flat}, 3B", P10 / "results_cf_v9_3b"), ("\\textsc{Flat}, 7B", P10 / "results_cf_v9_7b"),
    ("ground-truth objects, 3B", P10 / "results_cf_gt_3b"), ("ground-truth objects, 7B", P10 / "results_cf_gt_7b"),
    ("\\textsc{Scoped}, 0.5B reader", X2 / "cf_d0_0.5b"), ("\\textsc{Scoped}, 1.5B reader", X2 / "cf_d0_1.5b"),
    ("D1, 3B", X1 / "cf_d1_3b"), ("D1, 7B", X1 / "cf_d1_7b"), ("D2, 3B", X1 / "cf_d2_3b"), ("D2, 7B", X1 / "cf_d2_7b"),
    ("D3, 3B", X1 / "cf_d3_3b"), ("D3, 7B", X1 / "cf_d3_7b"),
    ("VLM moondream", X2 / "px_moondream_cf"), ("VLM llava-phi3", X2 / "px_llava-phi3_cf"),
    ("VLM Qwen3-VL 2B, 256 tokens", X2 / "px_q3vl2b_cf"), ("VLM Qwen3-VL 2B, 1,024 tokens", X3 / "px_q3vl2b_cf_t1024"),
    ("Qwen3 4B reader on \\textsc{Scoped}", X3 / "qwen3_4b_d0_cf"), ("VLM Qwen3-VL 4B", X3 / "qwen3vl_4b_cf"),
    ("Qwen3 8B reader on \\textsc{Scoped}", X3 / "qwen3_8b_d0_cf"), ("VLM Qwen3-VL 8B", X3 / "qwen3vl_8b_cf"),
    ("reader without scene, 3B", X3 / "blind_cf_3b"), ("reader without scene, 7B", X3 / "blind_cf_7b"),
    ("FT-VLM 3B", X3 / "ft3b_lowres_cf"), ("FT-VLM 7B", X3 / "ft7b_lowres_cf"), ("FT-Text 3B", X3 / "fttext3b_cf"),
    ("VLM 3B, reference implementation, full resolution", X3 / "zs3b_fullres_hf_cf"), ("VLM 3B, reference implementation, reduced resolution", X3 / "zs3b_lowres_cf"),
    ("VLM 3B, control run", E / "b123_vlm_aids/pixel_3b"), ("VLM 7B, control run", E / "b123_vlm_aids/pixel_7b"),
    ("VLM 3B + second image", E / "b123_vlm_aids/stereo_3b"), ("VLM 7B + second image", E / "b123_vlm_aids/stereo_7b"),
    ("VLM 3B + vocabulary in prompt", E / "b123_vlm_aids/taskinfo_3b"), ("VLM 7B + vocabulary in prompt", E / "b123_vlm_aids/taskinfo_7b"),
    ("VLM 3B + \\textsc{Scoped} text", E / "b123_vlm_aids/hybrid_3b"), ("VLM 7B + \\textsc{Scoped} text", E / "b123_vlm_aids/hybrid_7b"),
    ("\\textsc{Scoped}, 3B, control run", E / "ctrl_text/d0_3b"), ("\\textsc{Scoped}, 7B, control run", E / "ctrl_text/d0_7b"),
    ("object list as triples, 3B", E / "b4_scenegraph/sg_triples_3b"), ("object list as triples, 7B", E / "b4_scenegraph/sg_triples_7b"),
    ("object list as JSON, 3B", E / "b4_scenegraph/sg_json_3b"), ("object list as JSON, 7B", E / "b4_scenegraph/sg_json_7b"),
    ("\\textsc{Scoped} content as triples, 3B", E / "b4b_scenegraph_aligned/sga_triples_3b"), ("\\textsc{Scoped} content as triples, 7B", E / "b4b_scenegraph_aligned/sga_triples_7b"),
    ("\\textsc{Scoped} content as JSON, 3B", E / "b4b_scenegraph_aligned/sga_json_3b"), ("\\textsc{Scoped} content as JSON, 7B", E / "b4b_scenegraph_aligned/sga_json_7b"),
    ("one-pass detector pair, 3B", E / "b5_light/infer/cf_d0_light1_3b"), ("one-pass detector pair, 7B", E / "b5_light/infer/cf_d0_light1_7b"),
    ("detector pair and stereo, 3B", E / "b5_light/infer/cf_d0_light2_3b"), ("detector pair and stereo, 7B", E / "b5_light/infer/cf_d0_light2_7b"),
    ("no depth network, no stereo, 3B", E / "b5_light/infer/cf_d0_light3_3b"), ("no depth network, no stereo, 7B", E / "b5_light/infer/cf_d0_light3_7b"),
    ("RF-DETR stack, 3B", E / "b6_rfdetr/infer/cf_d0_rfdetr_3b"), ("RF-DETR stack, 7B", E / "b6_rfdetr/infer/cf_d0_rfdetr_7b"),
]


def health(d):
    ps = glob.glob(str(d / "*forced.jsonl"))
    if not ps:
        return None
    rows = {}
    for l in open(ps[0], encoding="utf-8"):
        try:
            r = json.loads(l)
        except json.JSONDecodeError:
            continue
        rows[r["qa_id"]] = r
    if not set(cf_order) <= set(rows):
        return None
    seq = [rows[q] for q in cf_order]
    best = cur = 0
    for r in seq:
        cur = cur + 1 if r.get("pred") is None else 0
        best = max(best, cur)
    return sum(bool(r["correct"]) for r in seq) / len(seq), sum(r.get("pred") is not None for r in seq) / len(seq), best


s1 = []
for name, d in ARMS:
    h = health(d)
    if h is None:
        print("S1: no complete log for", name, d); continue
    s1.append(f"{name} & {h[0]:.4f} & {h[1]:.4f} & {h[2]} \\\\")

# ------------------------------------------------------------------ S2 contrasts
LAB = [("primary_3b", "\\textsc{Scoped} $-$ VLM, 3B (primary; interval of the first script $[+0.0403,\\,+0.0996]$)"), ("primary_7b", "\\textsc{Scoped} $-$ VLM, 7B (primary; interval of the first script $[+0.0073,\\,+0.0690]$)"),
       ("scoped_vs_flat_3b", "\\textsc{Scoped} $-$ \\textsc{Flat}, 3B"), ("scoped_vs_flat_7b", "\\textsc{Scoped} $-$ \\textsc{Flat}, 7B"),
       ("flat_vs_pixel_3b", "\\textsc{Flat} $-$ VLM, 3B"), ("flat_vs_pixel_7b", "\\textsc{Flat} $-$ VLM, 7B"),
       ("nostereo_vs_pixel_3b", "stereo cue off $-$ VLM, 3B"), ("nostereo_vs_pixel_7b", "stereo cue off $-$ VLM, 7B"),
       ("stereo_cue_3b", "\\textsc{Scoped} $-$ stereo cue off, 3B"), ("stereo_cue_7b", "\\textsc{Scoped} $-$ stereo cue off, 7B"),
       ("q3txt4b_vs_q3vl4b", "Qwen3 4B reader $-$ Qwen3-VL 4B"), ("q3txt8b_vs_q3vl8b", "Qwen3 8B reader $-$ Qwen3-VL 8B"),
       ("pixelrerun_vs_archived_3b", "VLM control run $-$ archived run, 3B"), ("pixelrerun_vs_archived_7b", "VLM control run $-$ archived run, 7B"),
       ("ctrl_vs_archived_scoped_3b", "\\textsc{Scoped} control run $-$ archived run, 3B"), ("ctrl_vs_archived_scoped_7b", "\\textsc{Scoped} control run $-$ archived run, 7B"),
       ("ctrl_scoped_vs_pixelrerun_3b", "\\textsc{Scoped} control $-$ VLM control, 3B"), ("ctrl_scoped_vs_pixelrerun_7b", "\\textsc{Scoped} control $-$ VLM control, 7B"),
       ("stereo2_vs_pixelrerun_3b", "VLM + second image $-$ VLM, 3B"), ("stereo2_vs_pixelrerun_7b", "VLM + second image $-$ VLM, 7B"),
       ("taskinfo_vs_pixelrerun_3b", "VLM + vocabulary $-$ VLM, 3B"), ("taskinfo_vs_pixelrerun_7b", "VLM + vocabulary $-$ VLM, 7B"),
       ("hybrid_vs_pixelrerun_3b", "VLM + text $-$ VLM, 3B"), ("hybrid_vs_pixelrerun_7b", "VLM + text $-$ VLM, 7B"),
       ("stereo2_vs_ctrl_scoped_3b", "VLM + second image $-$ \\textsc{Scoped}, 3B"), ("stereo2_vs_ctrl_scoped_7b", "VLM + second image $-$ \\textsc{Scoped}, 7B"),
       ("taskinfo_vs_ctrl_scoped_3b", "VLM + vocabulary $-$ \\textsc{Scoped}, 3B"), ("taskinfo_vs_ctrl_scoped_7b", "VLM + vocabulary $-$ \\textsc{Scoped}, 7B"),
       ("hybrid_vs_ctrl_scoped_3b", "VLM + text $-$ \\textsc{Scoped}, 3B"), ("hybrid_vs_ctrl_scoped_7b", "VLM + text $-$ \\textsc{Scoped}, 7B"),
       ("d1_vs_scoped_3b", "D1 $-$ \\textsc{Scoped}, 3B"), ("d1_vs_scoped_7b", "D1 $-$ \\textsc{Scoped}, 7B"),
       ("d2_vs_scoped_3b", "D2 $-$ \\textsc{Scoped}, 3B"), ("d2_vs_scoped_7b", "D2 $-$ \\textsc{Scoped}, 7B"),
       ("d3_vs_scoped_3b", "D3 $-$ \\textsc{Scoped}, 3B"), ("d3_vs_scoped_7b", "D3 $-$ \\textsc{Scoped}, 7B"),
       ("d2_vs_d1_3b", "D2 $-$ D1, 3B"), ("d2_vs_d1_7b", "D2 $-$ D1, 7B"), ("d1_vs_pixel_3b", "D1 $-$ VLM, 3B"), ("d1_vs_pixel_7b", "D1 $-$ VLM, 7B"),
       ("sg_triples_vs_ctrl_scoped_3b", "object list as triples $-$ \\textsc{Scoped}, 3B"), ("sg_triples_vs_ctrl_scoped_7b", "object list as triples $-$ \\textsc{Scoped}, 7B"),
       ("sg_json_vs_ctrl_scoped_3b", "object list as JSON $-$ \\textsc{Scoped}, 3B"), ("sg_json_vs_ctrl_scoped_7b", "object list as JSON $-$ \\textsc{Scoped}, 7B"),
       ("sg_triples_vs_pixelrerun_3b", "object list as triples $-$ VLM, 3B"), ("sg_triples_vs_pixelrerun_7b", "object list as triples $-$ VLM, 7B"),
       ("sg_json_vs_pixelrerun_3b", "object list as JSON $-$ VLM, 3B"), ("sg_json_vs_pixelrerun_7b", "object list as JSON $-$ VLM, 7B"),
       ("sga_triples_vs_ctrl_scoped_3b", "\\textsc{Scoped} content as triples $-$ \\textsc{Scoped}, 3B"), ("sga_triples_vs_ctrl_scoped_7b", "\\textsc{Scoped} content as triples $-$ \\textsc{Scoped}, 7B"),
       ("sga_json_vs_ctrl_scoped_3b", "\\textsc{Scoped} content as JSON $-$ \\textsc{Scoped}, 3B"), ("sga_json_vs_ctrl_scoped_7b", "\\textsc{Scoped} content as JSON $-$ \\textsc{Scoped}, 7B"),
       ("scoped7b_vs_1.5b", "7B reader $-$ 1.5B reader"), ("scoped1.5b_vs_moondream", "1.5B reader $-$ moondream"), ("scoped1.5b_vs_llavaphi3", "1.5B reader $-$ llava-phi3"),
       ("scoped1.5b_vs_q3vl2b_think", "1.5B reader $-$ Qwen3-VL 2B (1,024 tokens)"), ("scoped1.5b_vs_q3vl2b_direct", "1.5B reader $-$ Qwen3-VL 2B (256 tokens; 31\\% unparsed)"),
       ("scoped3b_vs_q3vl2b_think", "3B reader $-$ Qwen3-VL 2B (1,024 tokens)"), ("scoped0.5b_vs_moondream", "0.5B reader $-$ moondream"),
       ("gt1.5b_vs_0.5b", "ground-truth objects: 1.5B $-$ 0.5B reader"), ("gt_vs_scoped_3b", "ground-truth objects $-$ \\textsc{Scoped}, 3B"), ("gt_vs_scoped_7b", "ground-truth objects $-$ \\textsc{Scoped}, 7B"),
       ("ftvlm_vs_scoped_3b", "FT-VLM $-$ \\textsc{Scoped}, 3B"), ("ftvlm_vs_scoped_7b", "FT-VLM $-$ \\textsc{Scoped}, 7B"),
       ("ftvlm_vs_pixel_3b", "FT-VLM $-$ VLM, 3B"), ("ftvlm_vs_pixel_7b", "FT-VLM $-$ VLM, 7B"), ("ftvlm_7b_vs_3b", "FT-VLM 7B $-$ FT-VLM 3B"),
       ("fttext_vs_ftvlm_3b", "FT-Text $-$ FT-VLM, 3B"), ("fttext_vs_scoped_3b", "FT-Text $-$ \\textsc{Scoped}, 3B"), ("gt_vs_ftvlm_7b", "ground-truth objects (7B reader) $-$ FT-VLM 7B"),
       ("zs3b_lowres_vs_fullres", "VLM 3B: reduced $-$ full resolution (reference implementation)"),
       ("light1_vs_ctrl_scoped_3b", "one-pass detector pair $-$ full stack, 3B"), ("light1_vs_ctrl_scoped_7b", "one-pass detector pair $-$ full stack, 7B"),
       ("light2_vs_ctrl_scoped_3b", "detector pair and stereo $-$ full stack, 3B"), ("light2_vs_ctrl_scoped_7b", "detector pair and stereo $-$ full stack, 7B"),
       ("light3_vs_ctrl_scoped_3b", "no depth network, no stereo $-$ full stack, 3B"), ("light3_vs_ctrl_scoped_7b", "no depth network, no stereo $-$ full stack, 7B"),
       ("rfdetr_vs_ctrl_scoped_3b", "RF-DETR stack $-$ full stack, 3B"), ("rfdetr_vs_ctrl_scoped_7b", "RF-DETR stack $-$ full stack, 7B"),
       ("light1_vs_pixelrerun_3b", "one-pass detector pair $-$ VLM, 3B"), ("light1_vs_pixelrerun_7b", "one-pass detector pair $-$ VLM, 7B"),
       ("light2_vs_pixelrerun_3b", "detector pair and stereo $-$ VLM, 3B"), ("light2_vs_pixelrerun_7b", "detector pair and stereo $-$ VLM, 7B"),
       ("light3_vs_pixelrerun_3b", "no depth network, no stereo $-$ VLM, 3B"), ("light3_vs_pixelrerun_7b", "no depth network, no stereo $-$ VLM, 7B"),
       ("rfdetr_vs_pixelrerun_3b", "RF-DETR stack $-$ VLM, 3B"), ("rfdetr_vs_pixelrerun_7b", "RF-DETR stack $-$ VLM, 7B")]
s2 = []
for k, lab in LAB:
    r = B[k]; p = r["signflip_p"]
    s2.append(f"{lab} & {sgn(r['delta'], r['star'])} & {ci(r)} & {(f'{p:.4f}' if p >= 0.0001 else '$<$0.0001')} & {r['loso_cross_zero']}/21 & {r['pos']}/{r['neg']} \\\\")
FC = R["family_contrast"]
FLAB = [("primary_3b", "\\textsc{Scoped} $-$ VLM, 3B"), ("primary_7b", "\\textsc{Scoped} $-$ VLM, 7B"),
        ("hybrid_vs_pixelrerun_3b", "VLM + text $-$ VLM, 3B"), ("hybrid_vs_pixelrerun_7b", "VLM + text $-$ VLM, 7B"),
        ("hybrid_vs_ctrl_scoped_3b", "VLM + text $-$ \\textsc{Scoped}, 3B"), ("hybrid_vs_ctrl_scoped_7b", "VLM + text $-$ \\textsc{Scoped}, 7B"),
        ("taskinfo_vs_pixelrerun_3b", "VLM + vocabulary $-$ VLM, 3B"), ("taskinfo_vs_pixelrerun_7b", "VLM + vocabulary $-$ VLM, 7B"),
        ("d1_vs_scoped_3b", "D1 $-$ \\textsc{Scoped}, 3B"), ("d1_vs_scoped_7b", "D1 $-$ \\textsc{Scoped}, 7B"),
        ("d1_vs_pixel_3b", "D1 $-$ VLM, 3B"), ("d1_vs_pixel_7b", "D1 $-$ VLM, 7B"),
        ("scoped_vs_flat_3b", "\\textsc{Scoped} $-$ \\textsc{Flat}, 3B"), ("scoped_vs_flat_7b", "\\textsc{Scoped} $-$ \\textsc{Flat}, 7B"),
        ("rfdetr_vs_pixelrerun_3b", "RF-DETR stack $-$ VLM, 3B"), ("rfdetr_vs_pixelrerun_7b", "RF-DETR stack $-$ VLM, 7B"),
        ("light1_vs_ctrl_scoped_3b", "one-pass detector pair $-$ full stack, 3B"), ("light1_vs_ctrl_scoped_7b", "one-pass detector pair $-$ full stack, 7B"),
        ("sg_triples_vs_ctrl_scoped_3b", "object list as triples $-$ \\textsc{Scoped}, 3B"), ("sg_triples_vs_ctrl_scoped_7b", "object list as triples $-$ \\textsc{Scoped}, 7B"),
        ("sg_json_vs_ctrl_scoped_3b", "object list as JSON $-$ \\textsc{Scoped}, 3B"), ("sg_json_vs_ctrl_scoped_7b", "object list as JSON $-$ \\textsc{Scoped}, 7B"),
        ("fttext_vs_ftvlm_3b", "FT-Text $-$ FT-VLM, 3B")]
s2b = []
for k, lab in FLAB:
    for i, f in enumerate(FAMS):
        r = FC[k][f]
        s2b.append(f"{lab if i == 0 else ''} & {FN[f]} & {r['n']} & {sgn(r['delta'], r['star'])} & {ci(r)} \\\\")
    s2b.append("\\addlinespace[2pt]")
st = R["stratified"]
s2c = []
for k, lab in (("scoped_3b-pixel_3b", "\\textsc{Scoped} $-$ VLM, 3B"), ("scoped_7b-pixel_7b", "\\textsc{Scoped} $-$ VLM, 7B"), ("ftvlm_3b-pixel_3b", "FT-VLM $-$ VLM, 3B"),
               ("fttext_3b-scoped_3b", "FT-Text $-$ \\textsc{Scoped}, 3B"), ("fttext_3b-ftvlm_3b", "FT-Text $-$ FT-VLM, 3B")):
    a, b = st[k]["prior_right"], st[k]["prior_wrong"]
    s2c.append(f"{lab} & {sgn(a['delta'], a['star'])} {ci(a)} & {sgn(b['delta'], b['star'])} {ci(b)} \\\\")
ps = R["prior_strata"]

# ------------------------------------------------------------------ S3 development-bank controls


def pc(k):
    r = PC[k]; lo, hi = r["ci"]
    return f"${r['delta']:+.4f}{'^{*}' if r['sig'] else ''}$ $[{lo:+.4f},\\,{hi:+.4f}]$"


jk = {k: B[k]["jackknife"] for k in ("primary_3b", "primary_7b")}

# ------------------------------------------------------------------ S9 nuScenes
s9 = []
for f in FAMS:
    r = R["nuscenes2"]["mini_fixed"]["contrast"]["family_fix_vs_pixel_7b"][f]
    s9.append(f"{FN[f]} & {r['n']} & {r['clusters']} & {sgn(r['delta'], r['star'])} & {ci(r)} & {r['net_items']:+d} \\\\")
r = R["nuscenes2"]["mini_fixed"]["contrast"]["fix_vs_pixel_7b"]
s9.append(f"\\midrule all & {r['n']} & {r['clusters']} & {sgn(r['delta'], r['star'])} & {ci(r)} & {r['net_items']:+d} \\\\")

NL = "\n"
TEX = r"""\documentclass[10pt]{article}
\usepackage[margin=0.9in]{geometry}
\usepackage{booktabs,longtable,array,amsmath,url}
\usepackage{graphicx}
\usepackage[T1]{fontenc}
\usepackage{times}
\renewcommand{\thetable}{S\arabic{table}}
\renewcommand{\thesection}{S\arabic{section}}
\setlength{\parindent}{0pt}\setlength{\parskip}{5pt}
\sloppy\emergencystretch=3em
\newcommand{\settab}[1]{\setcounter{table}{#1}\addtocounter{table}{-1}\renewcommand{\thetable}{S\arabic{table}}}
\newcommand{\fixtab}[1]{\renewcommand{\thetable}{#1}}
\title{Supplement to ``Semantic Serialization as a Perception Interface for Small Language Models in Closed-Set, Task-Aware Embodied Question Answering''}
\author{Cong Xu and Ravi Sankar}
\date{}
\begin{document}
\maketitle
This supplement holds the tables and sections to which the paper refers: Tables S1, S2, S4 to S7, and S10, and Sections S2, S3, S8, S9, and S11 to S15. A table carries the number of its section; Section S3 has no table. All values are on the confirmatory bank (1328 questions, 21 recordings) unless a caption or a section says otherwise. Intervals are 95\% intervals of the paired bootstrap that Section VI of the paper defines, over the recordings of CODa or over the scenes of nuScenes; $^{*}$ marks an interval that excludes zero. Tables S1, S2, S8, S9, and S12 to S14 are computed from the released per-question predictions and logs by three scripts of the release (\texttt{exp\_rev1/analysis/rev2\_analysis.py}, \texttt{b10\_e2e\_numbers.py}, and \texttt{build\_supplement.py}).

\section{Parse rates}
Table~\ref{tab:s1} lists, for every arm on the confirmatory bank, the accuracy, the share of answers that contain a readable option letter (the parse rate), and the longest run of consecutive unreadable answers in bank order. An unreadable answer is counted as wrong. A long run indicates a fault of the serving software. The row ``first run'' of the 3B VLM had such a fault and is not used in the paper; the row ``run with the reload rule'' is its repetition with the rule that reloads the model after a degenerate answer.

\begin{longtable}{@{}p{0.60\linewidth}ccc@{}}
\caption{Accuracy, parse rate, and longest run of unreadable answers of every arm (confirmatory bank).}\label{tab:s1}\\
\toprule arm & accuracy & parse rate & longest run \\ \midrule \endfirsthead
\toprule arm & accuracy & parse rate & longest run \\ \midrule \endhead
\bottomrule \endfoot
<<S1>>
\end{longtable}

\section{Intervals of all comparisons}
Table~\ref{tab:s2a} gives every comparison of the paper with its interval and with the three further checks of Section VII-G of the paper: the $p$ value of the two-sided exact sign-flip test over the 21 recordings, the number of the 21 leave-one-sequence-out intervals that include zero, and the number of recordings in which the first system is ahead and behind. All rows are computed by one script. For the two primary comparisons, the intervals of the first analysis script, which was written during the confirmatory run (\texttt{analysis/confirm\_analysis.py}) are given in the row labels. That script and the script of this table implement the same resampling with different random-number generators, and their intervals differ in the third decimal ($[+0.0393,\,+0.0995]$ against $[+0.0403,\,+0.0996]$ at 3B, and $[+0.0070,\,+0.0689]$ against $[+0.0073,\,+0.0690]$ at 7B). Table~\ref{tab:s2b} gives the comparisons within each question family, and Table~\ref{tab:s2c} gives the comparisons on the questions that the answer-prior rule gets right and wrong.

{\footnotesize\fixtab{S2a}
\begin{longtable}{@{}p{0.43\linewidth}ccccc@{}}
\caption{All comparisons on the confirmatory bank (first system minus second).}\label{tab:s2a}\\
\toprule comparison & difference & 95\% interval & sign-flip $p$ & LOSO & ahead/behind \\ \midrule \endfirsthead
\toprule comparison & difference & 95\% interval & sign-flip $p$ & LOSO & ahead/behind \\ \midrule \endhead
\bottomrule \endfoot
<<S2>>
\end{longtable}

\fixtab{S2b}
\begin{longtable}{@{}p{0.36\linewidth}lccc@{}}
\caption{Comparisons within each question family.}\label{tab:s2b}\\
\toprule comparison & family & questions & difference & 95\% interval \\ \midrule \endfirsthead
\toprule comparison & family & questions & difference & 95\% interval \\ \midrule \endhead
\bottomrule \endfoot
<<S2B>>
\end{longtable}
}

\fixtab{S2c}\begin{table}[h]\centering\footnotesize
\caption{Comparisons on the <<PR>> questions that the answer-prior rule answers correctly and on the <<PW>> questions that it answers wrongly. The split was made after the results were known.}\label{tab:s2c}
\begin{tabular}{@{}lcc@{}}
\toprule comparison & rule right & rule wrong \\ \midrule
<<S2C>>
\bottomrule
\end{tabular}
\end{table}

\section{Further controls}
The following results are exploratory. They were obtained on the development bank (1366 questions) while the system was built, except where the confirmatory bank is named. The development-bank values are computed by \texttt{analysis/paper1\_controls.py} of the release; the 7B models are used unless a size is given.

\emph{What the text states in advance matters even with correct objects.} When the serializer receives the ground-truth objects, the \textsc{Flat} text scores $0.955$ and an older serializer, which wrote ranges and bearings as numbers, scores $0.857$ (<<PC:gtv9_vs_gtv3>>). A caption in prose with the same objects scores $0.804$.

\emph{The language model of the VLM is more accurate on the serialized text than the VLM on the image.} On the confirmatory bank, the language model of the VLM scores higher when it is given the serialized text and no image than when the VLM is given the image: $+0.0949^{*}$ $[+0.0497,\,+0.1244]$ at 3B and $+0.0377^{*}$ $[+0.0043,\,+0.0654]$ at 7B (\texttt{analysis/iface2\_confirm.json}). On the development bank the same comparison gives <<PC:controlA_vs_pixel>>, and the VLM on the text does not differ from the text-only model on the same text (<<PC:controlA>>).

\emph{Drawing the facts into the image is not enough.} When the class and the range of every ground-truth object are drawn into the image, the VLM scores $0.832$, which is <<PC:controlB>> more than with the plain image and <<PCN:gtv9_vs_anno>> less than the text-only reader on the \textsc{Flat} text of the same objects.

\emph{An object list alone is worse than the image.} A text that lists only the perceived objects, without the lines that the serializer computes, scores $0.608$, against $0.747$ for the VLM (<<PC:L0_vs_pixel>>). Adding the side words raises it by <<PC1:ladder_increments:L2-L1>>.

\emph{From \textsc{Flat} to \textsc{Scoped}.} Seven serializer versions were compared on the development bank; \textsc{Flat} is the first and \textsc{Scoped} the last. At 3B, adding the two selection lines and the sector by image column changed the accuracy by $+0.0549^{*}$ $[+0.0292,\,+0.0758]$; writing the object rows for every family by $-0.0168$ $[-0.0335,\,+0.0054]$; and limiting the rows to counting by $+0.0256^{*}$ $[+0.0023,\,+0.0394]$ (\texttt{analysis/stats\_for\_revision.txt}). The serializer of the first paragraph of this section, which writes numbers and no bands, is older than \textsc{Flat}.

\emph{Predictions written down before the runs on the probe banks and the range variants} (\texttt{amendments/A3\_amendment.md}). P1: with ranges in meters (D1) the system keeps a resolved advantage over the VLM in counting and keeps its sign in nearest-distance. The counting part held ($+0.1424^{*}$ at 3B, $+0.1325^{*}$ at 7B); the nearest-distance part failed (the sign changed: $-0.0512$ at 3B and $-0.0157$ at 7B, both unresolved). P2: rewording (N1) removes less than half of the advantage. It held (46\% at 3B; at 7B the advantage is larger on N1). P3: on N2, D1 exceeds the VLM. It failed ($-0.0473^{*}$ at 3B, $+0.0516$ unresolved at 7B).

\emph{Predictions of the two later groups of experiments.} For the reader sizes (\texttt{amendments/A4\_amendment.md}): S1, that the advantage over the VLM does not shrink from 7B to 3B to the nearest smaller VLM, held ($+0.0429^{*}$, $+0.0761^{*}$, and $+0.1242^{*}$ for the 1.5B reader against moondream); at 0.5B, which S1 did not cover, the serialized system fails. S2, that the advantage of the D1 variant on N2 is absent or negative at 1.5B and 0.5B, did not hold against the one VLM of that size: D1 is ahead of moondream by $+0.1947^{*}$ at 1.5B and $+0.1617^{*}$ at 0.5B (moondream scores $0.272$ on N2, less than a random choice). The plan specified a budget of 256 tokens and no paired comparison for Qwen3-VL 2B; the 1,024-token run and its comparison with the 1.5B reader were added afterwards. For the fine-tuned arms (\texttt{amendments/A5\_amendment.md}): the expectation that fine-tuning the VLM narrows the advantage of the serialized system held; the advantage reverses ($-0.0768^{*}$ at 3B and $-0.0685^{*}$ at 7B). The error analysis of Section V-B of the paper used a version of the system older than \textsc{Flat}.

\emph{Another model family as the reader.} With the \textsc{Flat} text, Llama-3.1-8B scores $0.776$ and Qwen2.5-7B scores $0.802$ on one machine (<<PC:xfam_llama3.1:8b  [PAPER CONTROL]>>). Runs with three further models failed in the serving software and are not reported.

\emph{The VLM with added inputs} (\texttt{exp\_rev1/B123\_PREREG.md}). The plan compared each arm with the archived run of the VLM and expected a control run to reproduce that run within $0.0015$. The control run of the 3B VLM differs from the archived run by <<JD:battery/pixelrerun_vs_archived_3b>> (unresolved), so the paper compares each arm with the control runs. In the arm with the answer vocabulary, the prompt gives the band boundaries, the 40\,m scope, the question family, and this rule for the side: left if the object is more than $15^\circ$ to the left of the optical axis, right if it is more than $15^\circ$ to the right, and center otherwise. This rule agrees with the image thirds that define the correct answers for $98.4\%$ of the objects.

\section{Classifiers on the serialized text}
Table~\ref{tab:s4} gives the accuracy of three classifiers that score each option from features of the serialized text. They are fitted on the development bank and applied without change to the confirmatory bank and to the two probe banks. On the probe banks they fall to the level of a random choice, because their features use the exact option strings (\texttt{summaries/baselines.md}, \texttt{summaries/baselines\_n1n2.md}).
\settab{4}\begin{table}[h]\centering\footnotesize
\caption{Classifiers over the serialized text, and the 7B reader for reference. A random choice gives $1/3$.}\label{tab:s4}
\begin{tabular}{@{}lccc@{}}
\toprule classifier & confirmatory & N1 & N2 \\ \midrule
fixed rule & 0.8027 & 0.3479 & 0.3510 \\
logistic regression & 0.8080 & 0.3479 & 0.3332 \\
gradient-boosted trees & 0.8245 & 0.3479 & 0.3183 \\ \midrule
7B reader on \textsc{Scoped}, no task training & 0.7892 & 0.7914 & 0.5860 \\
\bottomrule
\end{tabular}
\end{table}

\section{A second interval procedure for the primary comparisons}
\settab{5}\begin{table}[h]\centering\footnotesize
\caption{The two primary comparisons under a second interval procedure, the delete-one cluster jackknife, computed by the script of Table~\ref{tab:s2a}.}\label{tab:s5}
\begin{tabular}{@{}lcc@{}}
\toprule procedure & 3B & 7B \\ \midrule
difference & $+0.0761$ & $+0.0429$ \\
paired bootstrap over recordings (criterion) & $[+0.0403,\,+0.0996]$ & $[+0.0073,\,+0.0690]$ \\
cluster jackknife & <<JK3>> & <<JK7>> \\
\bottomrule
\end{tabular}
\end{table}

\section{Detectors on their training recordings and on held-out recordings}
\settab{6}\begin{table}[h]\centering\footnotesize
\caption{Mean average precision at an overlap of $0.5$ (mAP$_{50}$), at overlaps of $0.5$ to $0.95$, and recall of the two detectors of each fold, on the frames of their training recordings and on the recordings held out from the fold (1280 pixels, one pass, default settings of the library). The held-out columns are what the serializer receives. The last column is the mAP$_{50}$ of RF-DETR-Medium, trained on the same frames, on the held-out recordings; its mean on the training recordings is $0.80$.}\label{tab:s6}
\begin{tabular}{@{}llccccc@{}}
\toprule
fold (held-out recordings) & detector & \multicolumn{2}{c}{training recordings} & \multicolumn{2}{c}{held-out recordings} & RF-DETR \\
 & & mAP$_{50}$ / mAP$_{50:95}$ & recall & mAP$_{50}$ / mAP$_{50:95}$ & recall & held-out mAP$_{50}$ \\ \midrule
0 (3, 8, 19, 20) & YOLO11l & 0.94 / 0.72 & 0.87 & 0.26 / 0.12 & 0.25 & 0.30 \\
 & YOLO11m & 0.93 / 0.71 & 0.85 & 0.26 / 0.12 & 0.27 & \\
1 (1, 4, 10, 13, 18) & YOLO11l & 0.94 / 0.75 & 0.88 & 0.29 / 0.13 & 0.35 & 0.34 \\
 & YOLO11m & 0.92 / 0.69 & 0.84 & 0.30 / 0.14 & 0.31 & \\
2 (2, 9, 12, 14--16) & YOLO11l & 0.94 / 0.74 & 0.86 & 0.35 / 0.15 & 0.35 & 0.40 \\
 & YOLO11m & 0.91 / 0.68 & 0.83 & 0.35 / 0.15 & 0.35 & \\
3 (0, 5--7, 11, 17) & YOLO11l & 0.93 / 0.73 & 0.86 & 0.38 / 0.17 & 0.37 & 0.45 \\
 & YOLO11m & 0.91 / 0.68 & 0.82 & 0.41 / 0.18 & 0.37 & \\
\bottomrule
\end{tabular}
\end{table}
Removing the boxes of fully occluded objects from the labels (under 4\% of the boxes within 40\,m) leaves the mean held-out mAP$_{50}$ of YOLO11l at $0.32$.

\section{Size of what reaches the language model}
\settab{7}\begin{table}[h]\centering\footnotesize
\caption{Size of the input of the reader and of the VLM for the 1328 confirmatory questions. Text tokens are counted with the Qwen2.5 tokenizer; visual tokens with the Qwen2.5-VL processor at its default setting. The frame is $1224{\times}1024$ pixels. P95 is the 95th percentile.}\label{tab:s7}
\begin{tabular}{@{}lrrr@{}}
\toprule quantity & median & mean & P95 \\ \midrule
\textsc{Scoped} text, bytes & 764 & 994 & 2216 \\
\textsc{Scoped} text, tokens & 236 & 339 & 846 \\
\textsc{Scoped} text with object rows for every family, bytes & 1914 & 1975 & 2735 \\
\textsc{Scoped} text with object rows for every family, tokens & 731 & 762 & 1092 \\ \midrule
frame as PNG (as sent to the VLM), bytes & 2,088,100 & 2,055,126 & 2,406,479 \\
frame as JPEG, quality 90, bytes & 330,852 & 323,623 & 404,166 \\
frame as JPEG, quality 75, bytes & 189,818 & 186,089 & 235,196 \\
frame as JPEG, quality 75, 640 pixels wide, bytes & 64,102 & 61,794 & 77,330 \\
visual tokens of the VLM & 1628 & 1628 & 1628 \\ \midrule
objects in the perceived state & 17 & 18 & 29 \\
\bottomrule
\end{tabular}
\end{table}
The \textsc{Scoped} text has 702 to 729 bytes (216 to 227 tokens) for the four families without object rows and 1840 bytes (700 tokens) for counting (medians). The text of the earlier serializer \textsc{Flat}, as it was run, has a median length of 1795 characters.

\section{Details of the measurements on the Jetson Orin Nano}
All values of the table of board measurements in the paper, part (b), come from one session (25\,W mode, desktop running, llama.cpp commit 11fe021 built with CUDA, all layers on the GPU, prompt cache in host memory disabled). Table~\ref{tab:s8} adds values that the paper does not show. The board has 8\,GB of memory that the processor and the GPU share. For five questions about one frame the server keeps the encoded image (VLM) or the common part of the text (reader). The row in bold of part (b) of the table of the paper is the sum of the unrounded values of the detector pair and the 3B reader. The two boards without a GPU have no power monitor.
\settab{8}\begin{table}[h]\centering\footnotesize
\caption{Jetson Orin Nano, further values. ``Full-stack prompts'': the reader on the \textsc{Scoped} text of the perceived states that the full stack computed on the laptop (the timing set of 50 questions), median and mean time per question. ``Five questions'': median time of the first and of a later question about one frame, with the prompt cache of the server on; the first question of a frame is always a counting question, which has the longest text. ``Free memory'': lowest free system memory during the five-question run.}\label{tab:s8}
\begin{tabular}{@{}lcccccc@{}}
\toprule
 & \multicolumn{3}{c}{full-stack prompts} & \multicolumn{3}{c}{five questions, one frame} \\
model & median (s) & mean (s) & same answers & first (s) & later (s) & free memory (GB) \\ \midrule
reader 0.5B & <<O:s05_med>> & <<O:s05_s>> & <<O:s05_agree>> & --- & --- & --- \\
reader 1.5B & <<O:s15_med>> & <<O:s15_s>> & <<O:s15_agree>> & <<O:r15_first>> & <<O:r15_later>> & <<O:r15_s5_min_avail_gb>> \\
reader 3B & <<O:s3_med>> & <<O:s3_s>> & <<O:s3_agree>> & <<O:r3_first>> & <<O:r3_later>> & <<O:r3_s5_min_avail_gb>> \\
reader 7B & <<O:s7_med>> & <<O:s7_s>> & <<O:s7_agree>> & <<O:r7_first>> & <<O:r7_later>> & <<O:r7_s5_min_avail_gb>> \\
VLM moondream & <<O:md_med>> & <<O:md_s>> & <<O:md_agree>> & <<O:md_first>> & <<O:md_later>> & <<O:md_s5_min_avail_gb>> \\
VLM Qwen2.5-VL 3B & <<O:vl_med>> & <<O:vl_s>> & <<O:vl_agree>> & <<O:vl_first>> & <<O:vl_later>> & <<O:vl_s5_min_avail_gb>> \\
\bottomrule
\end{tabular}
\end{table}

The one-pass detector pair needs <<O:perc_s>>\,s per frame (slope of the wall time over runs of 1, 11, and 41 frames; <<O:perc_loop_s>>\,s per frame inside the frame loop of the 41-frame run) and <<O:perc_fixed_s>>\,s once to load. The board draws <<O:idle_w>>\,W when idle and <<O:perc_w>>\,W in the frame loop. With the 3B reader loaded at the same time, the lowest free memory during perception is <<O:cores_min_avail_gb>>\,GB. The serializer needs <<O:ser_ms>>\,ms per question on the board. The detectors run in PyTorch without conversion to an inference engine, so the time per frame is an upper value for this board.

The Qwen2.5-VL 3B file of the laptop runs packs the vision encoder in a format that llama.cpp does not read. The board therefore ran the conversion of the same model that the llama.cpp project publishes, at the same quantization; its answers agree with the laptop run for <<O:vl_agree>> questions of the timing set. Moondream was run with the prompt template of the laptop serving software, reproduced on the completion endpoint of llama.cpp.

On the two boards without a GPU, the mean and the 95th percentile of the time per question are $30.1$ and $63.8$\,s (0.5B) and $59.9$ and $125.6$\,s (1.5B) on the Orange~Pi~3B, and $12.5$ and $25.3$\,s (0.5B) and $24.8$ and $50.3$\,s (1.5B) on the Agilex~5 HPS. Each server ran under a memory limit of 1.52\,GB, so that a model that does not fit is stopped and does not use swap space. For the 0.5B reader on the Orange~Pi, the memory value of the paper ($0.69$\,GB) is from a separate run of 10 questions without the prompt cache of the server; with the cache, the timed run peaked at $0.95$\,GB.

\emph{Note on an earlier table.} The file \texttt{summaries/compute\_table.md} of the release lists, for several questions about one frame, a session of the 7B VLM in which the image was already encoded before the first question (0.44, 0.82, 1.86, and 3.70\,s for 1, 2, 5, and 10 questions). The table of the paper adds the one encoding of the image that a new frame requires ($1.102$\,s for the first question and $0.371$\,s for each further one), and it uses the per-question medians of the module table for the readers.

\section{The first check on nuScenes (nuScenes-mini)}
This check on the ten scenes of nuScenes-mini (347 questions) was run before the bank of Section~S14 was built, and the perception settings for nuScenes were fixed on it. It is not used for any criterion.

\emph{Correction.} In its first run the serializer used the image width of the CODa camera (1224 pixels) for the 1600-pixel images of nuScenes, so that it placed the boundaries between left, center, and right at the wrong image columns. With annotated objects its sector differed from the correct sector in 11 of the 64 direction questions. The values of this section are from a second run with the image width of the camera (\texttt{amendments/A6\_addendum1.md}). The serialized system then scores <<J:nuscenes2/mini_fixed/fix_d0_rfdetr_3b/acc>> at 3B and <<J:nuscenes2/mini_fixed/fix_d0_rfdetr_7b/acc>> at 7B (first run: <<J:nuscenes/arms/d0_rfdetr_3b/acc>> and <<J:nuscenes/arms/d0_rfdetr_7b/acc>>); in the direction family it scores <<J:nuscenes2/mini_fixed/fix_d0_rfdetr_3b/family/direction|.3f>> and <<J:nuscenes2/mini_fixed/fix_d0_rfdetr_7b/family/direction|.3f>> (first run: <<J:nuscenes/arms/d0_rfdetr_3b/family/direction|.3f>> and <<J:nuscenes/arms/d0_rfdetr_7b/family/direction|.3f>>). With annotated objects the readers score <<J:nuscenes2/mini_fixed/fix_d0_gt_3b/acc>> and <<J:nuscenes2/mini_fixed/fix_d0_gt_7b/acc>> (first run: <<J:nuscenes/arms/d0_gt_3b/acc>> and <<J:nuscenes/arms/d0_gt_7b/acc>>). The 7B VLM scores <<J:nuscenes/arms/pixel_7b/acc>>. The serialized system minus the VLM at 7B is <<JDCI:nuscenes2/mini_fixed/contrast/fix_vs_pixel_7b>> (first run: <<JDCI:nuscenes/contrast/ser_vs_pixel_7b>>). The 3B VLM, served by Ollama, returned a parsable answer for only 60\% of the questions and is not compared.

\settab{9}\begin{table}[h]\centering\footnotesize
\caption{nuScenes-mini bank, serialized system (second run) minus VLM at 7B, by family. ``Net'' is the number of questions that only the serialized system answers correctly minus the number that only the VLM answers correctly. Intervals resample the 10 scenes (8 scenes contain path-object questions).}\label{tab:s9}
\begin{tabular}{@{}lccccc@{}}
\toprule family & questions & scenes & difference & 95\% interval & net \\ \midrule
<<S9>>
\bottomrule
\end{tabular}
\end{table}
The surface-cue audit of the generator did not pass on this bank. Over all questions, the correct option is the shortest of the three in $0.432$ and the longest in $0.343$ of the questions; in the nearest-class family the values are $0.552$ and $0.209$, in the nearest-distance family $0.439$ and $0.439$, and in the path-object family $0.455$ and $0.182$ (\texttt{exp\_rev1/c1\_nusc/audit\_full.txt}). In the nearest-distance family the correct band is ``over 15 meters'' in 36 questions and ``5 to 15 meters'' in 30. The 3B VLM returned a degenerate repeated string for 40\% of the questions even with a reload of the model for every question; the incident is described in \texttt{exp\_rev1/c1\_nusc/INCIDENTS.md}.

\section{Probe banks N1 and N2}
\settab{10}\begin{table}[h]\centering\footnotesize
\caption{Accuracy on the probe bank N2 (3974 questions of three types that no serializer was written for; the text arms cover 3971 of them, and differences are paired). Differences from the VLM of the same size: \textsc{Scoped} $+0.0118$ $[-0.0196,\,+0.0360]$ at 3B and $+0.0413^{*}$ $[+0.0021,\,+0.0738]$ at 7B; D1 $-0.0473^{*}$ $[-0.0764,\,-0.0064]$ at 3B and $+0.0516$ $[-0.0014,\,+0.0970]$ at 7B.}\label{tab:s10}
\begin{tabular}{@{}lcccc@{}}
\toprule reader size & 0.5B & 1.5B & 3B & 7B \\ \midrule
\textsc{Scoped} & 0.4132 & 0.4591 & 0.5014 & 0.5860 \\
D1 & 0.4336 & 0.4666 & 0.4422 & 0.5963 \\ \midrule
VLM & \multicolumn{4}{c}{moondream 0.2720; llava-phi3 0.4867; Qwen2.5-VL 3B 0.4899; Qwen2.5-VL 7B 0.5448} \\
\bottomrule
\end{tabular}
\end{table}
On N1, in which every question and option is reworded, the accuracies are $0.7515$ at 3B and $0.7914$ at 7B for \textsc{Scoped}, $0.7086$ and $0.7733$ for D1, and $0.7101$ and $0.7176$ for the VLM. The differences from the VLM are $+0.0414^{*}$ $[+0.0050,\,+0.0677]$ at 3B and $+0.0738^{*}$ $[+0.0281,\,+0.1039]$ at 7B for \textsc{Scoped}, and $-0.0015$ $[-0.0477,\,+0.0293]$ at 3B and $+0.0557^{*}$ $[+0.0064,\,+0.0861]$ at 7B for D1 (\texttt{summaries/SUMMARY.md}). FT-VLM 3B, evaluated on the probe banks without change, is $+0.1258^{*}$ above the VLM without task training on N1 and $+0.0526^{*}$ on N2.

\section{Where the material is in the release}
The script \texttt{go\_confirm.bat} was last saved at 23:33:42 on 8 August 2026. Its log shows that the generation of the confirmatory bank started at 23:33:49 and that the first arm started at 23:56:26. These are file and log times of the authors' machine.

\medskip
\begin{tabular}{@{}p{0.42\linewidth}p{0.52\linewidth}@{}}
\toprule item & location in the release \\ \midrule
question banks & \texttt{banks/} \\
perceived states and ground-truth states & \texttt{states/} \\
per-question predictions, first submission & \texttt{results/} \\
per-question predictions and logs, both revisions & \texttt{exp\_rev1/} (one folder per experiment; \texttt{README.md} there maps folders to tables) \\
record of the primary criterion & folder \texttt{amendments/primary\_criterion/}: \texttt{go\_confirm.bat}, the script that generated the confirmatory bank and ran the arms, with the criterion in its header, and \texttt{confirm.log}, its log; \texttt{A0\_primary\_criterion.md} in \texttt{amendments/} gives the times \\
later additions, as committed & \texttt{amendments/A3} to \texttt{A6} with \texttt{A6\_addendum1.md}, \texttt{exp\_rev1/B123\_PREREG.md} \\
source of the serializer and its check & \texttt{serializer/} (\texttt{verify\_serializer.py}) \\
protocol R, confirmatory bank & \texttt{exp\_rev1/c3\_reason/} \\
second nuScenes bank, predictions, perceived states; VLM with the Transformers library & \texttt{exp\_rev1/c2\_nusc/} \\
analysis of this paper (all comparisons) & \texttt{exp\_rev1/analysis/rev2\_analysis.py}, \texttt{rev2\_results.json} \\
analysis of the two primary comparisons & \texttt{analysis/confirm\_analysis.py}, \texttt{analysis/stats\_for\_revision.txt} \\
board measurements & \texttt{exp\_rev1/b10\_boards/} \\
\bottomrule
\end{tabular}
\section{Accuracy balanced over correct answers}
This analysis was made after the results were known (\texttt{amendments/A6\_amendment.md}, Part~3). Within a family, the accuracy is computed for each correct answer that occurs in at least $m$ questions of the confirmatory bank, and these values are averaged; the balanced accuracy is the mean of the five family values. A rule that always gives the most frequent answer of a family scores $1/K$ in a family with $K$ answers. Table~\ref{tab:s12} gives the result for $m=5$, which was fixed first, and for $m=10$ and $m=1$. With $m=5$ the families have <<J:balanced/min5/cells/counting|d>> (counting), <<J:balanced/min5/cells/direction|d>> (direction), <<J:balanced/min5/cells/nearest_class|d>> (nearest-class), <<J:balanced/min5/cells/nearest_dist|d>> (nearest-distance), and <<J:balanced/min5/cells/path_object|d>> (path-object) answers, which cover <<J:balanced/min5/n_in_cells|d>> of the 1328 questions; with $m=1$ the two class families have <<J:balanced/min1/cells/nearest_class|d>> and <<J:balanced/min1/cells/path_object|d>> answers, many of which occur in one to four questions. The intervals resample the 21 recordings ($B=20000$).

\settab{12}\begin{table}[h]\centering\footnotesize
\caption{Balanced accuracy on the confirmatory bank (top) and differences in balanced accuracy with 95\% intervals (bottom), for three values of the minimum number $m$ of questions per correct answer. A star marks an interval that excludes zero. The pairs are those of the table of further checks of the paper (Table 9), as the amendment specified, and \textsc{Flat} $-$ VLM. $^{\dagger}$: difference from a control run.}\label{tab:s12}
\setlength{\tabcolsep}{3.5pt}\begin{tabular}{@{}lccc@{}}
\toprule & $m=5$ & $m=10$ & $m=1$ \\ \midrule
answer-prior rule & <<J:balanced/min5/acc/prior>> & <<J:balanced/min10/acc/prior>> & <<J:balanced/min1/acc/prior>> \\
VLM, 3B & <<J:balanced/min5/acc/pixel_3b>> & <<J:balanced/min10/acc/pixel_3b>> & <<J:balanced/min1/acc/pixel_3b>> \\
VLM, 7B & <<J:balanced/min5/acc/pixel_7b>> & <<J:balanced/min10/acc/pixel_7b>> & <<J:balanced/min1/acc/pixel_7b>> \\
\textsc{Scoped}, 3B reader & <<J:balanced/min5/acc/scoped_3b>> & <<J:balanced/min10/acc/scoped_3b>> & <<J:balanced/min1/acc/scoped_3b>> \\
\textsc{Scoped}, 7B reader & <<J:balanced/min5/acc/scoped_7b>> & <<J:balanced/min10/acc/scoped_7b>> & <<J:balanced/min1/acc/scoped_7b>> \\
VLM with image and \textsc{Scoped} text, 3B & <<J:balanced/min5/acc/hybrid_3b>> & <<J:balanced/min10/acc/hybrid_3b>> & <<J:balanced/min1/acc/hybrid_3b>> \\
VLM with image and \textsc{Scoped} text, 7B & <<J:balanced/min5/acc/hybrid_7b>> & <<J:balanced/min10/acc/hybrid_7b>> & <<J:balanced/min1/acc/hybrid_7b>> \\
FT-VLM, 3B & <<J:balanced/min5/acc/ftvlm_3b>> & <<J:balanced/min10/acc/ftvlm_3b>> & <<J:balanced/min1/acc/ftvlm_3b>> \\
FT-Text, 3B & <<J:balanced/min5/acc/fttext_3b>> & <<J:balanced/min10/acc/fttext_3b>> & <<J:balanced/min1/acc/fttext_3b>> \\
ground-truth objects, 7B reader & <<J:balanced/min5/acc/gt_7b>> & <<J:balanced/min10/acc/gt_7b>> & <<J:balanced/min1/acc/gt_7b>> \\ \midrule
<<S12ROWS>>
\bottomrule
\end{tabular}
\end{table}
\section{Reasoning before the answer, and a second back end for the VLM}
Both additions were written down in \texttt{amendments/A6\_amendment.md} and committed to the authors' repository before the runs. The commit carries the time of the authors' machine; it was not registered with a third party.

\emph{Protocol R.} The last sentence of the system prompt of each route (``Reply with ONLY the option letter.'') is replaced by ``First reason step by step in a few sentences. Then give the final answer on a new last line in the form `Answer: X', where X is the option letter.'' The last line of the user prompt is replaced by ``Reason step by step, then end with a line of the form `Answer: X'.'' The temperature is 0, and at most 512 tokens are generated. The answer is the option letter that follows the last occurrence of the word ``answer'' in the output, with or without ``is'' and a colon (for example ``Answer: B'' or ``the correct answer is C''). If no letter follows any occurrence but the text after the last ``Answer:'' is exactly the text of one option, that option counts. Otherwise, if the last line has at most 20 characters, a letter in that line counts. Every other output is unparsed and is counted as wrong. The amendment describes the last-line rule as applying only when the output contains no ``Answer:''; the committed script, whose hash the amendment records, also applies it when the text after ``Answer:'' names no option, so that ``Answer: N/A'' is read as option A. This happened in 13 outputs of the 7B VLM on the second nuScenes bank (4 of them are counted as correct) and in 1 output of the 7B VLM on the confirmatory bank (counted as wrong); it favors the VLM. A server error without text is not scored: the model is unloaded and the question is asked again, at most three times. The reload rule of the VLM arms of the paper also applies (after four unparsed outputs in a row the model is reloaded and the question is asked once more). The wording and the rule were fixed on the first 40 questions of the development bank (25 questions for the 7B models).

\settab{13}\begin{table}[h]\centering\footnotesize
\caption{Confirmatory bank: the shipped arms, which answer with the option letter, and the same routes under protocol R. ``Parsed'' is the share of outputs from which an option could be read; the last column is the accuracy on those outputs. The median output has <<J:protocol_r/arms/vlmR_3b/median_chars|.0f>> and <<J:protocol_r/arms/vlmR_7b/median_chars|.0f>> characters for the VLM (3B and 7B) and <<J:protocol_r/arms/readerR_3b/median_chars|.0f>> and <<J:protocol_r/arms/readerR_7b/median_chars|.0f>> for the reader.}\label{tab:s13}
\setlength{\tabcolsep}{3.5pt}\begin{tabular}{@{}lcccccccc@{}}
\toprule arm & all & counting & direction & nearest-class & nearest-dist. & path-object & parsed & on parsed \\ \midrule
VLM, 3B, letter & <<J:acc/pixel_3b>> & <<J:acc_family/pixel_3b/counting|.3f>> & <<J:acc_family/pixel_3b/direction|.3f>> & <<J:acc_family/pixel_3b/nearest_class|.3f>> & <<J:acc_family/pixel_3b/nearest_dist|.3f>> & <<J:acc_family/pixel_3b/path_object|.3f>> & \multicolumn{2}{c}{Table S1} \\
VLM, 3B, protocol R & <<J:protocol_r/arms/vlmR_3b/acc>> & <<J:protocol_r/arms/vlmR_3b/family/counting|.3f>> & <<J:protocol_r/arms/vlmR_3b/family/direction|.3f>> & <<J:protocol_r/arms/vlmR_3b/family/nearest_class|.3f>> & <<J:protocol_r/arms/vlmR_3b/family/nearest_dist|.3f>> & <<J:protocol_r/arms/vlmR_3b/family/path_object|.3f>> & <<J:protocol_r/arms/vlmR_3b/parse|.3f>> & <<J:protocol_r/arms/vlmR_3b/acc_parsed|.3f>> \\
VLM, 7B, letter & <<J:acc/pixel_7b>> & <<J:acc_family/pixel_7b/counting|.3f>> & <<J:acc_family/pixel_7b/direction|.3f>> & <<J:acc_family/pixel_7b/nearest_class|.3f>> & <<J:acc_family/pixel_7b/nearest_dist|.3f>> & <<J:acc_family/pixel_7b/path_object|.3f>> & \multicolumn{2}{c}{Table S1} \\
VLM, 7B, protocol R & <<J:protocol_r/arms/vlmR_7b/acc>> & <<J:protocol_r/arms/vlmR_7b/family/counting|.3f>> & <<J:protocol_r/arms/vlmR_7b/family/direction|.3f>> & <<J:protocol_r/arms/vlmR_7b/family/nearest_class|.3f>> & <<J:protocol_r/arms/vlmR_7b/family/nearest_dist|.3f>> & <<J:protocol_r/arms/vlmR_7b/family/path_object|.3f>> & <<J:protocol_r/arms/vlmR_7b/parse|.3f>> & <<J:protocol_r/arms/vlmR_7b/acc_parsed|.3f>> \\ \midrule
\textsc{Scoped}, 3B reader, letter & <<J:acc/scoped_3b>> & <<J:acc_family/scoped_3b/counting|.3f>> & <<J:acc_family/scoped_3b/direction|.3f>> & <<J:acc_family/scoped_3b/nearest_class|.3f>> & <<J:acc_family/scoped_3b/nearest_dist|.3f>> & <<J:acc_family/scoped_3b/path_object|.3f>> & \multicolumn{2}{c}{Table S1} \\
\textsc{Scoped}, 3B reader, protocol R & <<J:protocol_r/arms/readerR_3b/acc>> & <<J:protocol_r/arms/readerR_3b/family/counting|.3f>> & <<J:protocol_r/arms/readerR_3b/family/direction|.3f>> & <<J:protocol_r/arms/readerR_3b/family/nearest_class|.3f>> & <<J:protocol_r/arms/readerR_3b/family/nearest_dist|.3f>> & <<J:protocol_r/arms/readerR_3b/family/path_object|.3f>> & <<J:protocol_r/arms/readerR_3b/parse|.3f>> & <<J:protocol_r/arms/readerR_3b/acc_parsed|.3f>> \\
\textsc{Scoped}, 7B reader, letter & <<J:acc/scoped_7b>> & <<J:acc_family/scoped_7b/counting|.3f>> & <<J:acc_family/scoped_7b/direction|.3f>> & <<J:acc_family/scoped_7b/nearest_class|.3f>> & <<J:acc_family/scoped_7b/nearest_dist|.3f>> & <<J:acc_family/scoped_7b/path_object|.3f>> & \multicolumn{2}{c}{Table S1} \\
\textsc{Scoped}, 7B reader, protocol R & <<J:protocol_r/arms/readerR_7b/acc>> & <<J:protocol_r/arms/readerR_7b/family/counting|.3f>> & <<J:protocol_r/arms/readerR_7b/family/direction|.3f>> & <<J:protocol_r/arms/readerR_7b/family/nearest_class|.3f>> & <<J:protocol_r/arms/readerR_7b/family/nearest_dist|.3f>> & <<J:protocol_r/arms/readerR_7b/family/path_object|.3f>> & <<J:protocol_r/arms/readerR_7b/parse|.3f>> & <<J:protocol_r/arms/readerR_7b/acc_parsed|.3f>> \\
\bottomrule
\end{tabular}
\end{table}

Table~\ref{tab:s13} gives the accuracies. The four comparisons that were fixed in advance are, at 3B and 7B respectively (paired bootstrap over the 21 recordings): reader under protocol R minus VLM under protocol R, <<JDCI:protocol_r/contrast/readerR_vs_vlmR_3b>> and <<JDCI:protocol_r/contrast/readerR_vs_vlmR_7b>>; shipped serialized system minus VLM under protocol R, <<JDCI:protocol_r/contrast/scoped_vs_vlmR_3b>> and <<JDCI:protocol_r/contrast/scoped_vs_vlmR_7b>>; VLM under protocol R minus shipped VLM, <<JDCI:protocol_r/contrast/vlmR_vs_vlm_3b>> and <<JDCI:protocol_r/contrast/vlmR_vs_vlm_7b>>; reader under protocol R minus shipped serialized system, <<JDCI:protocol_r/contrast/readerR_vs_scoped_3b>> and <<JDCI:protocol_r/contrast/readerR_vs_scoped_7b>>. These comparisons use the archived runs of the paper, as the amendment specified. Against the control runs of Section~VI of the paper, which were made on the present installation of the serving software, the VLM under protocol R changes by <<JDCI:protocol_r/contrast/vlmR_vs_ctrlvlm_3b>> at 3B and <<JDCI:protocol_r/contrast/vlmR_vs_ctrlvlm_7b>> at 7B, the reader by <<JDCI:protocol_r/contrast/readerR_vs_ctrlscoped_3b>> and <<JDCI:protocol_r/contrast/readerR_vs_ctrlscoped_7b>>, and the control run of the serialized system leads the VLM under protocol R by <<JDCI:protocol_r/contrast/ctrlscoped_vs_vlmR_3b>> and <<JDCI:protocol_r/contrast/ctrlscoped_vs_vlmR_7b>>. For the first three comparisons the sign-flip test gives $p<0.005$ at both sizes and no leave-one-recording-out interval includes zero; these two checks were not part of the amendment.

The unparsed outputs are few. The 3B VLM has <<J:protocol_r/arms/vlmR_3b/n_unparsed|d>>: <<J:protocol_r/arms/vlmR_3b/unparsed_error|d>> server errors that remained after three repetitions, <<J:protocol_r/arms/vlmR_3b/unparsed_cut|d>> outputs cut at 512 tokens, and <<J:protocol_r/arms/vlmR_3b/unparsed_other|d>> outputs that name no offered option; most of the last group state that no option is correct or that the question cannot be answered from the image. The 7B VLM has <<J:protocol_r/arms/vlmR_7b/n_unparsed|d>> unparsed outputs, the 3B reader <<J:protocol_r/arms/readerR_3b/n_unparsed|d>>, and the 7B reader <<J:protocol_r/arms/readerR_7b/n_unparsed|d>>. The numbers of outputs cut at 512 tokens are <<J:protocol_r/arms/vlmR_3b/cut_at_limit|d>> (3B VLM), <<J:protocol_r/arms/vlmR_7b/cut_at_limit|d>> (7B VLM), <<J:protocol_r/arms/readerR_3b/cut_at_limit|d>> (3B reader), and <<J:protocol_r/arms/readerR_7b/cut_at_limit|d>> (7B reader). If the unparsed outputs are left out, the VLM under protocol R still scores below the shipped VLM on all questions (last column of Table~\ref{tab:s13}).

\emph{The VLM with the Transformers library.} The VLM arms of the paper are served by Ollama with weights quantized to 4 bits. As a check of this back end, the same two VLMs were run on the confirmatory bank with the Transformers library, the weights of the model authors in 16-bit floating point (bfloat16), the image at its native resolution, and the shipped prompts, decoding, and parser. (Table~S1 lists an earlier run of the 3B VLM with this library, which used the prompt of the fine-tuned arms and scores $0.6920$.) They score <<J:protocol_r/arms/hfpixel_3b/acc>> at 3B and <<J:protocol_r/arms/hfpixel_7b/acc>> at 7B; the differences from the shipped VLM arms are <<JDCI:protocol_r/contrast/hfpixel_vs_vlm_3b>> and <<JDCI:protocol_r/contrast/hfpixel_vs_vlm_7b>>. The serialized system, whose reader uses 4-bit weights, minus this VLM is <<JDCI:protocol_r/contrast/scoped_vs_hfpixel_3b>> at 3B and <<JDCI:protocol_r/contrast/scoped_vs_hfpixel_7b>> at 7B.
\section{The second nuScenes bank}
The bank, the arms, the analysis, the criterion, and the wording that follows from each outcome were written down in \texttt{amendments/A6\_amendment.md} and committed, together with the bank file, before any model was run on these scenes. An addendum on the image width (Section~S9) was committed before the runs as well. These are commits in the authors' repository with the time of the authors' machine; they were not registered with a third party.

\emph{Bank.} The candidate scenes are the 840 scenes of nuScenes v1.0-trainval that are not among the ten scenes of v1.0-mini. An object is in scope if it belongs to one of six classes (pedestrian, car, truck, bus, bicycle, motorcycle), projects into the front-camera image, is within 40\,m, has a visibility of at least 40\%, and holds at least 10 LiDAR points. Every keyframe and every family is a candidate under the templates and margins of the paper. The selection draws, within each family, the same number of questions for every answer as far as candidates exist, with at most one question per frame and four per scene, on frames at least four keyframes apart. The keyframes are nominally 0.5\,s apart, and the amendment states this rule as ``at least 2\,s apart''; by the time stamps of the camera the smallest gap is 1.8\,s. For the two families whose options are class names, the two wrong options are chosen so that the correct name is the shortest, the middle, and the longest of the three about equally often. The result is 2718 questions on 2718 frames of 829 scenes (14 scenes with one question, 35 with two, 486 with three, 294 with four); 1550 questions are from Boston and 1168 from three areas of Singapore. Counting has 100 questions for each count from 1 to 5 and 53 for the count 6. Direction has 200 questions for each side. Nearest-class has 100 questions each for pedestrian, car, truck, and bus, 91 for bicycle, and 96 for motorcycle. Nearest-distance has 275 questions for each of the bands ``5 to 15 meters'' and ``over 15 meters'' and 24 for ``under 5 meters'', which is almost absent from a driving camera. Path-object has 100 questions each for pedestrian, car, and truck, 62 for bus, 27 for motorcycle, and 15 for bicycle. In the surface-cue audit the correct option is the shortest of the three in $0.350$ and the longest in $0.336$ of the questions; within the families the two values lie between $0.314$ and $0.401$ (\texttt{exp\_rev1/c2\_nusc/audit\_nusc2.txt}). The audit measures the length rank over all classes together. Within a class the rank is fixed by the construction (``Car'' and ``Bus'' are always the shortest of the three names, ``Pedestrian'' and ``Motorcycle'' always the longest), and the options of a counting question are three consecutive numbers. A rule that also looks at the option set can therefore score more than the answer-prior rule of the paper (<<J:nuscenes2/prior_from_mini/acc|.3f>>): learned on the other scenes in five folds, such a rule scores <<J:nuscenes2/prior_optionset_cv/acc|.3f>>. The readers without a scene, which see the options, score <<J:nuscenes2/arms/blind_3b/acc|.3f>> and <<J:nuscenes2/arms/blind_7b/acc|.3f>>.

\emph{Systems.} Perception: RF-DETR-Medium with COCO weights, detections accepted at a confidence of 0.50; range is the median of a ground-plane cue (camera height 1.51\,m from the calibration), a class-height cue (median heights of the annotated boxes of nuScenes-mini), and UniDepthV2; the bearing comes from the image column and the intrinsics. The readers are served by Ollama with 4-bit weights, as in the paper. The VLMs are run with the Transformers library, the weights of the model authors in bfloat16, and the image at $1600{\times}900$; the 7B VLM was also run through Ollama.

\settab{14}\begin{table}[h]\centering\footnotesize
\caption{Second nuScenes bank: serialized system minus VLM (Transformers), with 95\% intervals over the scenes. ``Without'' rows leave out all scenes of one location. ``Night'' and ``rain'' are the scenes whose description in nuScenes contains that word.}\label{tab:s14}
\begin{tabular}{@{}lccc@{}}
\toprule questions & number & 3B & 7B \\ \midrule
all & <<J:nuscenes2/n|d>> & <<JDCI:nuscenes2/contrast/E1_s_vs_vlm_3b>> & <<JDCI:nuscenes2/contrast/E2_s_vs_vlm_7b>> \\ \midrule
without Boston seaport & <<J:nuscenes2/contrast/E1_s_vs_vlm_3b/leave_location_out/boston-seaport/n|d>> & <<JDCI:nuscenes2/contrast/E1_s_vs_vlm_3b/leave_location_out/boston-seaport>> & <<JDCI:nuscenes2/contrast/E2_s_vs_vlm_7b/leave_location_out/boston-seaport>> \\
without Singapore Holland Village & <<J:nuscenes2/contrast/E1_s_vs_vlm_3b/leave_location_out/singapore-hollandvillage/n|d>> & <<JDCI:nuscenes2/contrast/E1_s_vs_vlm_3b/leave_location_out/singapore-hollandvillage>> & <<JDCI:nuscenes2/contrast/E2_s_vs_vlm_7b/leave_location_out/singapore-hollandvillage>> \\
without Singapore One North & <<J:nuscenes2/contrast/E1_s_vs_vlm_3b/leave_location_out/singapore-onenorth/n|d>> & <<JDCI:nuscenes2/contrast/E1_s_vs_vlm_3b/leave_location_out/singapore-onenorth>> & <<JDCI:nuscenes2/contrast/E2_s_vs_vlm_7b/leave_location_out/singapore-onenorth>> \\
without Singapore Queenstown & <<J:nuscenes2/contrast/E1_s_vs_vlm_3b/leave_location_out/singapore-queenstown/n|d>> & <<JDCI:nuscenes2/contrast/E1_s_vs_vlm_3b/leave_location_out/singapore-queenstown>> & <<JDCI:nuscenes2/contrast/E2_s_vs_vlm_7b/leave_location_out/singapore-queenstown>> \\ \midrule
Boston seaport only & <<J:nuscenes2/contrast/E1_s_vs_vlm_3b/location/boston-seaport/n|d>> & <<JDCI:nuscenes2/contrast/E1_s_vs_vlm_3b/location/boston-seaport>> & <<JDCI:nuscenes2/contrast/E2_s_vs_vlm_7b/location/boston-seaport>> \\
Singapore Holland Village only & <<J:nuscenes2/contrast/E1_s_vs_vlm_3b/location/singapore-hollandvillage/n|d>> & <<JDCI:nuscenes2/contrast/E1_s_vs_vlm_3b/location/singapore-hollandvillage>> & <<JDCI:nuscenes2/contrast/E2_s_vs_vlm_7b/location/singapore-hollandvillage>> \\
Singapore One North only & <<J:nuscenes2/contrast/E1_s_vs_vlm_3b/location/singapore-onenorth/n|d>> & <<JDCI:nuscenes2/contrast/E1_s_vs_vlm_3b/location/singapore-onenorth>> & <<JDCI:nuscenes2/contrast/E2_s_vs_vlm_7b/location/singapore-onenorth>> \\
Singapore Queenstown only & <<J:nuscenes2/contrast/E1_s_vs_vlm_3b/location/singapore-queenstown/n|d>> & <<JDCI:nuscenes2/contrast/E1_s_vs_vlm_3b/location/singapore-queenstown>> & <<JDCI:nuscenes2/contrast/E2_s_vs_vlm_7b/location/singapore-queenstown>> \\ \midrule
night & <<J:nuscenes2/contrast/E1_s_vs_vlm_3b/night/n|d>> & <<JDCI:nuscenes2/contrast/E1_s_vs_vlm_3b/night>> & <<JDCI:nuscenes2/contrast/E2_s_vs_vlm_7b/night>> \\
rain & <<J:nuscenes2/contrast/E1_s_vs_vlm_3b/rain/n|d>> & <<JDCI:nuscenes2/contrast/E1_s_vs_vlm_3b/rain>> & <<JDCI:nuscenes2/contrast/E2_s_vs_vlm_7b/rain>> \\ \midrule
counting & <<J:nuscenes2/n_family/counting|d>> & <<JDCI:nuscenes2/contrast/E1_s_vs_vlm_3b/family/counting>> & <<JDCI:nuscenes2/contrast/E2_s_vs_vlm_7b/family/counting>> \\
direction & <<J:nuscenes2/n_family/direction|d>> & <<JDCI:nuscenes2/contrast/E1_s_vs_vlm_3b/family/direction>> & <<JDCI:nuscenes2/contrast/E2_s_vs_vlm_7b/family/direction>> \\
nearest-class & <<J:nuscenes2/n_family/nearest_class|d>> & <<JDCI:nuscenes2/contrast/E1_s_vs_vlm_3b/family/nearest_class>> & <<JDCI:nuscenes2/contrast/E2_s_vs_vlm_7b/family/nearest_class>> \\
nearest-distance & <<J:nuscenes2/n_family/nearest_dist|d>> & <<JDCI:nuscenes2/contrast/E1_s_vs_vlm_3b/family/nearest_dist>> & <<JDCI:nuscenes2/contrast/E2_s_vs_vlm_7b/family/nearest_dist>> \\
path-object & <<J:nuscenes2/n_family/path_object|d>> & <<JDCI:nuscenes2/contrast/E1_s_vs_vlm_3b/family/path_object>> & <<JDCI:nuscenes2/contrast/E2_s_vs_vlm_7b/family/path_object>> \\
\bottomrule
\end{tabular}
\end{table}

\emph{Criterion.} The two comparisons that were fixed in advance are in the first row of Table~\ref{tab:s14}. For both, the sign-flip test over the scenes with 20000 random sign assignments gives $p<0.001$ (no random assignment reached the observed difference), and the interval stays above zero when the scenes of each location are left out in turn. Both are therefore firm in the sense fixed in advance. The table also gives the difference within each location, in the scenes at night and in rain, and for each family; the split by location was not specified in advance.

\emph{Further arms.} With the image width of the CODa camera, as in the first run of Section~S9, the serialized system scores <<J:nuscenes2/arms/sraw_3b/acc>> at 3B and <<J:nuscenes2/arms/sraw_7b/acc>> at 7B. The image width of the camera adds <<JD:nuscenes2/contrast/s_vs_sraw_3b>> and <<JD:nuscenes2/contrast/s_vs_sraw_7b>>, and without it the system is still above the VLM (<<JDCI:nuscenes2/contrast/sraw_vs_vlm_3b>> and <<JDCI:nuscenes2/contrast/sraw_vs_vlm_7b>>). The 7B VLM served by Ollama scores <<J:nuscenes2/arms/pixel_ollama_7b/acc>>; the VLM with the Transformers library differs from it by <<JDCI:nuscenes2/contrast/hf_vs_ollama_vlm_7b>>, and the serialized system minus the Ollama VLM is <<JDCI:nuscenes2/contrast/s_vs_ollama_vlm_7b>>. The VLM that receives the image and the serialized text exceeds the reader alone by <<JDCI:nuscenes2/contrast/hybrid_vs_s_3b>> at 3B and <<JDCI:nuscenes2/contrast/hybrid_vs_s_7b>> at 7B, and the VLM alone by <<JD:nuscenes2/contrast/hybrid_vs_vlm_3b>> and <<JD:nuscenes2/contrast/hybrid_vs_vlm_7b>>. With annotated objects the readers exceed the serialized system by <<JD:nuscenes2/contrast/gt_vs_s_3b>> and <<JD:nuscenes2/contrast/gt_vs_s_7b>>. The readers without a scene answer every question with an option letter and score <<J:nuscenes2/arms/blind_3b/acc>> at 3B and <<J:nuscenes2/arms/blind_7b/acc>> at 7B. In the nearest-distance family the 3B VLM chooses a nearer band than the correct one in <<J:nuscenes2/band_bias/hf_pixel_3b/nearer|d>> of the <<J:nuscenes2/band_bias/hf_pixel_3b/n|d>> questions and a farther one in <<J:nuscenes2/band_bias/hf_pixel_3b/farther|d>>; the 7B VLM in <<J:nuscenes2/band_bias/hf_pixel_7b/nearer|d>> and <<J:nuscenes2/band_bias/hf_pixel_7b/farther|d>>; the serialized system at 7B in <<J:nuscenes2/band_bias/s_7b/nearer|d>> and <<J:nuscenes2/band_bias/s_7b/farther|d>>.

<<S14R>>
\clearpage
\section{Accuracy against model size}
Fig.~S1 plots the values of the table of the paper that gives the accuracy by model size. The point to read from it is where each model lies relative to the answer-prior rule (horizontal line) and to the readers on ground-truth objects.

\begin{center}
\includegraphics[width=0.5\linewidth]{fig_scale.pdf}

\small Fig.~S1. Accuracy on the confirmatory bank against model size. Filled circles: the serialized system. Squares: the same readers on ground-truth objects. Open triangles and diamonds: VLMs; the Qwen3-VL point is the run with 1,024 output tokens. Horizontal dashed line: the answer-prior rule, which sees no scene.
\end{center}
\end{document}
"""


def pc1(key):
    a, b = key.split(":", 1)
    r = PC[a][b]; lo, hi = r["ci"]
    return f"${r['delta']:+.4f}{'^{*}' if r['sig'] else ''}$ $[{lo:+.4f},\\,{hi:+.4f}]$"


def pcn(k):
    r = PC[k]; lo, hi = r["ci"]
    return f"${r['delta']:.4f}{'^{*}' if r['sig'] else ''}$ $[{lo:.4f},\\,{hi:.4f}]$"


import re
TEX = TEX.replace("<<S1>>", NL.join(s1)).replace("<<S2>>", NL.join(s2)).replace("<<S2B>>", NL.join(s2b)).replace("<<S2C>>", NL.join(s2c))
TEX = TEX.replace("<<S9>>", NL.join(s9)).replace("<<PR>>", str(ps["right"])).replace("<<PW>>", str(ps["wrong"]))
TEX = TEX.replace("<<JK3>>", f"$[{jk['primary_3b'][0]:+.4f},\\,{jk['primary_3b'][1]:+.4f}]$").replace("<<JK7>>", f"$[{jk['primary_7b'][0]:+.4f},\\,{jk['primary_7b'][1]:+.4f}]$")
TEX = re.sub(r"<<PC1:([^<>]+)>>", lambda m: pc1(m.group(1)), TEX)
TEX = re.sub(r"<<PCN:([^<>]+)>>", lambda m: pcn(m.group(1)), TEX)
TEX = re.sub(r"<<PC:([^<>]+)>>", lambda m: pc(m.group(1)), TEX)
TEX = re.sub(r"<<O:([^<>]+)>>", lambda m: str(O[m.group(1)]), TEX)
# Section S14, protocol R on the second nuScenes bank (A6: run because protocol R changed the
# accuracy of the VLM on the confirmatory bank by more than 0.02)
_n2 = R["nuscenes2"]
if all(k in _n2["arms"] for k in ("hf_reason_3b", "hf_reason_7b", "readerR_3b", "readerR_7b")):
    S14R = (r"\emph{Protocol R on this bank.} Amendment A6 specified that protocol R (Section~S13) is also run on this bank if it changes the accuracy of the VLM on the confirmatory bank by $0.02$ or more, which it did. "
            r"Under protocol R the VLM scores <<J:nuscenes2/arms/hf_reason_3b/acc>> at 3B and <<J:nuscenes2/arms/hf_reason_7b/acc>> at 7B (parsed: <<J:nuscenes2/arms/hf_reason_3b/parse|.3f>> and <<J:nuscenes2/arms/hf_reason_7b/parse|.3f>>), "
            r"and the reader <<J:nuscenes2/arms/readerR_3b/acc>> and <<J:nuscenes2/arms/readerR_7b/acc>> (parsed: <<J:nuscenes2/arms/readerR_3b/parse|.3f>> and <<J:nuscenes2/arms/readerR_7b/parse|.3f>>). "
            r"Against the arms of the paper that answer with the letter, protocol R changes the VLM by <<JDCI:nuscenes2/contrast/vlmR_vs_vlm_3b>> at 3B and <<JDCI:nuscenes2/contrast/vlmR_vs_vlm_7b>> at 7B, and the reader by <<JDCI:nuscenes2/contrast/readerR_vs_s_3b>> and <<JDCI:nuscenes2/contrast/readerR_vs_s_7b>>, respectively. No output of these four arms was cut at 512 tokens. "
            r"The reader minus the VLM, both under protocol R, is <<JDCI:nuscenes2/contrast/readerR_vs_vlmR_3b>> at 3B and <<JDCI:nuscenes2/contrast/readerR_vs_vlmR_7b>> at 7B; "
            r"the serialized system of the paper minus the VLM under protocol R is <<JDCI:nuscenes2/contrast/s_vs_vlmR_3b>> and <<JDCI:nuscenes2/contrast/s_vs_vlmR_7b>>.")
else:
    S14R = r"\emph{Protocol R on this bank.} RUNS IN PROGRESS --- NOT FOR RELEASE."
TEX = TEX.replace("<<S14R>>", S14R)
# statements made in words in Sections S13 and S14
_pc = R["protocol_r"]["contrast"]
for _k in ("readerR_vs_vlmR", "scoped_vs_vlmR", "vlmR_vs_vlm"):
    for _s in ("3b", "7b"):
        assert _pc[f"{_k}_{_s}"]["signflip_p"] < 0.005 and _pc[f"{_k}_{_s}"]["loso_cross_zero"] == 0, (_k, _s)
for _s in ("3b", "7b"):
    assert R["protocol_r"]["arms"][f"vlmR_{_s}"]["acc_parsed"] < R["acc"][f"pixel_{_s}"]
assert all(_n2.get("cut_at_limit", {}).get(k, 0) == 0 for k in ("hf_reason_3b", "hf_reason_7b", "readerR_3b", "readerR_7b"))
for _k in ("E1_s_vs_vlm_3b", "E2_s_vs_vlm_7b"):
    assert _n2["contrast"][_k]["signflip_p"] < 0.001 and _n2["contrast"][_k]["firm"], _k
assert _n2["arms"]["blind_3b"]["parse"] == 1.0 and _n2["arms"]["blind_7b"]["parse"] == 1.0


S12_PAIRS = [(r"\textsc{Scoped} $-$ VLM (primary), 3B", "primary_3b"), ("7B", "primary_7b"),
             ("stereo cue off $-$ VLM, 3B", "nostereo_vs_pixel_3b"), ("7B", "nostereo_vs_pixel_7b"),
             (r"one-pass pair $-$ VLM$^{\dagger}$, 3B", "light1_vs_pixelrerun_3b"), ("7B", "light1_vs_pixelrerun_7b"),
             (r"RF-DETR stack $-$ VLM$^{\dagger}$, 3B", "rfdetr_vs_pixelrerun_3b"), ("7B", "rfdetr_vs_pixelrerun_7b"),
             (r"VLM + text $-$ VLM$^{\dagger}$, 3B", "hybrid_vs_pixelrerun_3b"), ("7B", "hybrid_vs_pixelrerun_7b"),
             (r"VLM + text $-$ \textsc{Scoped}$^{\dagger}$, 3B", "hybrid_vs_ctrl_scoped_3b"), ("7B", "hybrid_vs_ctrl_scoped_7b"),
             (r"\textsc{Scoped} $-$ \textsc{Flat}, 3B", "scoped_vs_flat_3b"), ("7B", "scoped_vs_flat_7b"),
             (r"FT-VLM $-$ \textsc{Scoped}, 3B", "ftvlm_vs_scoped_3b"), ("7B", "ftvlm_vs_scoped_7b"),
             ("FT-Text $-$ FT-VLM, 3B", "fttext_vs_ftvlm_3b"),
             ("1.5B reader $-$ moondream", "scoped1.5b_vs_moondream"), ("1.5B reader $-$ Qwen3-VL 2B", "scoped1.5b_vs_q3vl2b_think"),
             ("Qwen3 reader $-$ Qwen3-VL, 4B", "q3txt4b_vs_q3vl4b"), ("8B", "q3txt8b_vs_q3vl8b"),
             (r"\midrule \textsc{Flat} $-$ VLM, 3B", "flat_vs_pixel_3b"), ("7B", "flat_vs_pixel_7b")]
assert len(S12_PAIRS) == 23
TEX = TEX.replace("<<S12ROWS>>", NL.join(
    f"{lab} & " + " & ".join(f"<<JDCI:balanced/min{m}/contrast/{key}>>" for m in (5, 10, 1)) + r" \\" for lab, key in S12_PAIRS))


def jfill(m):
    kind, _, key = m.group(1).partition(":")
    path, _, fmt = key.partition("|")
    cur = R
    for part in path.split("/"):
        cur = cur[part]
    if kind == "J":
        return format(cur, fmt or ".4f")
    if kind == "JD":
        return sgn(cur["delta"], cur["star"])
    if kind == "JDCI":
        return sgn(cur["delta"], cur["star"]) + " " + ci(cur)
    if kind == "JP":
        return f"{cur:.4f}" if cur >= 0.0001 else "$<$0.0001"
    if kind == "JROW":
        return f"{cur['acc']:.4f} & " + " & ".join(f"{cur['family'][f]:.3f}" for f in FAMS) + f" & {cur['parse']:.3f}"
    raise KeyError(m.group(0))


TEX = re.sub(r"<<(J[A-Z]*:[^<>]+)>>", jfill, TEX)
left = re.findall(r"<<[^<>]+>>", TEX)
assert not left, left
(ROOT / "supplement.tex").write_text(TEX, encoding="utf-8", newline="\n")
print("wrote supplement.tex;", len(s1), "arms in S1;", len(s2), "contrasts in S2")
