# Amendment A4 (frozen 2026-08-10, prior to any run it governs)

Purpose: to measure how the serialized interface and the pixel interface scale
with reader or decoder size, extending the 3B and 7B co-primary design
downward.

New text-reader arms: Qwen2.5-Instruct 0.5B and 1.5B, each evaluated on D0 at
the confirmatory bank, D0 and D1 at the N2 bank, and D0 over ground-truth
states at the confirmatory bank. Ground-truth-state arms at 3B and 7B are
re-run on this machine for curve completeness.

New pixel arms: moondream (1.8B) and LLaVA-Phi-3-mini (3.8B; retained as a
mid-curve point, not sub-2B), evaluated on the confirmatory bank and the N2
bank. Qwen3-VL 2B is included as a recorded-deviation arm evaluated on the
confirmatory bank only. Decoding deviation, stated in advance: Qwen3-VL 2B
is a thinking model whose answer channel is empty under the frozen 8-token
budget; it is run with a 256-token thinking budget versus 8 tokens for every
other arm, and only the non-thinking content channel is parsed. This
asymmetry favors the deviating arm; its results are reported descriptively,
in a separate row, and enter no paired contrast.

The frozen option-aware baselines are additionally evaluated as-is on the N1
and N2 banks; descriptive, no refitting.

Same decoding, parse, and pairing rules as Amendment A3 for every
non-deviating arm; same clustered bootstrap for within-family contrasts.

Pre-stated predictions.
(S1) Within the Qwen2.5 family, the D0-at-confirmatory advantage over the
pixel arm does not shrink as scale decreases from 7B to 3B to the nearest
comparable smaller pixel arm; the text arm's accuracy declines more slowly
with scale than the pixel arms' accuracy declines.
(S2) On N2, the D1 advantage decreases with reader scale and is absent or
negative at 1.5B and 0.5B.
(S3) The divergence between the D0-at-confirmatory curve and the D1-at-N2
curve identifies the alignment requirement of the interface; this is
exploratory.

Cross-family pixel comparisons are descriptive only and no preregistered
contrast is attached to them. All outcomes will be reported regardless of
direction. Nothing frozen under A3 is modified.
