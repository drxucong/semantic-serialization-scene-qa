# Amendment A7, addendum 3 (written 2026-11-16, about 03:10 board time)

## The cause of the failure in the full-image run, and the rule that replaces addendum 2

### What the repeat run of addendum 2 showed

The repeat run of addendum 2 (a newly started server, questions 891 to 1328 of the bank in
order) answered its first 100 questions, the ones that precede the failure, with ordinary
option letters. From its 101st question on, which is question 991 of the bank
(`coda_3_12072_counting`), every output was again the string `????????`. The run was stopped
after 110 questions, about 20 minutes after its server had started. Its log is kept
(`log_full-qwen2.5vl-3b-rerun_stopped.txt`); it wrote no answer file.

The failure is therefore not an effect of the running time, as addendum 2 supposed. A
diagnostic run (`exp_rev1/scripts/b10_diag_fault.py`) showed:

- The server of the stopped run returned `????????` for every further request: for question
  990, which it had answered correctly before, for the last question of the bank, and for a
  request with text only.
- A newly started server answered a text-only request normally. Asked question 991 as its
  first image request, it returned `????????`, and after that it returned the same string for
  questions 992, 990, 991, 1328, and 1, and for a text-only request.

One question, with the camera frame at full resolution, puts this server into a state in
which every output is that string, until the server is started again. The 337 questions that
followed it in the first run failed for that reason and not for their own content. With the
image reduced to 672 x 560 the same question was answered in the session, and on the laptop
the same model answered it at full resolution. This is the kind of fault that the paper
reports for the same model on the laptop (Section VI), where it was handled by a rule that
reloads the model after a degenerate output.

### Rule (replaces rules 2 to 4 of addendum 2; fixed here, before the run)

1. The 990 answers of the first process stand (addendum 2, rule 1).
2. The 338 failed questions are answered again, in bank order, by
   `exp_rev1/scripts/b10_board_bench_guard.py`: same board, power mode, model files, server
   binary and settings, prompts, and images. An output is called degenerate if, stripped of
   blanks, it has at least four characters and at most two distinct ones (the test of the
   laptop runs). After a degenerate output the server is stopped and started again, and the
   question is asked once more.
3. A question whose second output is degenerate again is recorded as failed and counts as
   wrong; the server is started again before the next question. The paper states how many
   questions remain failed and names them in the Supplement.
4. The run also answers the 100 questions that precede the failure (addendum 2, rule 3). The
   paper reports how many of these answers equal those of the first process; the answers of
   the first process stay in the comparison.
5. O2 is computed on all 1328 questions: 990 answers of the first process and 338 answers of
   this run. The Supplement also gives O2 on the 990 questions of the first process alone
   (addendum 2, rule 5).
6. Time and energy per question of the full-image VLM are computed over the answers that
   enter the comparison. In the run with the rule, the power is averaged over the time
   windows of the recorded requests, so that the loading of the server does not enter it; the
   time of a restart is not part of the time per question, and the paper states the number of
   restarts.

### Known when this addendum was written

Everything listed in addendum 2, and the facts above. The 100 answers of the stopped repeat
run exist only as option letters in its log; they had not been compared with the answers of
the first process.

### Status

Unchanged: O2 was written down beforehand, without a criterion. The paper states that the
answers of 338 questions come from a second run, that its rule was fixed after the other 990
answers had been scored, and that the rule is the one the paper already uses for this model
on the laptop.

### Note added on 2026-11-16, after the run

The stopped repeat run had answered 120 questions when it was stopped, not 110: its log
(`log_full-qwen2.5vl-3b-rerun_stopped.txt`) has 120 result lines, 100 with an option letter and
20 with the string. The number 110 above was read from the log while the run was still going.
The rule is unchanged.
