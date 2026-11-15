# Amendment A6 (written 2026-11-15, before the runs that it governs)

Three additions for the second revision of the manuscript (IEEE Access-2026-44226). Parts 1
and 2 are new runs; their arms, settings, analysis, and the way the result will be worded are
fixed here before any of these runs has been made on the confirmatory bank or on the new
nuScenes bank. Part 3 is an analysis of predictions that already exist and is post hoc.
Nothing fixed under the primary criterion or under A3, A4, A5 is changed.

Terms: "Scoped" is the serializer of the manuscript (v15 in the scripts); "reader" is the
text-only Qwen2.5 model that reads the serialized text; "VLM" is Qwen2.5-VL on the image;
"confirmatory bank" is `banks/qa_confirm.jsonl` (1328 questions, 21 recordings).

## What was known when this was written

- All results of the manuscript as of commit 9b30e4c.
- A preview of Part 3 (see Part 3).
- For Part 1: the outputs of protocol R on the first 40 questions of the *development* bank
  (25 questions for the 7B models), which were used to fix the wording of the prompt and the
  rule that reads the answer (the rule for an answer given as option text and the rule for
  server errors were added after the first of these tests). They are in `amendments/A6_files/`.
  No model has been run under
  protocol R on the confirmatory bank.
- For Part 2: the first nuScenes check on the ten scenes of v1.0-mini (`exp_rev1/c1_nusc/`),
  and a test on 16 questions of that mini bank on 2026-11-15, in which Qwen2.5-VL 3B served by
  Ollama 0.40.16 again returned a degenerate output ("88888888") for 14 of 16 questions. The
  new bank was written from the annotation tables alone. No image of the new scenes has been
  opened and no model has been run on them.

## Part 1. Protocol R ("reason, then answer") on the confirmatory bank

Reason. All arms of the manuscript ask for the option letter only and allow 8 output tokens.
A reviewer can ask whether the VLM would do better if it could reason first.

Protocol R is the same for the two routes: the last sentence of the system prompt of the
shipped arm ("Reply with ONLY the option letter.") is replaced by "First reason step by step
in a few sentences. Then give the final answer on a new last line in the form 'Answer: X',
where X is the option letter."; the last line of the user prompt ("Answer with ONLY the
option letter.") is replaced by "Reason step by step, then end with a line of the form
'Answer: X'."; temperature 0; at most 512 output tokens. The answer is the letter of the last
"Answer: X" of the output; if the text after the last "Answer:" is not a letter but is exactly
the text of one option, that option; if there is no "Answer:" and the last non-empty line has
at most 20 characters, the letter found in that line; otherwise the output is unparsed and
counts as wrong. A server error without text is not scored: the model is unloaded and the
question is asked again, at most three times. The reload rule of the shipped VLM arm also
applies. The script is `amendments/A6_files/c3_reason_answer.py`
(SHA-256 9786a709380157059b34ebcba2502e329ea19f7ee4385b6ce12a136f76a76802).

Arms, all on the 1328 questions of the confirmatory bank, served by Ollama as in the
manuscript: VLM-R at 3B and 7B (Qwen2.5-VL, image and question); Reader-R at 3B and 7B
(Qwen2.5, Scoped text of the shipped perception and question).

Analysis (paired bootstrap over the 21 recordings, B = 20000, as in `rev2_analysis.py`), at
each size: (a) Reader-R minus VLM-R; (b) Scoped (shipped, letter only) minus VLM-R;
(c) VLM-R minus VLM (shipped); (d) Reader-R minus Scoped (shipped). Accuracy, the share of
parsed outputs, and the share of outputs cut at 512 tokens are reported for every arm.

Status and wording. This is a sensitivity check; the primary criterion and its result are not
changed by it. All four arms are reported whatever the outcome. If at 3B the interval of
contrast (b) includes zero or lies below zero, the manuscript will no longer state that the 3B
result holds under every sensitivity check, and the abstract will say so.

## Part 2. A second external bank on nuScenes v1.0-trainval

Reason. The first external check used ten scenes, could report only the 7B models, and its
bank failed the surface-cue audit in the class families.

Bank (frozen). `exp_rev1/c2_nusc/qa_nusc2.jsonl`,
SHA-256 f649a9bbf996b8d4cf0c14ad9eeee497b9007f8c33cfb63364ad7089c3fb9833: 2718 questions on
2718 front-camera keyframes of 829 scenes. Scenes: all 840 scenes of v1.0-trainval that are
not among the ten scenes of v1.0-mini (11 scenes contribute no question). The question
templates, the visible scope, the margins, and the option format are those of the first bank.
What differs is the selection: every keyframe and every family is a candidate; within a
family the gold answer is drawn uniformly over the answer values as far as candidates exist;
at most one question per frame and four per scene, on frames at least 2 s apart; class
distractors are chosen so that the gold is the shortest, the middle, or the longest name
about equally often. Shortfalls (`bank_report.txt`): count 6 has 53 of 100 questions; the
band "under 5 meters away" has 24 (it is almost absent from a driving camera, so the band
family is balanced over the other two bands, 275 each); path-object has 62 Bus, 27
Motorcycle, and 15 Bicycle questions of 100 each. The surface-cue gate passes
(`audit_nusc2.txt`); the script would have written no bank otherwise. Generator:
`c2_make_nusc_qa.py`, SHA-256 4b2f8ec54546ef72be41aef854038c2cfb32724c910d6033a4f81042ee784735,
seed 20261115.

Systems. Nothing is trained or tuned on the new scenes.
- Serialized route: the zero-shot perception of the first nuScenes check, unchanged
  (RF-DETR-Medium with COCO weights, acceptance at confidence 0.50, range = median of the
  ground-plane cue, the class-height cue, and UniDepthV2; no stereo), then Scoped, then the
  reader (Qwen2.5 3B and 7B, Ollama, letter only, 8 tokens), as shipped.
- VLM route: Qwen2.5-VL 3B and 7B with the shipped system and user prompts, letter only,
  8 tokens, greedy. Because of the serving fault above, both sizes are run with the
  Transformers library (weights of the model authors in bfloat16, image at its native
  1600 x 900 resolution). The 7B VLM is also run through Ollama as a check of the back end.
- Further arms: reader on the Scoped text of the annotated objects (3B, 7B); reader with
  the question and options only (3B, 7B; its share of parsed outputs is reported); VLM with
  the image and the Scoped text of the perceived objects (3B, 7B).
- Back-end check on the confirmatory bank: the 3B and 7B VLM run with Transformers
  (bfloat16, native resolution, letter only), compared with the shipped Ollama arms.
- Protocol R on this bank (VLM and reader, both sizes) is run only if, in Part 1, protocol R
  changes the accuracy of the VLM by 0.02 or more at either size.

Criterion. E1: Scoped minus VLM at 3B, paired bootstrap over scenes (B = 20000), interval
above zero. E2: the same at 7B. A result is called firm if, in addition, a sign-flip test
over scenes (20000 random sign assignments) gives p < 0.05 and the interval stays above zero
when each of the four recording locations is left out in turn.

Wording. If E1 and E2 hold, the manuscript says that the result carries over to a second
dataset with perception that was not trained on it. If one holds, it says which. If neither
holds, the abstract and the limitations say that the result did not carry over. Accuracy per
family, the answer-prior rule (answer frequencies taken from the mini bank), and the scenes
whose description contains "night" or "rain" are reported descriptively. The first check on
v1.0-mini stays in the Supplement.

## Part 3. Accuracy balanced over gold answers (post hoc)

Reason. On the confirmatory bank a rule that never looks at the scene scores 0.652, and the
difference between the routes is unresolved on the questions that this rule answers wrongly.

Definition. Within a family, the accuracy is computed separately for each gold answer (for
example each count, each band) that has at least five questions, and these are averaged; the
balanced accuracy is the mean of the five family values. A rule that always gives the most
frequent answer of a family scores 1/K in that family. Contrasts: the pairs of Table 9 of the
manuscript, paired bootstrap over the 21 recordings, B = 20000. Sensitivity: a minimum of one
and of ten questions per gold answer in place of five.

Status. Post hoc and exploratory. A preview with B = 5000 and the minimum of five was computed
on 2026-11-14 before this text was written (3B: +0.087, interval above zero; 7B: +0.005,
unresolved; fine-tuned reader minus fine-tuned VLM: +0.023, unresolved). The manuscript will
say that the analysis is post hoc.
