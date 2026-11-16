# exp_rev1: material added for the resubmission (IEEE Access-2026-44226)

Every experiment that the revised manuscript adds, under the release policy of this
repository: the evaluation is public (question banks, per-question predictions,
perceived states, measurements, analysis scripts), and since 2026-11-15 the source of
the serializer is public too (folder `serializer/` of the repository); the perception
stack, the question generators, detector weights, and the images of CODa and nuScenes
are not redistributed. Section and table numbers refer to the revised
manuscript, *Semantic Serialization as a Perception Interface for Small Language
Models in Closed-Set, Task-Aware Embodied Question Answering*. "Supplement" is
`SUPPLEMENT.pdf` in the repository root.

| folder | what | manuscript |
|---|---|---|
| `B123_PREREG.md` | arms and analysis of the VLM with added inputs, written down before the runs | Sections VI and VII-B |
| `b123_vlm_aids/` | VLM given both stereo images, the answer vocabulary in its prompt, or the serialized text with the image; VLM control runs; `INCIDENTS.md` = serving faults and how they were handled | Section VII-B, Table 5 |
| `ctrl_text/` | the two primary text arms run again on the reinstalled serving software (controls) | Section VI; Tables 5, 6, 10 |
| `b4_scenegraph/` | the perceived objects as relation triples and as a JSON scene graph (object list only) | Section VII-C, Table 6 |
| `b4c_scenegraph_convention/` | the object-list scene graphs run again with the sign convention of the bearing and the rule for left, center, and right stated in the prompt (control added after an internal review; not planned in advance) | Section VII-C; Supplement Section S17 |
| `b4b_scenegraph_aligned/` | relation triples and JSON with the content of the serialized text (counts, selections, band and sector of the nearest object of each class) | Section VII-C, Table 6 |
| `b6_rfdetr/` | RF-DETR-Medium in place of the YOLO11 pair: training curves, mAP on training and held-out recordings, perceived states, predictions | Section VII-H, Table 10; Supplement Table S6 |
| `b5_light/` | lighter perception stacks: perceived states, predictions, time per frame (`timing/timing_summary.json`) | Section VII-H, Table 10 |
| `a9_detmap/` | accuracy of every fold's YOLO11 detectors on their training recordings and on held-out recordings | Section VII-H; Supplement Table S6 |
| `b7_bandwidth/` | size of the serialized text and of the camera frame, visual tokens | Section VII-I; Supplement Table S7 |
| `b8_memory/` | GPU memory of each reader and VLM (peak minus idle) | Table 11 |
| `b10_boards/opi3b/`, `b10_boards/hps_agilex5/` | reader alone on two boards without a GPU | Section VII-I; Supplement Table S8d |
| `b10_boards/orin_nano_e2e/` | Jetson Orin Nano, one session: one-pass detector pair on the board, serializer, reader on the board's own states, VLMs, one question per frame and five questions per frame, board power | Table 12 (five questions per frame, moondream); Supplement Section S8 |
| `b10_boards/orin_nano_e2e_lowres/` | Jetson Orin Nano, second session: Qwen2.5-VL 3B on the timing set with the image reduced to 672 x 560, and once more at the full resolution | Section VII-I, Table 12 (five questions per frame); Supplement Section S8 |
| `b10_boards/orin_nano_fullbank/` | Jetson Orin Nano, third session (`amendments/A7_onboard.md`): the whole confirmatory bank on the board. One-pass detector pair on all 1328 frames, serializer, readers of 1.5B, 3B, and 7B; Qwen2.5-VL 3B at the reduced and at the full resolution; the VLM with image and serialized text on the timing set; and, added during the session (`amendments/A7_addendum1.md`, exploratory), the VLM with the reduced image and the serialized text on the whole bank (`full-hyb-qwen2.5vl-3b-lr`). In the full-image run of the VLM (`full-qwen2.5vl-3b`) the last 338 outputs are the string `????????`: one question (`coda_3_12072_counting`) puts the server into a failed state that lasts until it is started again (`log_diag_fault.txt`; `amendments/A7_addendum2.md` and `A7_addendum3.md`). A first repeat run without a rule for this failed in the same way and was stopped (`log_full-qwen2.5vl-3b-rerun_stopped.txt`). `full-qwen2.5vl-3b-guard` holds the run of these 338 questions, and of the 100 questions before them, with the reload rule (`b10_board_bench_guard.py`: restart after a degenerate output, ask once more) | Section VII-I, Table 12 (accuracy, time, and energy per question); Supplement Section S8 |
| `b10_boards/orin_nano_e2e_mintok/` | Jetson Orin Nano, timing run added on 15 November 2026: Qwen2.5-VL 3B on the timing set with the image reduced to 980 x 840 (1050 image tokens, the smallest size of this aspect ratio above the 1024 that the server names as the minimum); time and energy only | Section VII-I; Supplement Section S8 |
| `b10_boards/orin_nano_fullbank/full-qwen2.5vl-3b-mr/`, `.../diag_encoder/`, `.../rule_on_board_states.json` | additions of 16 November 2026, after an internal review of the finished manuscript. (1) Qwen2.5-VL 3B on the whole bank with the image reduced to 980 x 840, with the reload rule in force from the first question (`amendments/A7_addendum4.md`; `swap_full-qwen2.5vl-3b-mr.txt` holds the swap counters of the board during the run). (2) A diagnostic of where the vision encoder runs: server logs with the encoder on the GPU and on the processor, three questions at each of three image sizes (not scored). (3) The fixed rule of `analysis/exp2_option_baselines.py`, applied offline by `scripts/b10_rule_on_board_states.py` to the states that the board produced (`states_confirm_light1_orin.json`) | Section VII-I, Table 12; Supplement Sections S4 and S8 |
| `b10_boards/orin_nano_fullbank_first_start/` | logs of the first start of the third session (20:04), which was stopped because the camera calibration of only one recording was on the board: 87 frames perceived, 55 reader answers, never scored | Supplement Section S8 |
| `b10_boards/orin_nano/` | earlier Orin session (reader and VLMs only, desktop stopped); superseded by `orin_nano_e2e/`, kept for the record | not used |
| `c1_nusc/` | first check on nuScenes v1.0-mini (ten scenes): question bank `qa_nusc.jsonl` (derived from nuScenes annotations, CC BY-NC-SA 4.0), predictions, surface-cue audit, `INCIDENTS.md`; `fix_*` = the serialized arms run again with the image width of the nuScenes camera (`amendments/A6_addendum1.md`); `states/` = perceived and annotated states (`_u1224` = image column rescaled for the serializer) | Supplement Section S9 |
| `c2_nusc/` | second nuScenes bank (v1.0-trainval, 829 scenes; derived from nuScenes annotations, CC BY-NC-SA 4.0): `qa_nusc2.jsonl`, `audit_nusc2.txt`, `bank_report.txt`, `scene_meta_nusc2.json`, `states/`; predictions: `s_*` serialized system, `sraw_*` the same with the CODa image width, `gt_*` annotated objects, `blind_*` reader without a scene, `hf_pixel_*` VLM (Transformers), `pixel_ollama_7b` VLM (Ollama), `d1_*` ranges in meters without band words and `sg_triples_*` object-list scene graph (amendment A8, `a8.log`), `hf_hybrid_*` VLM with image and serialized text, `readerR_*` and `hf_reason_*` protocol R; `cf_hf_pixel_*` = the VLM with Transformers on the confirmatory bank | Section VII-J, Table 13; Supplement Sections S13 and S14 |
| `key_audit/` | audit of the answer key of the nearest-distance family: for every nearest-distance question of the confirmatory bank and of the second nuScenes bank, the distance to the center of the box (the key) and to the nearest point of its footprint | Sections IV-A and VII-J; Supplement Section S16 |
| `c3_reason/` | protocol R ("reason, then answer") on the confirmatory bank: VLM and reader at 3B and 7B, with the full output text | Section VII-B; Supplement Section S13 |
| `scripts/` | measurement and evaluation harnesses (board benchmarks and builds, memory, size of the text, detector evaluation, runner for the VLM with added inputs) | |
| `analysis/` | the statistics of the revised manuscript (see the next section) | |

## Reproducing the numbers of the revised manuscript

From `exp_rev1/analysis/` (Python 3 with numpy and pandas):

    python rev2_analysis.py     # every accuracy and contrast of Section VII, the answer-prior
                                # analysis, the checks of Table 9, nuScenes -> rev2_results.json
    python b10_e2e_numbers.py   # Table 12, Supplement Section S8          -> b10_e2e_numbers.json
    python build_supplement.py  # the Supplement (Sections S1 to S18)      -> ../supplement.tex

All three read only files of this repository. `rev2_results.json` and `b10_e2e_numbers.json`
are the files from which the tables of the manuscript and of the Supplement were filled.
`rev2_analysis.py` uses the paired bootstrap over recordings of `robustness_cf.py`
(B = 20000, seed 20260809, each replicate divided by its own number of questions).

The two primary intervals quoted in the manuscript, [+0.0403, +0.0996] at 3B and
[+0.0073, +0.0690] at 7B, are those of `analysis/confirm_analysis.py` in the repository
root, which quotes the criterion (`analysis/stats_for_revision.txt`). The criterion itself is
in the header of `amendments/primary_criterion/go_confirm.bat`, the script that generated the
confirmatory bank and ran the arms; `amendments/A0_primary_criterion.md` gives its times. That
script and `rev2_analysis.py` implement the same resampling with different random-number
generators; for the primary contrasts `rev2_analysis.py` gives [+0.0393, +0.0995] and
[+0.0070, +0.0689]. The manuscript states this in Section II.

`b_arms_analysis.py`, `c1_analysis.py`, and `b10_numbers.py` belong to an earlier draft of
the revision. They are kept because their outputs were checked against the same logs; the
manuscript no longer quotes them. Where they differ from `rev2_results.json` in the third
or fourth decimal, the cause is the reference arm (archived run or control run) or the
order of the recordings in the bootstrap.

## Notes

- Answers that contain no readable option letter are counted as wrong everywhere.
  Supplement Table S1 gives the parse rate of every arm.
- `b8_memory`: a one-off scheduled task re-fired on 2026-10-14 and overwrote the first
  memory measurement; it was measured again on 2026-10-23 (`b8_memory/memory.json`).
- `b10_boards`: `peak_rss_mb` in the board summaries is MiB (kB/1024); the manuscript
  reports GB = 10^9 bytes. On the Orin, GPU buffers share system memory with the file
  cache, so no per-process peak is reported. Power is the mean of tegrastats VDD_IN while
  the model works. `probe50_index.jsonl` lists the 50 probe questions; the prompt texts can
  be written again with `serializer/`.
- `b10_boards/orin_nano_e2e`: the probe file on the board carried, as the laptop answers of
  Qwen2.5-VL 3B, those of the first run with the serving fault. `b10_e2e_numbers.py`
  recomputes the agreement against the guarded re-run (48 of 50), which is the 3B VLM arm of
  the manuscript. The `agree_laptop` field of that summary (47 of 50) is therefore not used.
- Runs set aside as invalid are kept under their own names with the reason in the name
  (`invalid_*`, `oom_*`).

## Licences

Data in this folder are derived from CODa and, in `c1_nusc/` and `c2_nusc/`, from nuScenes; both are
released under CC BY-NC-SA 4.0, and the derived data here are released under the same licence.
Scripts are released under the MIT licence.
