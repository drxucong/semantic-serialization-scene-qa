# Amendment A7, addendum 1 (written 2026-11-15, during the session on the board)

## One arm is added to the session: the VLM with the reduced image and the serialized text

Amendment A7 planned the VLM with image and serialized text on the 50 questions of the timing
set only, for time and energy. This addendum adds a run of that arm on all 1328 confirmatory
questions at the reduced resolution (672 x 560), on the board, with the serialized text of the
states that the board computed. It starts when the planned session has finished
(`exp_rev1/scripts/run_b10_orin_hybrid_lr.sh`, prompts by `b10_orin_hybrid_full.py`).

Reason: on the laptop the VLM that also reads the serialized text is the most accurate
configuration without task training. A reader who plans a deployment will ask what this
configuration reaches on the board at a resolution at which the VLM is fast. The arm at the
full resolution is not run on the whole bank; it needs about ten seconds per question.

## Known when this addendum was written

- The reader runs of the session had finished and had been read: on the board the serialized
  system answers 0.7425 (3B reader), 0.7395 (1.5B), and 0.7771 (7B) of the 1328 questions
  correctly.
- The VLM with the full image and the serialized text had answered the timing set: 10.18 s
  per question, 41 of 50 correct.
- No answer of the VLM on the whole bank had been read, at either resolution; those runs
  were still in progress or had not started.

## Status

This arm is exploratory. It has no criterion. The paper reports its accuracy, time, and
energy on the board whatever the outcome, together with its difference from the serialized
system with the 3B reader and from the VLM with the reduced image alone (paired bootstrap
over the 21 recordings, B = 20000, seed 20260809). The comparisons O1 and O2 of A7 are
unchanged.
