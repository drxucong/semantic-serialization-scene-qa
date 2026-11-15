# Record of the primary criterion (confirmatory bank)

This file was added on 2026-11-14, with the revised manuscript. It describes the record of
the primary criterion and what that record shows. Section VI of the revised manuscript
summarizes it.

## The record

`amendments/primary_criterion/go_confirm.bat` is the script that generated the confirmatory
bank and then ran the six arms on it. Its header contains the criterion.
`amendments/primary_criterion/confirm.log` is the log that this script wrote. Both files are verbatim copies from the authors' machine.

| item | time (local, UTC-4) | source |
|---|---|---|
| `go_confirm.bat` last saved | 2026-08-08 23:33:42 | file time |
| run started; bank generation started | 2026-08-08 23:33:49 | `confirm.log`, lines 1-2 |
| bank written (1328 questions); perception started | 2026-08-08 23:33:58 | `confirm.log`, lines 6-9; file time of the bank |
| first arm started (Scoped, 7B) | 2026-08-08 23:56:26 | `confirm.log` |
| last arm finished | 2026-08-09 01:25:20 | `confirm.log` |

SHA-256 of the two files:

    69b6d01cd082aa9e448b345938ffd18a84ca74655c8a7ff1551c8f1e0e0fb88d  go_confirm.bat
    1874da6477c7011c94170aea5634238e88c42253c353470ed488406366a45e1a  confirm.log

A second copy of `go_confirm.bat` with the same hash is in an archive of the working
session that was made on 2026-08-09 21:27; that archive holds unreleased source code and is
not part of this release.

## The criterion

From the header of `go_confirm.bat` (v15 is the serializer that the manuscript calls
Scoped, v9 the one that it calls Flat; the "floor" is the variation between repeated runs):

    CRITERIA, frozen 2026-08-08 23:0x, before the bank exists and before any
    arm runs. Scene-cluster paired bootstrap, B=20000, seed 0, clusters =
    recording sequences. Run-noise floor +-.006 (7B) / +-.008 (3B).

      A1  PRIMARY   v15 - pixel VLM at 7B: CI lower bound > 0 AND delta > +.006
      A2  PRIMARY   v15 - pixel VLM at 3B: CI lower bound > 0 AND delta > +.008
      A3  DECISION  v15 - v9 at both scales, floor applied. The paper leads
                    with v15 only if v15 is not WORSE than v9 above the floor
                    at either scale. If v15 loses above the floor at 7B or 3B,
                    the paper keeps v9 and v15 is reported as an ablation.

The header of `analysis/confirm_analysis.py` quotes the same three rules. The outcome is in
`analysis/confirm_table.txt` and `analysis/stats_for_revision.txt`: A1 and A2 pass, and A3
keeps v15.

## History

1. A first criterion was fixed for v9 on the 1366-question bank, which the manuscript now
   calls the development bank.
2. Seven serializer versions (v9 to v15) were then compared on that bank, and v15 was
   chosen there. That bank could therefore no longer serve as a test of v15.
3. The criterion above was written for v15 in the script that then generated a new bank of
   1328 questions (the confirmatory bank) on frames at least 1.5 s away from every frame of
   the development bank.

## What the record shows and what it does not show

- The criterion was part of the script that generated the bank, and that script was last
  saved before the bank was generated and 23 minutes before the first arm started.
- The times are file times and log times of the authors' machine. The criterion was not
  registered with a third party, and the version history of the project repository begins
  one day later (2026-08-09, with the commit that fixes the probe banks).
- The 3B VLM arm of this run had a fault of the serving software (parse rate 0.244); it was
  run again on 2026-08-09 with a rule that reloads the model, as the manuscript describes.
- The later additions `A3_amendment.md`, `A4_amendment.md`, `A5_amendment.md`, and
  `A5_addendum2.md` were committed to the project repository before the runs that they
  govern. `exp_rev1/B123_PREREG.md` was written before the runs that it governs.
