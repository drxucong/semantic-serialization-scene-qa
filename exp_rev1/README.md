# exp_rev1: material for the resubmission (IEEE Access-2026-44226)

Every experiment added in the revised manuscript, under the release policy of this
repository: the evaluation is public (question banks, per-item logs, perceived states,
measurements, analysis scripts); the perception stack, the serializer, the question
generators, detector weights and CODa images are not redistributed. Section and table
numbers refer to the revised manuscript.

| folder | what | manuscript |
|---|---|---|
| `B123_PREREG.md` | arms, analysis and predictions written down before any run | Section VIII |
| `b123_vlm_aids/` | zero-shot VLM given both stereo images (B1), the decision vocabulary in its prompt (B2), the serialized state alongside the image (B3), and re-run pixel controls; per-item logs; `INCIDENTS.md` = serving faults and how they were handled | Section VIII-A, Table 13 |
| `b4_scenegraph/` | the same perceived state read as relation triples and as a JSON scene graph | Section VIII-B |
| `b6_rfdetr/` | RF-DETR-M detector swap: per-fold training curves (`metrics.csv`), train/held-out mAP (`eval/rf_*.json`), perceived states, per-item logs | Section VIII-C |
| `b5_light/` | lighter perception stacks: perceived states, per-item logs, end-to-end timing (`timing/timing_summary.json`) | Section VIII-D, Table 14 |
| `b10_boards/` | readers and VLMs on edge boards (Orange Pi 3B, Agilex 5 HPS, Jetson Orin Nano): per-question latency, answers, memory and, on the Orin, board power (`power.jsonl`); `probe50_index.jsonl` lists the 50 probe items (prompt texts withheld with the serializer) | Section VIII-E, Table 15 |
| `c1_nusc/` | external evaluation on nuScenes v1.0-mini front camera: question bank `qa_nusc.jsonl` (derived from nuScenes annotations, CC BY-NC-SA 4.0), per-item logs, option-bias audit, `INCIDENTS.md` | Section VIII-F, Table 16 |
| `a9_detmap/` | per-fold YOLO11 accuracy on its own training split and on held-out sequences (incl. the visible-scope label variants vis1/vis2) | Section VII-H, Table 9 |
| `b7_bandwidth/` | interface payload per item (bytes and tokens of each stream, keyframe sizes, visual tokens) | Section VII-J, Table 12 |
| `b8_memory/` | GPU memory of each reader and VLM (peak minus idle) | Section VII-I, Table 10 |
| `scripts/` | measurement and evaluation harnesses (board benchmark and builds, memory, payload, detector evaluation, VLM-aid runner) | |
| `analysis/` | the statistics behind Section VIII | |

## Reproducing the Section VIII statistics

From `exp_rev1/analysis/` (Python 3 with numpy and pandas):

    python b_arms_analysis.py            # Tables 13-14, Sections VIII-A..D -> b_arms_results.{md,json}
    python c1_analysis.py                # Table 16, Section VIII-F          -> c1_results.{md,json}
    python robustness_cf.py --csv ../../results/exp3_predictions/predictions3_cf_v2.csv
                                         # Table 8, Section VII-G           -> robustness_cf.json

All three read only files in this repository; their outputs are byte-for-byte the
numbers in the manuscript (paired cluster bootstrap, B = 20000, seed 20260809).

## Notes

- B8: a one-off scheduled task re-fired on 2026-10-14 and overwrote the first memory
  measurement; it was re-measured cleanly on 2026-10-23 (`b8_memory/memory.json`), and
  Table 10 reports peak minus idle GPU memory from that file.
- B10: `peak_rss_mb` in the board summaries is MiB (kB/1024); the manuscript reports
  GB = 10^9 bytes. On the Orin, GPU buffers share system memory with the file cache, so no
  per-process peak is reported; the manuscript gives the lowest free memory during each run
  (`mem_available_before_kb` minus `peak_sys_used_mb`). Power is the mean of tegrastats
  VDD_IN over the answering window (`t_measure_start`..`t_measure_end`; samples in
  `power.jsonl`). `analysis/b10_numbers.py` turns the summaries into the numbers of Table 15.
- Runs set aside as invalid are kept under their own names with the reason in the name:
  `invalid_cachehit_*` (Orange Pi: the warm-up shared a prompt with item 1),
  `oom_*` (Orange Pi: context or host prompt cache too large for the board),
  `invalid_chattemplate_moondream` and `invalid_marker_moondream` (Orin: moondream needs
  Ollama's prompt template, reproduced in the final run, which then matches the paper's
  answers on 50 of 50 items), `invalid_warmupcache_qwen2.5vl-3b` (Orin: the warm-up used
  item 1's image, so item 1 reused the encoded image).
