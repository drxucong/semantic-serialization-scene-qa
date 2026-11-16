# Amendment A7: the confirmatory bank on the embedded board (written 2026-11-15)

## Status of this note

This note was written after the session on the board had been started and after its first
stage (perception of the 1328 frames) had finished, and before any answer of a language model
from this session had been read by the authors. It is a commit in the authors' repository with
the time of the authors' machine. It was not registered with a third party.

Known when this note was written:

- the accuracies on the laptop (one-pass detector pair with the 3B reader 0.7455, with the 7B
  reader 0.7794; Qwen2.5-VL 3B 0.6913, control run 0.6995);
- the session of 50 questions on the board (`exp_rev1/b10_boards/orin_nano_e2e/`): time and
  energy of every arm, and no accuracy;
- a second session of 50 questions (`exp_rev1/b10_boards/orin_nano_e2e_lowres/`): Qwen2.5-VL 3B
  answers 34 of 50 correctly at the full resolution (1224 x 1024, 9.97 s per question) and 30
  of 50 with the image reduced to 672 x 560 (2.06 s per question).

## Why this session

The first session on the board measured time and energy on 50 questions and took the accuracy
from the laptop. It ran the VLM only at the full resolution of the camera. An internal review
noted that this comparison is not like for like: a VLM can be made faster by reducing the
image, and the accuracy of the serialized system on the board was not measured. This session
measures both.

## The session

Board, condition, and software as in the first session (Jetson Orin Nano 8 GB, 25 W mode,
desktop running, llama.cpp 11fe021, all layers on the GPU, 4-bit weights). Script:
`exp_rev1/scripts/run_b10_orin_fullbank.sh`, driver `b10_orin_fullbank.py`.

1. Perception on the board: the one-pass detector pair (two fine-tuned YOLO11 detectors, one
   pass each over the full frame, ground-plane and class-height ranging, one camera) on all
   1328 confirmatory frames, each frame with the detectors of the fold that never saw its
   recording.
2. The shipped serializer on the states that the board computed.
3. Readers on the board: Qwen2.5 3B, 1.5B, 7B, all 1328 questions.
4. Qwen2.5-VL 3B with the image and the serialized text, 50 questions, at both resolutions
   (time and energy only).
5. Qwen2.5-VL 3B on all 1328 questions with the image reduced to 672 x 560 (bicubic).
6. Qwen2.5-VL 3B on all 1328 questions at the full resolution.

The reduced resolution was chosen before the 50-question session as the resolution at which
the image has about one quarter of the pixels; no other reduced resolution was run.

## Comparisons fixed here

Paired cluster bootstrap over the 21 recordings, B = 20000, seed 20260809, percentile
interval, as everywhere in the paper. "Firm" has the meaning of the paper: the interval
excludes zero, the exact sign-flip test over the recordings gives p < 0.05, and the interval
excludes zero with each recording left out in turn.

- O1: serialized system on the board (3B reader) minus the VLM on the board at the reduced
  resolution.
- O2: serialized system on the board (3B reader) minus the VLM on the board at the full
  resolution.

Reported without a criterion: the same two differences for the 1.5B and the 7B reader; the
VLM at the reduced resolution minus the VLM at the full resolution; for every arm the number
of answers that agree with the same arm on the laptop; time, power, and energy per question
of every arm.

## Wording that follows from each outcome

For O1 and for O2 separately:

- interval above zero: "on the board the serialized system is more accurate than the VLM at
  this resolution", with "firm" only if the three conditions hold;
- interval includes zero: "on the board no difference in accuracy is resolved at this
  resolution"; the paper then states the difference in time and energy only;
- interval below zero: "on the board the VLM at this resolution is more accurate than the
  serialized system"; the paper then states that the serialized system is faster and less
  accurate.

Whatever the outcome, the table of the board reports accuracy, time, and energy of every arm
of this session, and the abstract states the time of the VLM at both resolutions. If a stage
fails or the session is interrupted, the paper reports the stages that finished and says
which did not.

The results of the laptop remain the primary results of the paper. This session does not
change the criterion of the confirmatory bank.
