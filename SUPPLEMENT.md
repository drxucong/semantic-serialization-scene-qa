# Supplement

This file is the supplementary material for

> **Free the Language Model From the Vision Encoder: Semantic Serialization as a
> Perception Interface for Small Language Models**
> Cong Xu and Ravi Sankar, iCONS Lab, University of South Florida

Wherever the paper says "the supplement", it means this document and the files it
points to in this repository. Every path below is relative to the repository root and
was checked to exist at the time of writing. Every analysis script runs from the
repository root, for example `python analysis/v12_rule_fix.py`.

The repository is an **evaluation release**. It contains the question banks, the
per-item prediction log of every arm, the perceived states, the frozen preregistration
amendments, and the analysis scripts, so that the reported statistics can be
recomputed independently. It does not contain the perception or serializer
implementation. What is and is not included is stated explicitly at the end.

---

## Where each pointer in the paper leads

| # | Paper location | What the paper points to | Where it is |
|---|---|---|---|
| 1 | §III, audit gates | the occlusion audit behind the clean-subset contrasts | `results/exp2_predictions/preds_cf_occlusion_clean.csv` (n = 1298 clean subset; the two contrasts recompute from it). **The object-level audit record itself is not shipped** — see *Not included*. |
| 2 | §III, arms | the fixed-ground-truth-content ladder: serializer vs. an older serializer vs. a prose caption (0.955 / 0.857 / 0.804, development bank, exploratory) | `analysis/paper1_controls.json` (keys `gtv9_vs_v9`, `gtv9_vs_gtv3`, `gtv9_vs_raw`, `gtv9_vs_anno`) and the caption arm's per-item logs, `results/phase10/results_qwen2.5_3b/caption__clean__forced.jsonl` and `results/phase10/results_qwen2.5_7b/caption__clean__forced.jsonl` |
| 3 | §IV, serializer | the four distinct sector-agreement quantities, separated | `analysis/check_sector.py` (object-level and one question-level rule) and `analysis/v12_rule_fix.py` (the shipped bearing rule vs. the generator's column rule, which is where the paper's 0.553 / 0.761 come from). See *Errata*. |
| 4 | §VI, frozen criterion | the *p* values obtained by CI inversion | `analysis/stats_for_revision.txt` — the primary confirmatory endpoint analysis, including the two endpoint *p* values and the intersection–union max |
| 5 | §VI, amendment discipline | the full amendment ledger with commit hashes and per-amendment predictions | `amendments/` — `A3_amendment.md`, `A4_amendment.md`, `A5_amendment.md`, `A5_addendum2.md`, plus `d_ladder_spec.md` and `schema.md` |
| 6 | §VI, instrument validation | the repeated-run narrative behind the ±0.0015 same-machine bound | `analysis/repeat_results.json` and `analysis/repeat_analysis.py`. **The plots are not shipped**; the numbers they were drawn from are. |
| 7 | Table III caption | the two same-decoder VL-on-text auxiliary arms, read on parsed items | `analysis/iface2_confirm.json` (full-set and `parsed_only` deltas with CIs and item counts) |
| 8 | §VII, mechanism | the operator-ladder tables | `analysis/paper1_controls.json` (keys `ladder_acc`, `ladder_increments`, `L0_vs_pixel`) |
| 9 | Table V caption | the full supervision ledger | `summaries/SUMMARY3_full.md` and the per-item logs under `results/exp3_predictions/` |
| 10 | §VIII, error attribution | the paired ground-truth-versus-perceived counterfactual | `analysis/gt_oracle_confirm.json` and `results/exp2_predictions/predictions2_gtcf.csv` |
| 11 | Appendix A, arm glossary | the amendment ledger recording each arm's full configuration and any deviation | `amendments/` together with `summaries/arms_master_table.md` |
| 12 | Data and Code Availability | the perception stack and serializer specified to reproduction detail | `amendments/d_ladder_spec.md` (the serializer variants D0–D3), `states/` (the frozen perceived states each arm actually read), and `README.md`. **The implementation source is not shipped** — see *Not included*. |

## Other material worth knowing about

| Topic | File |
|---|---|
| Primary endpoints, per-family contrasts, reproducibility floor | `analysis/stats_for_revision.txt` |
| Confirmatory-bank pass/fail against the frozen criterion | `analysis/confirm_table.txt` |
| Oracle ceilings and the operator ladder on the development bank | `analysis/final_table.txt` |
| Bank composition, separation, and leakage audit | `analysis/bank_audit.txt`, `analysis/nn_audit.txt`, `analysis/audit/bank_leakage_audit.py` |
| Visible-scope construction | `analysis/audit/audit_visibility.py` |
| Frozen-file hashes | `analysis/audit/hash_manifest_p1.py` |
| Reader-scale sweep, per-item | `results/exp2_predictions/predictions2_cf.csv`, `predictions2_gtcf.csv`, `predictions2_n2.csv` |
| Option-aware learned baselines | `summaries/baselines.md`, `summaries/baselines_n1n2.md`, `results/baselines/` |
| Blind arm | `summaries/blind_audit.md` (see *Errata*), `results/exp3_infer/blind_cf_3b`, `results/exp3_infer/blind_cf_7b` |
| Compute and latency | `summaries/compute_table.md` |
| Question banks | `banks/qa_coda.jsonl` (development, 1366), `banks/qa_confirm.jsonl` (confirmatory, 1328), `banks/n1_bank.jsonl`, `banks/n2_bank.jsonl` |
| Serialized-state exemplars | `exemplars/serialized_state_examples.json` |

## A note on the two bootstrap runs

Two 21-cluster bootstraps of the same paired predictions exist in this release. The
paper's headline and per-family numbers all come from `analysis/stats_for_revision.txt`,
the primary confirmatory endpoint analysis, and that is the run whose max *p* the paper
quotes. `summaries/table2_per_family.md` is a separate run of the same quantities and
differs from it in the fourth decimal. If a value in the paper does not match
`table2_per_family.md` exactly, this is why; compare against `stats_for_revision.txt`.

## Denominators on N2

The N2 bank holds 3974 items. The text arms are scored on 3971 of them and the pixel
arms on all 3974 (verify in `results/exp2_predictions/predictions2_n2.csv`, column
`arm`). Contrasts reported in the paper are paired on the common items, which is why a
contrast may differ in the fourth decimal from the difference of the two per-arm
accuracies in the reader-scale table.

## Errata for this release

1. **`summaries/blind_audit.md` is stale.** It states that no blind arm was ever run on
   the confirmatory bank. That was true when it was written and is no longer true: the
   confirmatory blind runs are in `results/exp3_infer/blind_cf_3b` and
   `results/exp3_infer/blind_cf_7b`, and the paper's 0.4142 / 0.4089 come from them.
   Use the per-item logs, not that summary.
2. **`analysis/check_sector.py` and `analysis/v12_rule_fix.py` compute the same-named
   sector agreement two different ways**, so they report different numbers and both are
   right for what they measure. The paper's question-level figures come from
   `v12_rule_fix.py`, which scores each rule on the direction family with unparsed items
   counted as failures: `171/309 = 0.5534` for the shipped bearing rule and
   `235/309 = 0.7605` for the generator's image-column rule. `check_sector.py` measures
   rule-versus-rule agreement instead and reports object-level `18821/19130 = 0.984`.
3. **The Section VIII attribution counts follow `reattribute.py` as released** - 43
   undetected classes, 40 ordering errors, no sector flips, summing to the 83 items on
   which the option-blind rule fails. An earlier run of the same analysis, which is not
   archived here, split one borderline item the other way and reported 39 ordering errors
   with 1 sector flip; the totals were identical either way. The released script is the
   one to trust, and its counts are stable across its own tolerance sweep.

## Not included in this release

Stated plainly so that nothing here promises more than it delivers:

- **The perception and serializer implementation.** This is an evaluation release. The
  perceived states that every arm actually read are provided in `states/`, and the
  serializer variants are specified in `amendments/d_ladder_spec.md`, but the source is
  withheld.
- **Trained detector weights.** Available on reasonable request.
- **CODa images.** Not redistributed; obtain them from the CODa authors. The data in
  this repository inherits CODa's CC BY-NC-SA 4.0 licence.
- **The object-level occlusion audit record.** The clean-subset predictions it produced
  are included; the audit record itself is not.
- **Plot files.** Figures in the paper were generated from the released numbers; the
  plotting outputs are not shipped.
- **Training corpora for the supervised arms.** The per-item predictions of those arms
  are included; the fine-tuning data is not.

---

Licences: data CC BY-NC-SA 4.0 (inherited from CODa), code MIT. See `LICENSE-DATA` and
`LICENSE-CODE`.
