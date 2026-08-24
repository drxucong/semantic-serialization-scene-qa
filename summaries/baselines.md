# Option-aware deterministic baselines (fit on dev, evaluated on cf)

Features used by B2 (frozen list):

```
fam_counting, fam_direction, fam_nearest_class, fam_nearest_dist, fam_path_object, opt_is_number, opt_is_band, opt_is_direction, opt_is_class, rule_score, rule_pick, cnt_absdiff_conf, cnt_absdiff_total, unc_count, band_match, near_dist_m, band_edge_margin_m, sector_match, sector_margin_px, is_nearest_class, is_runnerup_class, nearest_class_margin_m, is_path_argmin, is_path_runnerup, path_margin_m, winner_det_conf, winner_lowconf, n_objects, n_classes, queried_class_present
```

| system | cf overall | counting | direction | nearest_class | nearest_dist | path_object |
|---|---|---|---|---|---|---|
| BASE_rule | 0.8027 | 0.520 | 0.889 | 0.889 | 0.886 | 0.879 |
| BASE_logreg | 0.8080 | 0.540 | 0.889 | 0.889 | 0.886 | 0.883 |
| BASE_gbtree | 0.8245 | 0.616 | 0.889 | 0.889 | 0.886 | 0.879 |

(dev-split accuracies: rule 0.7767, logreg 0.7906, gbtree 0.8411; option-blind closed-form reference from the paper: .619)

## 配对 bootstrap(21 簇、B=20000、种子 20260809)

| 对比 | Δ | 95% CI | sig |
|---|---|---|---|
| D0_7b vs BASE_gbtree | −0.0354 | [−0.0604, −0.0159] | * |
| D0_3b vs BASE_gbtree | −0.0572 | [−0.0803, −0.0354] | * |
| BASE_gbtree vs PIXEL_7b | +0.0783 | [+0.0480, +0.1078] | * |

参照(cf 总体):D0_3b .7674,D0_7b .7891,PIXEL_3b .6913,PIXEL_7b .7462,
option-blind 闭式参照(论文旧值).619。
