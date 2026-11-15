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
    r = N["contrast_family_7b"][f]
    s9.append(f"{FN[f]} & {r['n']} & {r['clusters']} & {sgn(r['delta'], r['star'])} & {ci(r)} & {r['net_items']:+d} \\\\")
r = N["contrast"]["ser_vs_pixel_7b"]
s9.append(f"\\midrule all & {r['n']} & {r['clusters']} & {sgn(r['delta'], r['star'])} & {ci(r)} & {r['net_items']:+d} \\\\")

NL = "\n"
TEX = r"""\documentclass[10pt]{article}
\usepackage[margin=0.9in]{geometry}
\usepackage{booktabs,longtable,array,amsmath,url}
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
This supplement holds Tables S1, S2, S4 to S7, and S10 and Sections S2, S3, S8, and S11, to which the paper refers, and further details in Section S9. A table carries the number of its section; Section S3 has no table. All values are on the confirmatory bank (1328 questions, 21 recordings) unless a caption says otherwise. Intervals are 95\% intervals of the paired bootstrap over recordings that Section VI of the paper defines; $^{*}$ marks an interval that excludes zero. Tables S1, S2, S8, and S9 are computed from the released per-question predictions and logs by three scripts of the release (\texttt{exp\_rev1/analysis/rev2\_analysis.py}, \texttt{b10\_e2e\_numbers.py}, and \texttt{build\_supplement.py}).

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
All values of the table of board measurements in the paper, part (b), come from one session (25\,W mode, desktop running, llama.cpp commit 11fe021 built with CUDA, all layers on the GPU, prompt cache in host memory disabled). Table~\ref{tab:s8} adds values that the paper does not show.
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

\section{The nuScenes-mini bank}
\settab{9}\begin{table}[h]\centering\footnotesize
\caption{nuScenes-mini bank, serialized system minus VLM at 7B, by family. ``Net'' is the number of questions that only the serialized system answers correctly minus the number that only the VLM answers correctly. Intervals resample the 10 scenes (8 scenes contain path-object questions).}\label{tab:s9}
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
later additions, as committed & \texttt{amendments/A3} to \texttt{A5}, \texttt{exp\_rev1/B123\_PREREG.md} \\
analysis of this paper (all comparisons) & \texttt{exp\_rev1/analysis/rev2\_analysis.py}, \texttt{rev2\_results.json} \\
analysis of the two primary comparisons & \texttt{analysis/confirm\_analysis.py}, \texttt{analysis/stats\_for\_revision.txt} \\
board measurements & \texttt{exp\_rev1/b10\_boards/} \\
\bottomrule
\end{tabular}
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
left = re.findall(r"<<[^<>]+>>", TEX)
assert not left, left
(ROOT / "supplement.tex").write_text(TEX, encoding="utf-8", newline="\n")
print("wrote supplement.tex;", len(s1), "arms in S1;", len(s2), "contrasts in S2")
