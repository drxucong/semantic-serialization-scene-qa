# Amendment A8 (written 2026-11-16, before the runs that it governs)

## Two less answer-aligned texts on the second nuScenes bank

Reason. Reviewer 1 asked for an external evaluation, "preferably with fewer answer-aligned or
more open-ended questions". The second nuScenes bank (A6, Part 2) is external, but it uses the
templates and the answer vocabulary of CODa, and the serialized text again states candidate
answers in the wording of the options. The arms that reduce this alignment (ranges in meters;
object-list scene graphs) were run on CODa only. This amendment runs two of them on the second
nuScenes bank. Nothing fixed under A6 is changed, and the two comparisons E1 and E2 of A6 keep
their status.

## What was known when this was written

- All results of A6 on this bank (the serialized system, the VLM, the VLM with image and text,
  annotated objects, the reader without a scene, the run with the CODa image width).
- All results on CODa, among them: with ranges in meters (D1) the serialized system has no
  resolved advantage over the VLM at either size; the object-list scene graphs score 0.12 to
  0.18 below the VLM control run.
- No run of D1 or of a scene graph exists on any nuScenes data (`exp_rev1/c1_nusc/`,
  `exp_rev1/c2_nusc/`).

## Arms

Bank: `outputs/nusc_ext2/qa_nusc2.jsonl` (2718 questions, 829 scenes). Perceived states: those
of the serialized system of A6 (`outputs/nusc_ext2/states_nusc2_rfdetr_u1224.json`), unchanged.
Readers: Qwen2.5 3B and 7B, served by Ollama, with the prompts, decoding, and parser of the
arm `s` of A6. Only the text that describes the scene changes.

1. D1, ranges in meters (`scripts/paper/run_serializer_dladder.py --mode d1`): the lines of
   the shipped text, with every range written in meters to one decimal and no band words. The
   words left, center, and right are unchanged. Output: `exp_rev1/c2_nusc/d1_3b`, `d1_7b`.
2. SG, object-list scene graph as relation triples (`scripts/rev1/b4_scenegraph.py --mode
   sg_triples`): for each object its class, its range in meters, its bearing in degrees, and
   its confidence; no band, no side word, and none of the lines that the serializer computes.
   Output: `exp_rev1/c2_nusc/sg_triples_3b`, `sg_triples_7b`. The JSON notation is not run; on
   CODa the two notations gave similar results.

## Comparisons and analysis

For each arm and size: the arm minus the VLM (`hf_pixel`), and the arm minus the shipped
serialized system (`s`). Paired bootstrap over the 829 scenes, B = 20000, seed 20260809, as in
A6; the same differences within each question family. Eight comparisons in all. They are
exploratory and have no criterion, and no correction for their number is applied.

Expectation from CODa, recorded here and not a criterion: D1 below the shipped system, mainly
in the nearest-distance family; the scene graph below the VLM. We make no prediction on
whether D1 stays above the VLM on this dataset.

## Wording, fixed in advance

For an arm minus the VLM, at each size:
- interval above zero: "with [this text] the serialized system keeps a resolved advantage
  over the VLM";
- interval includes zero: "with [this text] no difference from the VLM is resolved";
- interval below zero: "with [this text] the VLM is more accurate".

The paper reports all eight differences, whatever the outcome: the four differences from the
VLM in Section VII-J, and all eight with their family values in the Supplement (Section S14).
If the outcome differs from the CODa result, the paper says so and does not call either
result the general one.
