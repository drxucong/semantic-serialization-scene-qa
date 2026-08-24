# Blind audit pack (reviewer 8.2)

**DATA GAP, stated up front:** the only existing blind runs are on the
DEVELOPMENT bank (qa_coda, 1366 items). No blind arm has ever been run on
the confirmatory bank. A cf blind run costs ~30 min (2 scales x 1328
no-scene calls) if wanted; not run without approval (unplanned arm).

## blind qwen2.5:3b  (n=1366, bank=DEVELOPMENT (qa_coda, n=1366; NOT qa_confirm), source=outputs\phase10\coda\results_qwen2.5_3b\blind__clean__forced.jsonl)

overall = 0.4341

- counting: 0.3792 (n=298)
- direction: 0.4110 (n=309)
- nearest_class: 0.4393 (n=239)
- nearest_dist: 0.5323 (n=248)
- path_object: 0.4265 (n=272)

## blind qwen2.5:7b  (n=1366, bank=DEVELOPMENT (qa_coda, n=1366; NOT qa_confirm), source=outputs\phase10\coda\results_qwen2.5_7b\blind__clean__forced.jsonl)

overall = 0.4129

- counting: 0.2819 (n=298)
- direction: 0.3948 (n=309)
- nearest_class: 0.3264 (n=239)
- nearest_dist: 0.4798 (n=248)
- path_object: 0.5919 (n=272)

## gold letter distribution x family (forced 3-choice, qa_confirm)

| family | A | B | C | n |
|---|---|---|---|---|
| counting | 108 | 101 | 93 | 302 |
| direction | 94 | 103 | 92 | 289 |
| nearest_class | 92 | 64 | 87 | 243 |
| nearest_dist | 84 | 84 | 86 | 254 |
| path_object | 84 | 81 | 75 | 240 |

## counting distractor construction rule

scripts/coda/make_confirm_qa.py lines 139-157: per-item feasible positions {min, mid, max} chosen to balance the correct answer's rank (cpos counter); distractor sets {k+1,k+2} / {k-1,k+1} / {k-2,k-1}; k>6 skipped; abstain never correct (stripped by the forced track).