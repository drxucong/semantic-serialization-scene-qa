# Arm definitions (appendix table draft)

| arm | one-line definition | source run dir |
|---|---|---|
| PIXEL_3b/7b @cf | qwen2.5vl on raw cam0 image, forced 3-choice, T=0, 8 tok | outputs/phase10/coda/results_cf_px3b_robust, results_cf_px_7b |
| PIXEL @N1/N2 | same protocol on frozen N1/N2 banks | exp1_runs/infer/n{1,2}_px_{3b,7b} |
| D0 (=SCOPED, v15_d5) | decision-scoped serializer: counts + corridor/overall arg-mins + per-class band+sector; per-object rows only for counting | outputs/phase10/coda/results_cf_v15_*, exp1_runs/infer/n{1,2}_d0_*, exp2_runs/infer/cf_d0_{0.5b,1.5b} |
| D1 (NUMERIC) | D0 with every distance as one-decimal metres, epsilon flags dropped | exp1_runs/infer/cf_d1_*, n{1,2}_d1_*, exp2_runs/infer/n2_d1_{0.5b,1.5b} |
| D2 (NUMERIC+ALT) | D1 + close/mid/far tags at 4/12 m (disjoint vocabulary) | exp1_runs/infer/cf_d2_* |
| D3 (ALT-ONLY) | tags only, no numerals (negative control) | exp1_runs/infer/cf_d3_* |
| FLAT (v9) | full per-object list serializer (pre-scoping production text) | outputs/phase10/coda/results_cf_v9_* |
| GT-D0 | D0 rendered from ground-truth object states (perception removed) | exp2_runs/infer/gtcf_d0_* |
| BASE_rule/logreg/gbtree | option-aware deterministic scorers over compiled state, fit on dev | exp2_runs/baseline_preds*.csv |
| blind | reader answers from question+options only, no scene | outputs/phase10/coda/results_qwen2.5_{3b,7b}/blind__* |
| pixel sweep arms | moondream, llava-phi3 on cf/N2 | exp2_runs/infer/px_* |
| pixel deviation arm | qwen3-vl:2b, 1024-token thinking budget (descriptive only) | exp3_runs/infer/px_q3vl2b_cf_t1024 |
