# Amendment A7, addendum 4 (written 2026-11-16, about 10:20 board time)

## A further VLM run on the board: the image at 980 x 840 pixels, all 1328 questions

### Why

The manuscript of 16 November (built at 05:13) was read by three internal reviewers. All three
noted the same gap. On the board the VLM has an accuracy at two image sizes only:

- the reduced image (672 x 560, 480 image tokens), which is below the 1024 image tokens that
  the server names as the minimum for this model family;
- the full image (1224 x 1024), the size of the run that failed in part and was answered
  again under addenda 2 and 3.

The size just above that minimum (980 x 840, 1050 image tokens) has a time on the 50 timing
questions (5.36 s per question, `orin_nano_e2e_mintok`) and no accuracy on the bank.

### Run (fixed here, before the run)

1. Board, power mode, model files, server binary and settings, and prompts are those of the
   full-image run. The camera frame is reduced to 980 x 840 pixels with bicubic resampling,
   the method of the 672 x 560 copies (`exp_rev1/scripts/run_b10_orin_mr_full.sh`).
2. All 1328 confirmatory questions are asked in bank order by
   `exp_rev1/scripts/b10_board_bench_guard.py`. The reload rule of addendum 3 is therefore in
   force from the first question: after a degenerate output the server is started again and
   the question is asked once more.
3. A question whose second output is degenerate again is recorded as failed and counts as
   wrong. The paper states how many such questions there are and names them in the
   Supplement.
4. The warm-up uses the reduced image of the first question (option `--warm-probe`, added to
   the script for this run; its default reproduces the earlier behavior).
5. The counters of swapped pages and the free swap space of the board are sampled every 10 s
   during the run, because the reviewers asked whether swap space was in use.

### Comparison O3 (exploratory, no criterion)

O3 is the accuracy of the serialized system with the 3B reader on the board (the answers of
session 3, unchanged) minus the accuracy of the VLM at 980 x 840. Interval, sign-flip test,
and leave-one-recording-out check are computed as for O1 and O2. If questions fail under
rule 3, O3 is also given without them and with all of them counted as correct answers of the
VLM.

### Wording, by outcome (fixed here)

- The interval lies above zero: "the serialized system is also more accurate than the VLM at
  this image size", with "firm" or "not firm" by the three conditions used for O1 and O2.
- The interval includes zero: "no difference in accuracy from the VLM at this image size is
  resolved". The sentences of the abstract, of Section VIII-A, and of Section IX that say
  "more accurate than the VLM at both resolutions" are then restricted to the sizes at which
  the difference is resolved, and they name this size as one at which it is not.
- The interval lies below zero: "the VLM at this image size is more accurate than the
  serialized system", and the same sentences are changed accordingly.

In every case the run receives a row in the table of the board and a point in its figure, and
its time and energy over the 1328 questions replace the values of the 50 timing questions in
the text. O1 and O2 and their wording stand as reported.

### Known when this addendum was written

- Every result of the manuscript of 05:13. On the board: serialized system with the 3B
  reader 0.7425; VLM 0.6664 with the reduced image and 0.6935 with the full image. On the
  laptop: the accuracies of the same model in Tables 3, 5, and S1.
- The 50 timing questions at 980 x 840: 5.36 s per question; 30 of 50 answers correct; 43 of
  50 equal to the answers of the laptop.
- A diagnostic run of the same morning (`exp_rev1/scripts/b10_diag_encoder.py`; three
  questions at each of the three image sizes; not scored, and not part of any comparison).
  With raised log verbosity the server prints `clip_ctx: CLIP using CUDA0 backend`, so the
  vision encoder runs on the GPU in the setting of all board runs. With the full image the
  encoding of the image takes about 8 s of the 10 s per question. The second half of the
  diagnostic, with the vision encoder on the CPU, was still running when this addendum was
  written.
- An offline computation of the same morning (no board, no language model;
  `exp_rev1/scripts/b10_rule_on_board_states.py`): the fixed rule of Supplement Table S4,
  applied without change to the states that the one-pass detector pair produced on the board,
  answers 1067 of the 1328 questions correctly (0.8035). The same code reproduces the 0.8027
  of Table S4 on the full-stack states.
