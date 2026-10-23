# C1 external evaluation: nuScenes mini, CAM_FRONT, 347 items, 10 scenes

| arm | n | acc | parse |
|---|---|---|---|
| pixel_3b | 347 | 0.3429 | 0.5965 |
| pixel_7b | 347 | 0.6628 | 1.0000 |
| d0_rfdetr_3b | 347 | 0.7493 | 0.9971 |
| d0_rfdetr_7b | 347 | 0.7867 | 1.0000 |
| d0_gt_3b | 347 | 0.9020 | 1.0000 |
| d0_gt_7b | 347 | 0.9452 | 1.0000 |
| blind_3b | 347 | 0.3112 | 1.0000 |
| blind_7b | 347 | 0.2997 | 1.0000 |

| contrast | 3B | 7B |
|---|---|---|
| serialized (zero-shot RF-DETR) − pixel | +0.4063 [+0.3201, +0.5037]* | +0.1239 [+0.0580, +0.1863]* |
| GT oracle − serialized | +0.1527 [+0.0912, +0.2167]* | +0.1585 [+0.1080, +0.2090]* |
| serialized − blind | +0.4380 [+0.3533, +0.5332]* | +0.4870 [+0.4311, +0.5471]* |
| pixel − blind | +0.0317 [-0.0773, +0.1499] | +0.3631 [+0.3065, +0.4219]* |

Per-family accuracy (3B / 7B):
- counting: pixel: 0.291 / 0.573; d0_rfdetr: 0.547 / 0.658; d0_gt: 0.812 / 0.932; blind: 0.274 / 0.214
- direction: pixel: 0.328 / 0.875; d0_rfdetr: 0.734 / 0.750; d0_gt: 0.828 / 0.828; blind: 0.281 / 0.391
- nearest_class: pixel: 0.537 / 0.881; d0_rfdetr: 0.940 / 0.910; d0_gt: 0.985 / 1.000; blind: 0.448 / 0.403
- nearest_dist: pixel: 0.061 / 0.258; d0_rfdetr: 0.833 / 0.833; d0_gt: 1.000 / 1.000; blind: 0.303 / 0.091
- path_object: pixel: 0.727 / 0.939; d0_rfdetr: 0.939 / 0.970; d0_gt: 1.000 / 1.000; blind: 0.242 / 0.636