# Frozen baselines evaluated as-is on N1/N2 (no refit, no parser repair)

## n1

| system | overall | counting | direction | nearest_class | nearest_dist | path_object |
|---|---|---|---|---|---|---|
| BASE_rule | 0.3479 | 0.358 | 0.325 | 0.379 | 0.331 | 0.350 |
| BASE_logreg | 0.3479 | 0.358 | 0.325 | 0.379 | 0.331 | 0.350 |
| BASE_gbtree | 0.3479 | 0.358 | 0.325 | 0.379 | 0.331 | 0.350 |

## n2

| system | overall | counting | nearest_class | nearest_dist |
|---|---|---|---|---|
| BASE_rule | 0.3510 | 0.382 | 0.325 | 0.346 |
| BASE_logreg | 0.3332 | 0.328 | 0.325 | 0.346 |
| BASE_gbtree | 0.3183 | 0.286 | 0.325 | 0.344 |

