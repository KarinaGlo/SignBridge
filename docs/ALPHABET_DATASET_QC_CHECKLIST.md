# BISINDO ALPHABET DATASET QC CHECKLIST (PHASE 1)

## 1. CSV Integrity
- [x] Verify Validator A (`VAL-A`) contains exactly 36 records (`VAL-REV-001`–`VAL-REV-036`).
- [x] Verify Validator B (`VAL-B`) contains exactly 36 records (`VAL-REV-001`–`VAL-REV-036`).
- [x] Confirm all 7 required columns exist with no duplicate, missing, or unexpected `sample_id`s.
- [x] Confirm `decision` values belong strictly to `{IDENTIFIED, AMBIGUOUS, UNDETERMINABLE}`.
- [x] Preserve empty `notes`, `identified_letter`, and `regional_variation` values without silent coercion.
- [x] Document that source CSVs were not present on disk in `D:\SEMESTER 5\ML\Projek_1` and were ingested verbatim from user-provided payloads.

## 2. Validator Comparison & Agreement Analysis
- [x] Merge Validator A and Validator B on `sample_id` into [`VALIDATOR_COMPARISON.csv`](file:///d:/SEMESTER%205/ML/Projek_1/docs/dataset_validation/alphabet/VALIDATOR_COMPARISON.csv).
- [x] Classify all 36 records into mutually exclusive `disagreement_category` classes.
- [x] Export all 21 decision/letter disagreement records to [`VALIDATOR_DISAGREEMENTS.csv`](file:///d:/SEMESTER%205/ML/Projek_1/docs/dataset_validation/alphabet/VALIDATOR_DISAGREEMENTS.csv).
- [x] Compute decision agreement (17/36 = 47.22%), Cohen's kappa ($\kappa = 0.109375$), both-`IDENTIFIED` letter agreement (11/11 = 100%), and regional variation agreement (29/36 = 80.56%) in [`VALIDATOR_AGREEMENT_SUMMARY.csv`](file:///d:/SEMESTER%205/ML/Projek_1/docs/dataset_validation/alphabet/VALIDATOR_AGREEMENT_SUMMARY.csv).

## 3. Image Traceability
- [x] Map all 36 `sample_id`s to `docs/validation_p2/phase_2b_1/stimulus_images/VAL-REV-XXX.jpg`.
- [x] Cross-reference `STIMULUS_SHA256_MANIFEST.csv` and `INTERNAL_SAMPLE_MAPPING.md` for processed paths and original Mendeley filenames.
- [x] Visually inspect all 25 non-`FULL_AGREEMENT` stimulus images before documenting visual issues.

## 4. Expert Adjudication
- [x] Generate [`VALIDATOR_ADJUDICATION_TEMPLATE.csv`](file:///d:/SEMESTER%205/ML/Projek_1/docs/dataset_validation/alphabet/VALIDATOR_ADJUDICATION_TEMPLATE.csv) with `expert_final_letter`, `expert_final_decision`, `expert_notes`, `adjudicator_id`, and `adjudication_date` left blank.
- [ ] Qualified BISINDO expert reviews the 25 `adjudication_required = TRUE` samples.
- [ ] Record expert decisions and adjudication dates without overwriting original Validator A/B columns.

## 5. Final QC Approval
- [x] Generate [`ALPHABET_DATASET_QC_FINAL.csv`](file:///d:/SEMESTER%205/ML/Projek_1/docs/dataset_validation/alphabet/ALPHABET_DATASET_QC_FINAL.csv) distinguishing provisional validator agreement (11) from unresolved samples (25).
- [ ] Reconcile `final_qc_status` after expert adjudication completes.
- [ ] Confirm `TEST_SET_DIAGNOSTIC_ONLY` firewall is respected before any downstream P2 work.
