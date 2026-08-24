# Amendment A4 -- sweep summary (raw, no interpretation)

## curve points (accuracy vs parameters)

| line | arm | bank | model | params | n | acc | unparsed% |
|---|---|---|---|---|---|---|---|
| D0@N2 | D0_05b | n2 | qwen2.5:0.5b | 0.49B | 3971 | 0.4132 | 0.00 |
| D0@N2 | D0_15b | n2 | qwen2.5:1.5b | 1.54B | 3971 | 0.4591 | 0.00 |
| D0@N2 | D0_3b | n2 | qwen2.5:3b | 3.09B | 3971 | 0.5014 | 0.23 |
| D0@N2 | D0_7b | n2 | qwen2.5:7b | 7.62B | 3971 | 0.5860 | 0.00 |
| D0@cf | D0_05b | cf | qwen2.5:0.5b | 0.49B | 1328 | 0.5143 | 1.51 |
| D0@cf | D0_15b | cf | qwen2.5:1.5b | 1.54B | 1328 | 0.7357 | 1.43 |
| D0@cf | D0_3b | cf | qwen2.5:3b | 3.09B | 1328 | 0.7673 | 0.53 |
| D0@cf | D0_7b | cf | qwen2.5:7b | 7.62B | 1328 | 0.7892 | 0.75 |
| D1@N2 | D1_05b | n2 | qwen2.5:0.5b | 0.49B | 3971 | 0.4336 | 0.03 |
| D1@N2 | D1_15b | n2 | qwen2.5:1.5b | 1.54B | 3971 | 0.4666 | 0.00 |
| D1@N2 | D1_3b | n2 | qwen2.5:3b | 3.09B | 3971 | 0.4422 | 0.23 |
| D1@N2 | D1_7b | n2 | qwen2.5:7b | 7.62B | 3971 | 0.5963 | 0.00 |
| GT-D0@cf | GT_05b | gtcf | qwen2.5:0.5b | 0.49B | 1328 | 0.6152 | 0.60 |
| GT-D0@cf | GT_15b | gtcf | qwen2.5:1.5b | 1.54B | 1328 | 0.8660 | 0.00 |
| GT-D0@cf | GT_3b | gtcf | qwen2.5:3b | 3.09B | 1328 | 0.9247 | 0.08 |
| GT-D0@cf | GT_7b | gtcf | qwen2.5:7b | 7.62B | 1328 | 0.9699 | 0.00 |
| pixel-deviation@cf | PXDEV_q3vl2b | cf | qwen3-vl:2b | 2.13B | 1328 | 0.5527 | 30.95 |
| pixel@N2 | PX_moondream | n2 | moondream | 1.42B | 3974 | 0.2720 | 0.00 |
| pixel@N2 | PIXEL_3b | n2 | qwen2.5vl:3b | 3.75B | 3974 | 0.4899 | 0.10 |
| pixel@N2 | PX_llavaphi3 | n2 | llava-phi3 | 3.82B | 3974 | 0.4867 | 0.23 |
| pixel@N2 | PIXEL_7b | n2 | qwen2.5vl:7b | 8.29B | 3974 | 0.5448 | 0.05 |
| pixel@cf | PX_moondream | cf | moondream | 1.42B | 1328 | 0.6114 | 0.83 |
| pixel@cf | PIXEL_3b | cf | qwen2.5vl:3b | 3.75B | 1328 | 0.6913 | 0.23 |
| pixel@cf | PX_llavaphi3 | cf | llava-phi3 | 3.82B | 1328 | 0.6468 | 0.00 |
| pixel@cf | PIXEL_7b | cf | qwen2.5vl:7b | 8.29B | 1328 | 0.7462 | 0.00 |

## contrasts (21 clusters, B=20000, seed 20260809; cross-family rows are descriptive per A4)

| contrast | bank | arms | Delta | 95% CI | sig |
|---|---|---|---|---|---|
| S1 D0_0.5b vs moondream@cf (cross-family, descriptive) | cf | D0_05b vs PX_moondream | -0.0971 | [-0.1456, -0.0632] | * |
| S1 D0_1.5b vs moondream@cf (cross-family, descriptive) | cf | D0_15b vs PX_moondream | +0.1242 | [+0.0732, +0.1523] | * |
| S1 D0_1.5b vs llava-phi3@cf (cross-family, descriptive) | cf | D0_15b vs PX_llavaphi3 | +0.0889 | [+0.0228, +0.1321] | * |
| S2 D1 vs D0 @N2, 0.5b (within-text) | n2 | D1_05b vs D0_05b | +0.0204 | [+0.0020, +0.0352] | * |
| S2 D1 vs D0 @N2, 1.5b (within-text) | n2 | D1_15b vs D0_15b | +0.0076 | [-0.0040, +0.0164] |  |
| S2 D1 vs D0 @N2, 3b (within-text) | n2 | D1_3b vs D0_3b | -0.0592 | [-0.0825, -0.0274] | * |
| S2 D1 vs D0 @N2, 7b (within-text) | n2 | D1_7b vs D0_7b | +0.0103 | [-0.0163, +0.0321] |  |
| S2 D1_0.5b vs moondream@N2 (cross-family, descriptive) | n2 | D1_05b vs PX_moondream | +0.1617 | [+0.1365, +0.1795] | * |
| S2 D1_1.5b vs moondream@N2 (cross-family, descriptive) | n2 | D1_15b vs PX_moondream | +0.1947 | [+0.1744, +0.2245] | * |
| GT curve step 0.5b vs 1.5b | gtcf | GT_05b vs GT_15b | -0.2508 | [-0.2800, -0.2232] | * |
| GT curve step 1.5b vs 3b | gtcf | GT_15b vs GT_3b | -0.0587 | [-0.0894, -0.0367] | * |
| GT curve step 3b vs 7b | gtcf | GT_3b vs GT_7b | -0.0452 | [-0.0551, -0.0337] | * |

## unparsed scan (discipline 6: >20% unusable)

- D0_05b@cf: 20/1328 (1.51%)
- D0_05b@n2: 0/3971 (0.00%)
- D0_15b@cf: 19/1328 (1.43%)
- D0_15b@n2: 0/3971 (0.00%)
- D0_3b@cf: 7/1328 (0.53%)
- D0_3b@n2: 9/3971 (0.23%)
- D0_7b@cf: 10/1328 (0.75%)
- D0_7b@n2: 0/3971 (0.00%)
- D1_05b@n2: 1/3971 (0.03%)
- D1_15b@n2: 0/3971 (0.00%)
- D1_3b@n2: 9/3971 (0.23%)
- D1_7b@n2: 0/3971 (0.00%)
- GT_05b@gtcf: 8/1328 (0.60%)
- GT_15b@gtcf: 0/1328 (0.00%)
- GT_3b@gtcf: 1/1328 (0.08%)
- GT_7b@gtcf: 0/1328 (0.00%)
- PIXEL_3b@cf: 3/1328 (0.23%)
- PIXEL_3b@n2: 4/3974 (0.10%)
- PIXEL_7b@cf: 0/1328 (0.00%)
- PIXEL_7b@n2: 2/3974 (0.05%)
- PXDEV_q3vl2b@cf: 411/1328 (30.95%)  **OVER 20%**
- PX_llavaphi3@cf: 0/1328 (0.00%)
- PX_llavaphi3@n2: 9/3974 (0.23%)
- PX_moondream@cf: 11/1328 (0.83%)
- PX_moondream@n2: 0/3974 (0.00%)

## phase-2 artefact index

- step 1: exp2_runs/seq20_diagnostic.md
- step 2: exp2_runs/baselines.md (+ bootstrap vs readers)
- step 2b: exp2_runs/baselines_n1n2.md
- step 3: exp2_runs/occlusion_audit.json + clean-subset contrasts in LOG.md
- step 7: exp2_runs/compute_table.md

**FLAGGED ARMS (>20% unparsed):** PXDEV_q3vl2b@cf
