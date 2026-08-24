# Amendment A5, second addendum (frozen 2026-08-12, prior to any run it governs)

Three additional arms, requested after SUMMARY3_full:

1. FT-TEXT: LoRA Qwen2.5-3B-Instruct (text) reading D0 serializations.
   Training items are IDENTICAL, question by question, to the FT-VLM
   per-fold sets (exp3_runs/sft/sft_fold{0..3}.jsonl; fold-0 excludes the
   validation sequence exactly as the VLM did). Hyperparameters are carried
   over from the FT-VLM winner (r=16, lr=1e-4, epochs=2) with no new grid.
   Because the deployed text interface reads PERCEIVED states, the training
   frames (5,598; never perceived before) are perceived once, out-of-fold
   (each frame by the detectors of the fold that holds its sequence out --
   the same construction as states_kf_v9), and D0 is rendered from those
   states by the frozen serializer path. Out-of-fold inference on the
   confirmatory bank, same items, same parse.
2. FT3B_low evaluated on the frozen N1 bank (inference only, existing
   adapters, fold routing by sequence).
3. FT3B_low evaluated on the frozen N2 bank (same).

Pre-stated: all outcomes reported regardless of direction; FT-TEXT vs
FT-VLM is the supervision-matched primary contrast of this addendum.
Nothing frozen under A3/A4/A5 is modified.
