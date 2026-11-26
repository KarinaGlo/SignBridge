# BISINDO ALPHABET DATASET QUALITY CONTROL REPORT (PHASE 1)
## SignBridge ID–PH (BISINDO ↔ FSL) Multimodal Classroom Bridge

> [!IMPORTANT]
> **AUDIT SCOPE & GOVERNANCE**
> - **Dataset Scope**: 36-image validation subset (`VAL-REV-001` through `VAL-REV-036`) from the **BISINDO Alphabet Image Data (Mendeley)** dataset. This audit does **not** cover the dynamic multimodal Recorder dataset and does **not** claim validation of all 8,620 Mendeley images.
> - **Source Immutability**: Original Validator A and Validator B responses, Mendeley source images, and P1/M6 model artifacts were preserved unmodified.
> - **No Fabricated Ground Truth**: Expert adjudication fields remain empty pending review by a qualified BISINDO expert.

---

## 1. Project Context

This report documents Phase 1 finalization of human validation results from **Validator A (`VAL-A`)** and **Validator B (`VAL-B`)** for 36 anonymized BISINDO alphabet stimulus images (`VAL-REV-001` to `VAL-REV-036`). The objective is to establish an auditable, reproducible quality-control (QC) baseline separating validator agreement, unresolved disagreements, and pending expert adjudication.

---

## 2. Input Files & Record Counts

| Source | Expected Filename | Repository Disk Status | Ingestion Source | Records | Review Date |
| :--- | :--- | :--- | :--- | :---: | :---: |
| **Validator A** | `VALIDATOR_A_RESPONSE_ACTUAL (2).csv` | Not found on disk in `D:\SEMESTER 5\ML\Projek_1` | Ingested verbatim from user-provided CSV payload | 36 | `2026-11-19` |
| **Validator B** | `VALIDATOR_B_RESPONSE_ACTUAL (1).csv` | Not found on disk in `D:\SEMESTER 5\ML\Projek_1` | Ingested verbatim from user-provided CSV payload | 36 | `2026-11-23` |

*Note*: [`docs/validation_p2/phase_2c/raw_responses/`](file:///d:/SEMESTER%205/ML/Projek_1/docs/validation_p2/phase_2c/raw_responses/) contained only `.gitkeep` at the time of audit. Both CSV payloads were preserved verbatim without altering any cell values.

---

## 3. Input Integrity Audit Results (Phase A)

Both validator datasets passed all structural integrity checks:

1. **Record Count**: Exactly **36 records** in each file.
2. **Schema**: Exact 7 required columns in both files: `validator_code`, `sample_id`, `identified_letter`, `decision`, `regional_variation`, `notes`, `review_date`.
3. **Sample ID Completeness & Uniqueness**: `VAL-REV-001` through `VAL-REV-036` present once each (36 unique IDs, 0 duplicates, 0 missing, 0 unexpected).
4. **Validator Code Consistency**: `VAL-A` (36/36) in Validator A; `VAL-B` (36/36) in Validator B.
5. **Decision Enum Validity**: Only supported values observed:
   - **Validator A**: `IDENTIFIED` (22), `AMBIGUOUS` (10), `UNDETERMINABLE` (4).
   - **Validator B**: `IDENTIFIED` (17), `AMBIGUOUS` (13), `UNDETERMINABLE` (6).
6. **Identified Letter Validity**: All non-empty values are valid uppercase A–Z letters. Empty values are preserved as missing:
   - **Validator A**: 2 empty (`VAL-REV-027` with `UNDETERMINABLE`, `VAL-REV-033` with `AMBIGUOUS`).
   - **Validator B**: 1 empty (`VAL-REV-019` with `AMBIGUOUS`).
7. **Regional Variation Values** (preserved as-is without silent normalization):
   - **Validator A**: `NO` (32), `UNSURE` (2), empty `""` (2).
   - **Validator B**: `NO` (33), empty `""` (3).
8. **Notes Preservation**: Empty `notes` (A: 28, B: 26) are preserved as missing values and never interpreted as agreement. Non-empty notes (A: 8, B: 10) are retained verbatim.

---

## 4. Comparison Methodology (Phase B)

Validator A and Validator B responses were inner-joined on `sample_id` into [`VALIDATOR_COMPARISON.csv`](file:///d:/SEMESTER%205/ML/Projek_1/docs/dataset_validation/alphabet/VALIDATOR_COMPARISON.csv). Each sample was classified into mutually exclusive `disagreement_category` classes:

- `FULL_AGREEMENT`: Both `decision == IDENTIFIED` and `A_identified_letter == B_identified_letter`.
- `LETTER_DISAGREEMENT`: Both `decision == IDENTIFIED` and letters differ.
- `IDENTIFIED_VS_AMBIGUOUS`: One `IDENTIFIED`, one `AMBIGUOUS`.
- `IDENTIFIED_VS_UNDETERMINABLE`: One `IDENTIFIED`, one `UNDETERMINABLE`.
- `AMBIGUOUS_VS_UNDETERMINABLE`: One `AMBIGUOUS`, one `UNDETERMINABLE`.
- `BOTH_AMBIGUOUS`: Both `AMBIGUOUS`.
- `BOTH_UNDETERMINABLE`: Both `UNDETERMINABLE`.
- `OTHER_OR_INVALID`: Any other combination.

---

## 5. Agreement Metrics & Statistical Analysis (Phase C)

Aggregate metrics are stored in [`VALIDATOR_AGREEMENT_SUMMARY.csv`](file:///d:/SEMESTER%205/ML/Projek_1/docs/dataset_validation/alphabet/VALIDATOR_AGREEMENT_SUMMARY.csv).

### 5.1 Decision Agreement
- **Identical decisions**: **17 / 36 (47.22%)** (11 both `IDENTIFIED`, 6 both `AMBIGUOUS`).
- **Decision disagreements**: **19 / 36 (52.78%)**.

### 5.2 Letter Agreement
1. **Across all 36 samples (raw `identified_letter` comparison)**:
   - Matching non-empty letters: **26 / 36 (72.22%)** — *Warning*: 15 of these 26 matches occur where at least one validator chose `AMBIGUOUS` or `UNDETERMINABLE` and therefore do **not** represent `FULL_AGREEMENT`.
   - Differing non-empty letters: **7 / 36 (19.44%)** (`VAL-REV-001`, `007`, `010`, `014`, `020`, `025`, `031`).
   - One missing letter: **3 / 36 (8.33%)** (`VAL-REV-019`, `027`, `033`).
2. **Eligible subset where BOTH validators selected `IDENTIFIED`**:
   - Eligible samples: **11 / 36 (30.56%)**.
   - Matching letters: **11 / 11 (100.00%)**.
   - Different letters: **0 / 11 (0.00%)**.

### 5.3 Regional Variation Agreement
- Exact match (`NO` vs `NO`): **29 / 36 (80.56%)**.
- Mismatch (`UNSURE` vs `NO`): **2 / 36 (5.56%)** (`VAL-REV-001`, `VAL-REV-027`).
- One empty (not equated to `NO` or `UNSURE`): **5 / 36 (13.89%)** (`VAL-REV-013`, `014`, `019`, `033`, `034`).

### 5.4 Disagreement Category Distribution

| Disagreement Category | Count | % of 36 |
| :--- | :---: | :---: |
| `FULL_AGREEMENT` | 11 | 30.56% |
| `LETTER_DISAGREEMENT` | 0 | 0.00% |
| `IDENTIFIED_VS_AMBIGUOUS` | 9 | 25.00% |
| `IDENTIFIED_VS_UNDETERMINABLE` | 8 | 22.22% |
| `AMBIGUOUS_VS_UNDETERMINABLE` | 2 | 5.56% |
| `BOTH_AMBIGUOUS` | 6 | 16.67% |
| `BOTH_UNDETERMINABLE` | 0 | 0.00% |
| **Total** | **36** | **100.00%** |

### 5.5 Inter-Rater Reliability (Cohen's Kappa)
- **Decision Field (`IDENTIFIED`, `AMBIGUOUS`, `UNDETERMINABLE`, $N=36$)**:
  - Observed agreement: $P_o = 17/36 = 0.472222$
  - Expected agreement: $P_e = \frac{22\cdot 17 + 10\cdot 13 + 4\cdot 6}{36^2} = \frac{528}{1296} = 0.407407$
  - **Cohen's Kappa**: $\kappa = \frac{0.472222 - 0.407407}{1 - 0.407407} = \mathbf{0.109375}$ (*Slight agreement* on Landis & Koch scale).
  - *Confusion Matrix (Rows = A, Cols = B)*: `IDENTIFIED`→(11, 5, 6); `AMBIGUOUS`→(4, 6, 0); `UNDETERMINABLE`→(2, 2, 0).
- **Identified Letter Field**:
  - A full-sample ($N=36$) letter $\kappa$ is **not statistically appropriate** because 25 samples involve `AMBIGUOUS`/`UNDETERMINABLE` decisions or missing letters across a sparse 26-class alphabet.
  - On the $N=11$ `BOTH_IDENTIFIED` subset, agreement is 11/11 (100%, spanning 7 letters: A, B, C, F, N, O, Y), which is conditioned on rater certainty and cannot be generalized as population-wide letter $\kappa$.
- **Limitations**: With only **2 validators** and **$N=36$** purposively sampled diagnostic/outlier images (19 test diagnostic + 17 train/val), $\kappa$ has wide confidence intervals and reflects threshold differences (e.g., Validator B marking low-light images `UNDETERMINABLE` where Validator A still attempted `IDENTIFIED`).

---

## 6. Disagreement Investigation & Visual Inspection (Phase D)

All **21 samples** with decision or letter disagreement are recorded in [`VALIDATOR_DISAGREEMENTS.csv`](file:///d:/SEMESTER%205/ML/Projek_1/docs/dataset_validation/alphabet/VALIDATOR_DISAGREEMENTS.csv), and all **25 non-`FULL_AGREEMENT` samples** (including the 4 `BOTH_AMBIGUOUS` matching-letter samples) were directly inspected via their stimulus JPGs:

| Sample ID | Category | A (Letter, Dec) | B (Letter, Dec) | Original Label | Visual Inspection & Notes Summary | Recommended Action |
| :--- | :--- | :--- | :--- | :---: | :--- | :--- |
| `VAL-REV-001` | `BOTH_AMBIGUOUS` | P, AMB (`UNSURE`) | K, AMB (`NO`) | K | Two-handed horizontal index on curled hand; angle makes K vs P ambiguous. | Expert adjudication + image review |
| `VAL-REV-002` | `BOTH_AMBIGUOUS` | C, AMB | C, AMB | C | Curved C-shape with shadow on beige background. | Expert confirmation |
| `VAL-REV-004` | `IDENTIFIED_VS_AMBIGUOUS` | C, AMB | C, ID | R | Curved index/thumb forming C-like shape; both validators read C vs Mendeley label R. | Expert adjudication (possible label error) |
| `VAL-REV-005` | `IDENTIFIED_VS_AMBIGUOUS` | M, ID | M, AMB | M | Two-handed M configuration over open palm. | Expert adjudication |
| `VAL-REV-007` | `BOTH_AMBIGUOUS` | D, AMB | O, AMB | D | Dark fabric background; two-handed loop; A notes *"Sudut kamera salah"*. | Expert adjudication + image review |
| `VAL-REV-009` | `IDENTIFIED_VS_AMBIGUOUS` | I, ID | I, AMB | J | Static frame of dynamic J; raised finger against busy wall; A notes *"Sudut kamera"*. | Expert adjudication (dynamic J limitation) |
| `VAL-REV-010` | `IDENTIFIED_VS_AMBIGUOUS` | E, AMB | W, ID | E | Three fingers extended upward, thumb tucked; A notes *"Sudut kamera salah"*. | Expert adjudication |
| `VAL-REV-013` | `BOTH_AMBIGUOUS` | T, AMB | T, AMB | T | Two-handed T configuration; A left `regional_variation` empty. | Expert confirmation |
| `VAL-REV-014` | `IDENTIFIED_VS_AMBIGUOUS` | E, AMB | W, ID | E | Three splayed fingers with bent thumb; visually resembles W/E; B left `regional_variation` empty. | Expert adjudication |
| `VAL-REV-016` | `IDENTIFIED_VS_AMBIGUOUS` | Z, ID | Z, AMB | Z | Blurry side-angle bent wrist, partially cropped; B notes cropped hand. | Expert adjudication |
| `VAL-REV-017` | `IDENTIFIED_VS_UNDETERMINABLE` | O, ID | O, UND | O | Very dark background/low lighting; B notes *"Pencahayaan kurang"*. | Expert adjudication |
| `VAL-REV-018` | `IDENTIFIED_VS_UNDETERMINABLE` | C, ID | C, UND | C | Very dark background/low lighting; B notes *"Pencahayaan kurang"*. | Expert adjudication |
| `VAL-REV-019` | `AMBIGUOUS_VS_UNDETERMINABLE` | Z, UND | *empty*, AMB | Z | Very dark side-angle static Z; B left letter & `regional_variation` empty. | Expert adjudication + image review |
| `VAL-REV-020` | `IDENTIFIED_VS_UNDETERMINABLE` | V, ID | B, UND | V | Plain background, soft/slightly blurry V-shape; B marked B/UND (*"Pencahayaan kurang"*). | Expert adjudication |
| `VAL-REV-021` | `IDENTIFIED_VS_UNDETERMINABLE` | B, ID | B, UND | B | Very dark background; two-handed B; B notes *"Pencahayaan kurang"*. | Expert adjudication |
| `VAL-REV-024` | `IDENTIFIED_VS_UNDETERMINABLE` | D, ID | D, UND | D | Very dark background & angled pose; B notes low light + awkward position. | Expert adjudication |
| `VAL-REV-025` | `IDENTIFIED_VS_AMBIGUOUS` | D, ID | H, AMB | H | Two-handed H-like configuration; B notes awkward angle. | Expert adjudication |
| `VAL-REV-026` | `IDENTIFIED_VS_UNDETERMINABLE` | Z, ID | Z, UND | Z | Side-angle flat hand; B notes cropped/incomplete hand. | Expert adjudication |
| `VAL-REV-027` | `IDENTIFIED_VS_UNDETERMINABLE` | *empty*, UND (`UNSURE`) | S, ID (`NO`) | Z | Two-handed pinched/hooked shape; A notes *"Gaada gesture kek gitu"*; Mendeley label Z. | Expert adjudication (high priority) |
| `VAL-REV-028` | `IDENTIFIED_VS_AMBIGUOUS` | O, ID | O, AMB | O | Thumb-index circle with 3 fingers raised. | Expert adjudication |
| `VAL-REV-030` | `IDENTIFIED_VS_UNDETERMINABLE` | M, UND | M, ID | M | Rotated two-handed M gesture; A notes *"Salah posisi tangan"*. | Expert adjudication |
| `VAL-REV-031` | `AMBIGUOUS_VS_UNDETERMINABLE` | U, UND | C, AMB | U | Cluttered red printed t-shirt background; ambiguous finger curl; A notes *"?"*. | Expert adjudication + image review |
| `VAL-REV-033` | `IDENTIFIED_VS_AMBIGUOUS` | *empty*, AMB | B, ID | B | Motion-blurred two-handed B on tie-dye fabric; A left letter & `regional_variation` empty. | Expert adjudication |
| `VAL-REV-034` | `BOTH_AMBIGUOUS` | L, AMB | L, AMB | L | Inverted/upside-down L against striped fabric; both note camera rotation/position. | Expert confirmation / rotation check |
| `VAL-REV-036` | `BOTH_AMBIGUOUS` | Y, AMB | Y, AMB | Y | Awkward finger configuration on striped fabric; A: *"Krg jelas"*, B: *"Konfigurasi jari janggal"*. | Expert confirmation + image review |

---

## 7. Image-to-Sample Traceability (Phase E)

All **36 / 36** `sample_id` records are 100% traceable via [`STIMULUS_SHA256_MANIFEST.csv`](file:///d:/SEMESTER%205/ML/Projek_1/docs/validation_p2/phase_2b_2/STIMULUS_SHA256_MANIFEST.csv) and [`INTERNAL_SAMPLE_MAPPING.md`](file:///d:/SEMESTER%205/ML/Projek_1/docs/validation_p2/phase_2b_1/INTERNAL_SAMPLE_MAPPING.md) to:
- Anonymized stimulus JPGs in [`docs/validation_p2/phase_2b_1/stimulus_images/`](file:///d:/SEMESTER%205/ML/Projek_1/docs/validation_p2/phase_2b_1/stimulus_images/) (`VAL-REV-001.jpg`–`VAL-REV-036.jpg`).
- Processed dataset paths (`data/processed/bisindo_alphabet/<LETTER>/<LETTER>_XXXX.jpg`).
- Original Mendeley filenames and documented original labels.

---

## 8. Adjudication Requirements & QC Decision Rules (Phases F & G)

Per [`VALIDATOR_ADJUDICATION_TEMPLATE.csv`](file:///d:/SEMESTER%205/ML/Projek_1/docs/dataset_validation/alphabet/VALIDATOR_ADJUDICATION_TEMPLATE.csv) and [`ALPHABET_DATASET_QC_FINAL.csv`](file:///d:/SEMESTER%205/ML/Projek_1/docs/dataset_validation/alphabet/ALPHABET_DATASET_QC_FINAL.csv):

- **Total samples reviewed**: 36
- **Validator agreement (`FULL_AGREEMENT`, provisional use eligible)**: **11** (`QC_PENDING` — awaiting protocol/expert sign-off; not claimed as final expert-adjudicated ground truth).
- **Expert-adjudicated ground truth**: **0** (all `expert_*` fields intentionally left blank).
- **Samples requiring expert adjudication (`QC_REQUIRES_ADJUDICATION`)**: **17** (`9 IDENTIFIED_VS_AMBIGUOUS` + `8 IDENTIFIED_VS_UNDETERMINABLE`).
- **Samples requiring image inspection & expert review (`QC_REQUIRES_IMAGE_REVIEW`)**: **8** (`2 AMBIGUOUS_VS_UNDETERMINABLE` + `6 BOTH_AMBIGUOUS`).
- **Total unresolved samples**: **25** (`final_ground_truth_eligible = FALSE` for all 36 until expert adjudication completes).
- **Missing image mapping**: **0**.

---

## 9. Recommendations for Subsequent Use

1. **Conduct Expert Adjudication**: Have a qualified BISINDO linguist/expert complete [`VALIDATOR_ADJUDICATION_TEMPLATE.csv`](file:///d:/SEMESTER%205/ML/Projek_1/docs/dataset_validation/alphabet/VALIDATOR_ADJUDICATION_TEMPLATE.csv) for all 25 unresolved samples (prioritizing `VAL-REV-004`, `009`, `010`, `014`, `025`, `027` where validator readings diverge from Mendeley labels).
2. **Maintain Test-Set Firewall**: 19 of the 36 samples are tagged `TEST_SET_DIAGNOSTIC_ONLY` and must not be used for model tuning or hyperparameter selection.
3. **Do Not Generalize to Full 8,620 Images**: These 36 samples represent a targeted diagnostic/outlier audit, not a random sample of the entire Mendeley dataset.
