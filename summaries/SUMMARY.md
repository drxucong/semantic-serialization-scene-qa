# Amendment A3 -- contrast summary (raw, no interpretation)

21 clusters, B=20000, seed 20260809, percentile CI. `*` = CI excludes 0.

| contrast | bank | arms | family | Delta | 95% CI | sig |
|---|---|---|---|---|---|---|
| P1 D1 vs PIXEL (all) | cf | D1_3b vs PIXEL_3b | all | +0.0218 | [-0.0234, +0.0515] |  |
| P1 counting | cf | D1_3b vs PIXEL_3b | counting | +0.1424 | [+0.0466, +0.2379] | * |
| P1 nearest-distance | cf | D1_3b vs PIXEL_3b | nearest_dist | -0.0512 | [-0.2111, +0.0994] |  |
| band vocab value (leak bound) | cf | D0_3b vs D1_3b | all | +0.0542 | [+0.0381, +0.0730] | * |
| discretisation beyond vocab | cf | D2_3b vs D1_3b | all | +0.0158 | [+0.0084, +0.0256] | * |
| negative control | cf | D3_3b vs PIXEL_3b | all | +0.0248 | [-0.0174, +0.0549] |  |
| P2 D0 vs PIXEL on N1 | n1 | D0_3b vs PIXEL_3b | all | +0.0414 | [+0.0050, +0.0677] | * |
| D1 vs PIXEL on N1 | n1 | D1_3b vs PIXEL_3b | all | -0.0015 | [-0.0477, +0.0293] |  |
| D0 vs PIXEL on N2 | n2 | D0_3b vs PIXEL_3b | all | +0.0118 | [-0.0196, +0.0360] |  |
| P3 D1 vs PIXEL on N2 | n2 | D1_3b vs PIXEL_3b | all | -0.0473 | [-0.0764, -0.0064] | * |
| reference Dconf (for P2) | cf | D0_3b vs PIXEL_3b | all | +0.0761 | [+0.0404, +0.0997] | * |
| P1 D1 vs PIXEL (all) | cf | D1_7b vs PIXEL_7b | all | +0.0075 | [-0.0303, +0.0337] |  |
| P1 counting | cf | D1_7b vs PIXEL_7b | counting | +0.1325 | [+0.0565, +0.1906] | * |
| P1 nearest-distance | cf | D1_7b vs PIXEL_7b | nearest_dist | -0.0157 | [-0.0923, +0.0492] |  |
| band vocab value (leak bound) | cf | D0_7b vs D1_7b | all | +0.0354 | [+0.0207, +0.0538] | * |
| discretisation beyond vocab | cf | D2_7b vs D1_7b | all | +0.0075 | [-0.0024, +0.0174] |  |
| negative control | cf | D3_7b vs PIXEL_7b | all | -0.0015 | [-0.0381, +0.0258] |  |
| P2 D0 vs PIXEL on N1 | n1 | D0_7b vs PIXEL_7b | all | +0.0738 | [+0.0281, +0.1039] | * |
| D1 vs PIXEL on N1 | n1 | D1_7b vs PIXEL_7b | all | +0.0557 | [+0.0064, +0.0861] | * |
| D0 vs PIXEL on N2 | n2 | D0_7b vs PIXEL_7b | all | +0.0413 | [+0.0021, +0.0738] | * |
| P3 D1 vs PIXEL on N2 | n2 | D1_7b vs PIXEL_7b | all | +0.0516 | [-0.0014, +0.0970] |  |
| reference Dconf (for P2) | cf | D0_7b vs PIXEL_7b | all | +0.0429 | [+0.0071, +0.0694] | * |

| P2 | Delta_conf | Delta_N1 | attenuation | verdict |
|---|---|---|---|---|
| P2 attenuation 3b | Delta_conf +0.0761 | Delta_N1 +0.0414 | attenuation 0.456 | P2 HOLDS (<0.5) |
| P2 attenuation 7b | Delta_conf +0.0429 | Delta_N1 +0.0738 | attenuation -0.720 | P2 HOLDS (<0.5) |
