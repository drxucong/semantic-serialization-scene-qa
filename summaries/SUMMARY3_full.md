# Phase-3 SUMMARY3 -- raw numbers, no interpretation

A5 (1f47f6f) + addendum (71812cc). Deviations recorded inline; deviation arm descriptive only.

## arm accuracies (cf, forced 3-choice)

| arm | n | acc | unparsed% | per-family |
|---|---|---|---|---|
| BLIND_3b | 1328 | 0.4142 | 0.0 | counting=0.374 direction=0.439 nearest_c=0.342 nearest_d=0.492 path_obje=0.425 |
| BLIND_7b | 1328 | 0.4089 | 0.0 | counting=0.278 direction=0.439 nearest_c=0.313 nearest_d=0.437 path_obje=0.604 |
| Q3TXT4B_D0 | 1328 | 0.7824 | 1.28 | counting=0.536 direction=0.858 nearest_c=0.885 nearest_d=0.78 path_obje=0.9 |
| Q3TXT8B_D0 | 1328 | 0.7809 | 1.28 | counting=0.54 direction=0.872 nearest_c=0.889 nearest_d=0.772 path_obje=0.875 |
| Q3VL4B | 1328 | 0.7229 | 0.0 | counting=0.46 direction=0.903 nearest_c=0.934 nearest_d=0.449 path_obje=0.912 |
| Q3VL8B | 1328 | 0.7575 | 0.0 | counting=0.44 direction=0.903 nearest_c=0.926 nearest_d=0.622 path_obje=0.954 |
| PXDEV_t1024 | 1328 | 0.7432 | 1.13 | counting=0.414 direction=0.879 nearest_c=0.93 nearest_d=0.634 path_obje=0.921 |
| ZS3B_low | 1328 | 0.6777 | 0.08 | counting=0.417 direction=0.803 nearest_c=0.84 nearest_d=0.516 path_obje=0.863 |
| FT3B_low | 1328 | 0.8441 | 0.0 | counting=0.586 direction=0.889 nearest_c=0.951 nearest_d=0.906 path_obje=0.942 |
| D0_3b | 1328 | 0.7673 | 0.53 | counting=0.566 direction=0.747 nearest_c=0.889 nearest_d=0.776 path_obje=0.912 |
| D0_7b | 1328 | 0.7892 | 0.75 | counting=0.583 direction=0.851 nearest_c=0.881 nearest_d=0.768 path_obje=0.904 |
| PIXEL_3b | 1328 | 0.6913 | 0.23 | counting=0.43 direction=0.785 nearest_c=0.848 nearest_d=0.539 path_obje=0.908 |
| PIXEL_7b | 1328 | 0.7462 | 0.0 | counting=0.447 direction=0.875 nearest_c=0.942 nearest_d=0.579 path_obje=0.946 |
| FT7B_low | 1328 | 0.8577 | 0.0 | counting=0.606 direction=0.92 nearest_c=0.975 nearest_d=0.878 path_obje=0.958 |
| ZS3B_full_hf | 1328 | 0.6920 | 0.0 | counting=0.434 direction=0.806 nearest_c=0.856 nearest_d=0.528 path_obje=0.887 |

## contrasts (21 clusters, B=20000, seed 20260809)

| contrast | arms | family | Delta | 95% CI | sig |
|---|---|---|---|---|---|
| Qwen3 family interface contrast, 4B | Q3TXT4B_D0 vs Q3VL4B | all | +0.0595 | [+0.0167, +0.0918] | * |
| Qwen3 family interface contrast, 8B | Q3TXT8B_D0 vs Q3VL8B | all | +0.0233 | [-0.0246, +0.0553] |  |
| ZS low (HF bf16) vs ZS full (ollama Q4) -- resolution AND runtime/quant differ; deconfounding fullres-HF run queued | ZS3B_low vs PIXEL_3b | all | -0.0136 | [-0.0318, +0.0030] |  |
| fine-tuning effect at matched resolution | FT3B_low vs ZS3B_low | all | +0.1664 | [+0.1346, +0.1990] | * |
| FT vs original full-res ZS (system change) | FT3B_low vs PIXEL_3b | all | +0.1529 | [+0.1278, +0.1782] | * |
| M1 headline: D0_3b vs fine-tuned pixel | D0_3b vs FT3B_low | all | -0.0768 | [-0.1216, -0.0433] | * |
| D0_7b vs fine-tuned 3B pixel | D0_7b vs FT3B_low | all | -0.0550 | [-0.1053, -0.0199] | * |
| reference zero-shot Delta, 3B | D0_3b vs PIXEL_3b | all | +0.0761 | [+0.0404, +0.0997] | * |
| reference zero-shot Delta, 7B | D0_7b vs PIXEL_7b | all | +0.0429 | [+0.0071, +0.0694] | * |
| FT-7B vs ZS-3B low (descriptive) | FT7B_low vs ZS3B_low | all | +0.1800 | [+0.1568, +0.2058] | * |
| M1 at 7B: D0_7b vs fine-tuned 7B pixel | D0_7b vs FT7B_low | all | -0.0685 | [-0.1178, -0.0357] | * |
| FT scale step 7B vs 3B | FT7B_low vs FT3B_low | all | +0.0136 | [-0.0046, +0.0338] |  |
| clean resolution effect (same HF bf16 runtime) | ZS3B_low vs ZS3B_full_hf | all | -0.0143 | [-0.0327, -0.0017] | * |
| runtime/quant effect (same full resolution) | ZS3B_full_hf vs PIXEL_3b | all | +0.0008 | [-0.0128, +0.0189] |  |

## deviations in force

- PXDEV_t1024: qwen3-vl:2b thinking budget 1024 vs 8 tokens everywhere else; favorable asymmetry; descriptive only.
- Qwen3 arms: HF chat template instead of ollama's; Qwen3-8B run in official non-thinking mode.
- FT arm + ZS-low control: max_pixels=401408 (512*28*28) for training AND inference; grid reduced to r=16, lr in {1e-4, 5e-5}; winner ep2 kept (val .8841/.8817 -> lr1e-4; ep2 .9016).
- FT hyperparameters for 7B transferred from the 3B selection, not re-selected.
- CONFOUND NOTE: ZS3B_low is transformers bf16 while the legacy full-res ZS arm (PIXEL_3b) is ollama Q4_K_M; their difference mixes resolution with runtime/quantization. A transformers full-res ZS run is queued to deconfound. FT-vs-ZS_low is unaffected (same runtime, same resolution).

## step-5 artefact index

- exp3_runs/writing_exports/table2_per_family.md
- exp3_runs/writing_exports/blind_audit.md (cf blind gap CLOSED by BLIND_3b/7b above)
- exp3_runs/writing_exports/qualitative/{win_scoped,fail_nearest_class}/
- exp3_runs/writing_exports/arms_master_table.md
- 7B QLoRA smoke: PASSED (100 steps, 34.6 min, loss .145); full 7B included above.
