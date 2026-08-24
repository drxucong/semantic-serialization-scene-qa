# Amendment A3 (frozen 2026-08-09, prior to any run it governs)

## Purpose
To test whether the confirmed SCOPED advantage over PIXEL depends on lexical and boundary
identity between the serializer's band vocabulary and the generator's option vocabulary.

## New serializer arms (confirmatory bank, PIXEL arm unchanged)
- **D1 (NUMERIC):** distance fields replaced by continuous values rounded to one decimal
  ("nearest pedestrian: 4.7 m"). All selections and runner-ups retained. No band strings,
  no epsilon borderline flags (the numeric value carries boundary proximity).
- **D2 (NUMERIC+ALT):** as D1, plus a coarse qualitative tag with vocabulary and boundaries
  disjoint from the option set: "close range" (r < 4 m), "mid range" (4 <= r <= 12 m),
  "far range" (r > 12 m).
- **D3 (ALT-ONLY, negative control):** the alternative tags of D2 without the numeric value.

Side words for bearing (left / center / right) are unchanged in all arms; this amendment
scopes to distance vocabulary only, and the direction family is analyzed separately.

## New question sets (generated and frozen before any arm is run on them)
- **N1 (paraphrase set):** every confirmatory-bank question is transformed by a frozen
  deterministic paraphrase table (stems and option strings reworded; boundaries, gold
  answers, and judgment logic unchanged). Assignment of stem variants is by question-id
  hash. The table and generated set are hashed and committed before any run.
- **N2 (novel-judgment set):** at least 300 questions with judgment logic and boundaries
  absent from every serializer vocabulary: novel three-way distance bands at 7 m and 22 m,
  ordinal cross-class comparisons, and count-within-radius (10 m and 12 m) items. Gold
  answers computed from ground truth by generator logic that shares no band map with any
  serializer. Both SCOPED and D1 are evaluated on N1 and N2.

## Evaluation
Same paired sequence-clustered bootstrap as the frozen primary criterion
(21 clusters, B = 20000, fixed seed, percentile CI), applied per contrast.

## Pre-stated predictions
If the mechanism is decision-aligned computation:
- **P1:** the D1 vs PIXEL 95% CI lower bound remains above zero on counting, and remains
  above zero or attenuates without sign reversal on nearest-distance;
- **P2:** the SCOPED vs PIXEL contrast on N1 attenuates by less than half of its
  confirmatory-bank value;
- **P3:** on N2, D1 exceeds PIXEL (95% CI lower bound above zero on the pooled N2 set).

If the mechanism is answer-string leakage: the N1 contrast collapses toward zero and D1
loses its nearest-distance advantage.

All outcomes will be reported regardless of direction. No serializer, prompt, threshold,
or question set will be modified after this amendment is frozen.

## Freeze procedure
1. Commit this file, the paraphrase table, both generator scripts, and the generated N1/N2
   banks to the repository.
2. Record SHA-256 hashes of all five artifacts in the commit message.
3. Only then run any arm listed above.
