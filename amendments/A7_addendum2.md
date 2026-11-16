# Amendment A7, addendum 2 (written 2026-11-16, about 01:50 board time)

## A failure in the full-image run of the VLM, and the rule for it

The run of the VLM with the full image on all 1328 confirmatory questions
(`out_e2e_full1328/full-qwen2.5vl-3b`, one server process, started 21:56 on 2026-11-15,
finished 01:41 on 2026-11-16) failed part of the way through.

- Questions 1 to 990 (in the order of the question file) have ordinary answers: one option
  letter, sometimes followed by a period.
- From question 991 to the end, all 338 answers are the same string of eight question marks
  (`????????`). The change falls at about 00:44, 2 h 47 min after the process had started.
- The server log contains no error or warning at that point. The time per question and the
  power draw do not change.
- The cause was not found. Kernel messages of the board need administrator rights, which the
  session does not have.

The 338 strings are not answers of the model. Comparison O2 of A7 cannot be computed from
this run alone. The failed questions are whole recordings (3 in part; 4, 5, 6, 7, 8, 9 in
full), so the 990 answered questions are not a random part of the bank.

## Rule (fixed here, before the repeat run starts)

1. The 990 answers of the first process stand.
2. The 338 failed questions are answered again by a newly started server process: same
   board, same power mode, same model files, same server binary and settings, same prompts and
   images (`exp_rev1/scripts/run_b10_orin_vlfull_rerun.sh`). The repeat run starts when the
   runs that are already queued on the board have finished.
3. The repeat run also answers the 100 questions that precede the failure (questions 891 to
   990), chosen by position. They show whether a new process gives the same answers as the
   first one. The paper reports how many of the 100 answers are the same. For these 100
   questions the answers of the first process stay in the comparison, whatever the count.
4. If an answer of the repeat run is again the string of question marks, that question is
   answered once more by another new process. A question that still fails then counts as
   wrong, and the paper says how many there are.
5. O2 is computed on all 1328 questions: 990 answers of the first process and 338 answers of
   the repeat run. The wording follows A7 unchanged. The Supplement also gives O2 on the 990
   questions of the first process alone.
6. Time and energy per question of the full-image VLM are computed over the answers that
   enter the comparison (990 + 338).
7. Every other run of the session is checked for the same string. A run that contains it is
   treated by the same rule.

## Known when this addendum was written

- All other runs of the session had been scored (A7, addendum 1), except the run of the VLM
  with the reduced image and the serialized text, which was in progress.
- The 990 ordinary answers of the failed run had been scored: the full-image VLM answers
  0.6949 of them correctly, the serialized system with the 3B reader 0.7424, the VLM with
  the reduced image 0.6747. On the 338 failed questions the serialized system with the 3B
  reader answers 0.7426 correctly and the VLM with the reduced image 0.6420.
- With the 338 failed answers counted as wrong, the analysis script printed an accuracy of
  0.5181 for the full-image VLM. That number is not used.
- No other run of the session contains the string: every answer of the three readers and of
  the VLM with the reduced image is an option letter or an ordinary unparsed text.

## Status

O2 keeps its status from A7: a comparison that was written down beforehand, without a
criterion. Because 990 of its 1328 answer pairs were known when this rule was fixed, the paper
states that the repeat run and its rule were added after a failure and after those answers
had been scored.
