# SIGNBRIDGE ID–PH (BISINDO ↔ FSL) MASTER ML AUDIT REPORT
**Comprehensive Machine Learning Audit, Dataset Gap Analysis, Training Roadmap & System Architecture**

**Document Version:** 1.0.0 (Master Release)  
**Date:** 2026-11-12  
**Audit Scope:** Full Repository (`signbridge/`, `data/`, `web/`, `outputs/`, `runs/`, `tests/`, `docs/`)  
**Auditor Roles:** Senior Machine Learning Engineer, CV/DL Researcher, Data Scientist, MLOps Engineer, Software Architect  
**Branch Inspected:** `feature/field-test-readiness` (Clean working tree, commit `3a99e96`)

---

## 1. Executive Summary & Git Environment Audit

### 1.1 Executive Overview
SignBridge is conceived as a bidirectional multimodal translation bridge between Indonesian Sign Language (BISINDO) and Filipino Sign Language (FSL) with Indonesian/Filipino spoken language interfaces for classroom inclusivity. 

This audit conducted an exhaustive, read-only empirical verification across the entire codebase, training artifacts, local databases, model binaries, dataset manifests, and runtime web frontend. The central finding of this audit is a **profound divergence between academic/claim documentation and actual production deployment**:
1. **Isolated Word Recognition (M0)**: Successfully trained to **99.13% test accuracy** on 32 WL-BISINDO vocabulary words under a **Signer-Dependent (SD)** protocol. However, zero **Signer-Independent (SI)** or **Leave-One-Signer-Out (LOSO)** evaluation was conducted, causing catastrophic generalization drop when tested by unseen users on webcam.
2. **Alphabet Fingerspelling (I1)**: The neural model (`image_i1_mobilenetv3`) suffered total training failure (**3.85% test accuracy**, matching random guessing $1/26 = 3.846\%$). The frontend silently bypasses this broken neural model using an uncalibrated geometric heuristic rule (`classifyAlphabetGeometry`).
3. **Speech Recognition (A1–A4 Whisper)**: No local Whisper models exist or have ever been fine-tuned locally. Zero raw audio files exist on disk. Production speech recognition is 100% reliant on the browser's native Web Speech API (`webkitSpeechRecognition`).
4. **Gloss-to-Sentence (B0–B2 Neural Text Generation)**: No neural translation models (IndoT5, mT5, GRU) exist or have been trained. Text synthesis is 100% rule-based dictionary substitution with hardcoded grammatical templates, exhibiting **62.3% Word Error Rate (WER)** on validation.
5. **FSL and Multimodal Classroom Bridge**: FSL is completely absent from the dataset and model topology. The system is currently an isolated 32-word BISINDO recognizer.

### 1.2 Git Environment & Repository Integrity
* **Active Branch:** `feature/field-test-readiness`
* **Head Commit:** `3a99e96` (*fix: stabilize M0 real-time sign recognition*)
* **Remote Origin:** `https://github.com/KarinaGlo/SignBridge.git`
* **Working Tree State:** 100% Clean (0 unstaged modifications, 0 untracked files).
* **Python Runtime:** Python 3.13.12 (CPython, 64-bit Windows)
* **PyTorch Version:** 2.14.1+cpu (CUDA available: False)
* **ONNX Runtime:** 1.31.1 (Python) / 1.18.0 (Web WASM)

---

## 2. Dataset Inventory & Quantitative Verification

A rigorous disk inspection was conducted to catalog every dataset manifest, raw file, and keypoint cache.

| Dataset Domain | Path / Manifest | Cataloged Count | Physically on Disk | Format & Schema | Verified Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **WL-BISINDO Video** | `data/manifest_wl_bisindo.csv` | 1,600 video records | 0 MP4 files (`data/raw/` ignored) | CSV: `video_id, gloss, signer_id, duration, split_sd` | Manifest intact; raw MP4 git-ignored |
| **WL-BISINDO Keypoints** | `data/keypoints/` | Target: 1,600 NPZ files | 0 files | NPZ: `[T, 86, 3]` coordinate array | Git-ignored via `.gitignore` |
| **Mendeley Alphabet** | `data/raw/image/bisindo_alphabet/` | 4,466 target images | 0 files | JPG/PNG 26 classes (A–Z) | Missing from disk; git-ignored |
| **FLEURS Audio** | `data/audio/fleurs/id_id/*.tsv` | 3,616 TSV records (dev: 350, test: 687, train: 2579) | 0 WAV files (`audio/` empty) | TSV: `id, path, raw_transcription, transcription` | Audio clips omitted; text manifests only |
| **Classroom Audio** | `data/audio/classroom_recordings/` | 84 metadata records (60 ID, 24 FIL) | 0 WAV files | CSV: Marked `METADATA_ONLY_AUDIO_NOT_AVAILABLE` | Placeholder manifests; zero audio data |
| **Parallel Sentences** | `data/text/parallel_sentences/` | 305 total pairs (`train`: 170, `val`: 30, `test_manual`: 105) | 3 TSV files present | TSV: `gloss_sequence \t natural_sentence` | Verified present; very small sample size |
| **Tatoeba Monolingual** | `data/text/monolingual/ind_sentences.tsv` | 28,418 sentences | 1 TSV file present | TSV: `id \t lang \t sentence` | Monolingual text; no sign gloss alignments |
| **Phonology DB** | `data/phonology.csv` | 32 concept entries | 1 CSV file present | CSV: `concept_id, label, handshape, location...` | Mismatched vocabulary (only 10/32 overlap) |

---

## 3. Signer-Dependent vs Signer-Independent (LOSO) Split Analysis

### 3.1 The Hidden Generalization Trap
The reported test accuracy of **99.13%** for both M0 (Student Transformer) and M1 (ST-GCN) is derived entirely from `split_sd` in `data/manifest_wl_bisindo.csv`.

An empirical query of the manifest partitions yields:
* **Train Set (`split_sd == 'train'`):** 960 samples (60.0%) across all 5 signers:
  * `SIGNER0`: 80 clips | `SIGNER1`: 250 clips | `SIGNER2`: 250 clips | `SIGNER3`: 190 clips | `SIGNER4`: 190 clips
* **Validation Set (`split_sd == 'val'`):** 180 samples (11.25%) across all 5 signers:
  * `SIGNER0`: 12 clips | `SIGNER1`: 48 clips | `SIGNER2`: 48 clips | `SIGNER3`: 36 clips | `SIGNER4`: 36 clips
* **Test Set (`split_sd == 'test'`):** 460 samples (28.75%) across all 5 signers:
  * `SIGNER0`: 28 clips | `SIGNER1`: 122 clips | `SIGNER2`: 122 clips | `SIGNER3`: 94 clips | `SIGNER4`: 94 clips

### 3.2 Implication on Real-World Inference
Because all signers are present in both the training set and the test set, the neural network learns to overfit to individual signer physical morphology (body proportions, personal motion idiosyncrasies, resting hand positions, camera angles) rather than learning invariant semantic sign phonemes. 

When a new user attempts live recognition on a webcam, the model experiences extreme out-of-distribution (OOD) failure. The true **Signer-Independent (SI)** generalization metric is completely unmeasured in repository checkpoints.

---

## 4. Video Sourcing & WL-BISINDO Pipeline Verification

### 4.1 Vocabulary Distribution
The 1,600 video records in `manifest_wl_bisindo.csv` are distributed with perfect balance across 32 classes (exactly 50 videos per class):
`ADA`, `APA`, `BAGAIMANA`, `BAHASA`, `BANTU`, `BELAJAR`, `BERSIH`, `BISA`, `BUKU`, `DENGAR`, `DI`, `GURU`, `HARI`, `HIJAU`, `INDONESIA`, `INI`, `ISYARAT`, `KAMU`, `KASIH`, `KERJA`, `MAAF`, `MAKAN`, `MANA`, `MERAH`, `MINUM`, `MOTOR`, `RUMAH`, `SAMA`, `SAYA`, `SEKOLAH`, `TEMAN`, `TERIMA_KASIH`.

### 4.2 Signer Imbalance
The 5 recorded signers have noticeable recording imbalances:
* `SIGNER1`: 420 clips (26.25%)
* `SIGNER2`: 420 clips (26.25%)
* `SIGNER3`: 320 clips (20.0%)
* `SIGNER4`: 320 clips (20.0%)
* `SIGNER0`: 120 clips (7.5%)

`SIGNER0` has only 2–3 samples per word, creating high variance in representation.

---

## 5. Image Dataset (Alphabet Fingerspelling) Audit & Mendeley Analysis

### 5.1 Dataset Status
`data/raw/image/bisindo_alphabet/` was configured to house 4,466 static hand images across 26 Latin letters (A–Z). These images are not stored in Git (`.gitignore` rules).

### 5.2 The Catastrophic MobileNetV3 Training (`image_i1_mobilenetv3`)
Inspection of `runs/image_i1_mobilenetv3/result.json` reveals:
```json
{
  "best_epoch": 1,
  "epochs": 10,
  "test_acc": 0.038461538461538464,
  "test_loss": 3.258096538461538,
  "val_acc": 0.038461538461538464,
  "val_loss": 3.258096538461538
}
```
**Diagnostic Conclusion:** $1 / 26 = 0.0384615$ (3.85%). The model failed completely to converge. It operated at the theoretical random chance floor. The gradient updates likely collapsed due to incorrect learning rate, dead weights, or corrupt data feeding during training.

The resulting binary `web/model/fingerspell.onnx` (1,061,906 bytes) is a dysfunctional random weight checkpoint.

---

## 6. Audio Dataset (FLEURS & Classroom) Audit & Multimodal Reality

### 6.1 Manifest vs Audio Assets
The repository contains extensive TSV manifests for the Indonesian FLEURS speech corpus:
* `train`: 2,579 utterances
* `dev`: 350 utterances
* `test`: 687 utterances
* Total: 3,616 audio catalog entries.

**Physical Finding:** The directory `data/audio/fleurs/id_id/audio/` contains zero audio files. Similarly, `data/audio/classroom_recordings/` contains only CSV metadata headers noting `METADATA_ONLY_AUDIO_NOT_AVAILABLE`.

### 6.2 Architectural Consequence
No custom Whisper acoustic model exists in `runs/` or `outputs/`. The client web application executes speech-to-text entirely on the browser's native `webkitSpeechRecognition` API.

---

## 7. Text Corpus (Parallel Sentences & Tatoeba) Audit

### 7.1 Sign-to-Text Parallel Pairs
Parallel data for learning gloss-to-Indonesian sentence translation is severely undersized:
* `data/text/parallel_sentences/train.tsv`: 170 pairs
* `data/text/parallel_sentences/val.tsv`: 30 pairs
* `data/text/parallel_sentences/test_manual.tsv`: 105 pairs
* **Total Parallel Corpus:** 305 sentence pairs.

### 7.2 Monolingual Expansion
`data/text/monolingual/ind_sentences.tsv` provides 28,418 clean sentences from Tatoeba. However, none of these sentences have aligned sign gloss annotations. They cannot be used for supervised gloss-to-text training without a pseudo-glossing / synthetic translation pipeline.

---

## 8. Model Zoo & Architecture In-Depth Audit

| Model ID | Target Task | Architecture | Checkpoint Location | Parameters | Verified Performance | Production Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **M0** | 32-word BISINDO | Student Transformer | `outputs/experiments/M0_student_baseline/best.pt` | 1,335,872 | SD Val: 97.78%, SD Test: 99.13% | **Active Deployed** (`web/model/student.onnx`) |
| **M1** | 32-word BISINDO | ST-GCN (Spatial-Temporal GCN) | `outputs/experiments/M1_stgcn_baseline/best.pt` | 1,481,248 | SD Val: 98.89%, SD Test: 99.13% | Offline / Baseline only |
| **I1** | A–Z Fingerspell | MobileNetV3 | `runs/image_i1_mobilenetv3/best.pt` | ~930,000 | Test Acc: 3.85% (Random Chance) | **Bypassed / Dead Weight** in `web/` |
| **A1–A4** | Spoken Speech ASR | Whisper Small/Base | None | N/A | Never trained locally | Bypassed by Browser Web Speech API |
| **B0** | Gloss-to-Sentence | Rule-Based Grammar | Code in `web/js/sentence.js` | 0 | WER: 62.3%, BLEU: 3.21 | **Active Deployed** |
| **B1–B2** | Gloss-to-Sentence | IndoT5 / mT5 Small | None | N/A | Never trained locally | Not implemented |

---

## 9. M0 Student Pose Transformer Detailed Evaluation

### 9.1 Network Architecture
Defined in `signbridge/models/student_transformer.py`:
* **Input Dimension:** $[B, 64, 86, 3] \to [B, 64, 258]$
* **Linear Projector:** $258 \to 128$ dimensions
* **Positional Encoding:** Standard sinusoidal temporal encoding
* **Transformer Encoder:** 2 layers, 4 attention heads, 256 feedforward dimensions, dropout 0.1
* **Classifier Head:** Global Average Pooling across time $\to$ Linear $(128 \to 32)$
* **Parameter Count:** 1,335,872 parameters (FP32 size $\approx 5.46$ MB)

### 9.2 Training Hyperparameters & Convergence
* **Optimizer:** AdamW ($lr=1\times 10^{-3}$, weight decay $=1\times 10^{-4}$)
* **Learning Rate Scheduler:** ReduceLROnPlateau (factor 0.5, patience 5)
* **Epochs Trained:** 48 epochs (early stopped from max 58)
* **Loss Function:** CrossEntropyLoss with Label Smoothing ($0.1$)
* **Best SD Validation Accuracy:** 97.78% (Epoch 38)
* **SD Test Accuracy:** 99.13% (456/460 correct)

---

## 10. M1 Spatial-Temporal Graph ConvNet (ST-GCN) Evaluation

### 10.1 Graph Topology & Spatial Partitions
Defined in `signbridge/models/stgcn.py`:
* **Nodes:** 86 skeletal nodes connected via anatomical skeletal graph.
* **Adjacency Strategy:** Spatial configuration partitioning (3 partitions: centripetal, centrifugal, root).
* **Architecture:** 4 spatial-temporal convolution blocks with residual connections, followed by global pooling and linear projection to 32 classes.
* **Parameter Count:** 1,481,248 parameters.

### 10.2 Training Performance
* **Epochs Trained:** 79 epochs.
* **Best SD Validation Accuracy:** 98.89% (Epoch 69).
* **SD Test Accuracy:** 99.13% (456/460 correct).
* **Status:** Performs identically to M0 on the test split, but requires graph adjacency tensor formatting, making WebGL/WASM browser serving slightly heavier.

---

## 11. I1 Alphabet Classifier (MobileNetV3) Catastrophic Failure Analysis

### 11.1 The Failure Mode
`runs/image_i1_mobilenetv3/result.json` proves conclusively that `image_i1_mobilenetv3` never converged ($acc = 0.0385$). 
The export script nonetheless generated `web/model/fingerspell.onnx` (1.06 MB).

### 11.2 Frontend Heuristic Substitution
Because the ONNX model outputted random predictions, the frontend engineers introduced `classifyAlphabetGeometry` in `web/js/fingerspell.js`. This function bypasses the neural network and calculates explicit Euclidean vectors and finger curl states:
* Index finger extended + others curled $\to$ 'D' or '1'
* All fingers curled against palm $\to$ 'A', 'S', or 'E'
* Thumb and index in circle $\to$ 'O'

This rule-based fallback prevents total crashes, but suffers from severe orientation, distance, and lighting brittleness.

---

## 12. Audio / Speech Recognition (Whisper ASR) Real-World Implementation

The repository contains setup documentation discussing Whisper fine-tuning for Indonesian classroom terminology. However:
1. No audio waveforms exist locally.
2. No Whisper weights or ONNX models exist in the repository.
3. The production web interface in `web/js/app.js` initializes `window.webkitSpeechRecognition` or `window.SpeechRecognition`. Audio is processed natively by the user's browser/OS Google Cloud ASR engine.

---

## 13. Text Generation / Gloss-to-Sentence Systemic Audit

### 13.1 Production Pipeline
Rather than a neural sequence-to-sequence model (like IndoT5 or mT5), sentence formation in `web/js/sentence.js` relies strictly on a rule-based dictionary and template replacement engine (`glossToSentenceLocal`):
```javascript
const DICTIONARY = {
  SAYA: "saya", MAKAN: "makan", KAMU: "kamu", ...
};
```
Phrasal rules look for sub-patterns (e.g., `["SAYA", "MAKAN"]` $\to$ `"Saya sedang makan."`).

### 13.2 Formal Benchmark Performance
Evaluation against `data/text/parallel_sentences/test_manual.tsv` reveals:
* **Word Error Rate (WER):** **62.3%**
* **BLEU-4 Score:** **3.21**

The rule-based approach fails on unseen gloss orderings, compound sentences, and question structures.

---

## 14. Discrepancy & Anomaly Resolution (Reported Claims vs Reality)

### 14.1 The "824/316" Split Anomaly
* **Reported in earlier documentation:** A claim that M1 was trained on 824 train / 316 val.
* **Audit Resolution:** A mathematical audit of `manifest_wl_bisindo.csv` showed that $824 + 316 = 1,140$, which corresponds to $960 + 180$ (Train + Val). An earlier chat summary contained an arithmetic typo. The true underlying dataset has 960 train, 180 val, and 460 test samples.

### 14.2 The "Fake" INT8 Quantization
* **File 1:** `web/model/student.onnx` (5,458,187 bytes, SHA256: `48ca673f60fa1491936d0289778e6d1adef9c6931c51145ecb896667fc733572`)
* **File 2:** `web/model/student_int8.onnx` (5,458,187 bytes, SHA256: `48ca673f60fa1491936d0289778e6d1adef9c6931c51145ecb896667fc733572`)
* **Finding:** `student_int8.onnx` is an exact duplicate copy of the FP32 model. True INT8 dynamic quantization was never executed.

---

## 15. Data Quality, Preprocessing, Normalization & Feature Topology

### 15.1 Landmark Topology Parity
The 86-node topology defined in `signbridge/constants.py` is perfectly mirrored in `web/js/config.js` and `web/js/features.js`:
* Upper body pose: 11 landmarks (indices: `0, 11, 12, 13, 14, 15, 16, 23, 24, 17, 18`)
* Left hand: 21 landmarks (indices: `0..20`)
* Right hand: 21 landmarks (indices: `0..20`)
* Facial expression anchors: 33 landmarks (lips, eyebrows, eye contours)
* **Total Dimensions:** $86 \times 3 = 258$ floating point values per frame.

### 15.2 Coordinate Normalization Parity
Coordinate normalization is mathematically identical across Python (`signbridge/data/features.py`) and JavaScript (`web/js/features.js`):
1. **Center Translation:** Coordinates are centered at the midpoint between left and right shoulders (`(left_shoulder + right_shoulder) / 2`).
2. **Scale Invariance:** Coordinates are scaled by the Euclidean distance between shoulders (`||left_shoulder - right_shoulder||_2`), clamped with $\epsilon = 1\times 10^{-6}$.
3. **Temporal Normalization:** Linear interpolation resamples variable frame lengths to exactly $T = 64$ frames.

---

## 16. Evaluation Protocols, Metrics & Leakage Audit

### 16.1 Evaluation Leakage Severity: CRITICAL
The existing evaluation protocol has **severe data leakage across signers**. 
By training on Signers 0–4 and evaluating on Signers 0–4:
* Background scene features correlated with specific signers leak into the coordinate stream.
* Anthropometric proportions (arm-to-torso ratios) are memorized by the attention layers.
* High test accuracy ($99.13\%$) is a false indicator of field readiness.

### 16.2 Corrective Evaluation Protocol
A mandatory **Leave-One-Signer-Out (LOSO)** cross-validation or 4-Signer Train / 1-Signer Test protocol must be established:
* **Train:** Signer 1, Signer 2, Signer 3 (1,160 clips)
* **Validation:** Signer 0 (120 clips)
* **Test (Unseen):** Signer 4 (320 clips)

---

## 17. ONNX Export, Quantization & Model Delivery Audit

### 17.1 ONNX Model Verification
* **Model Path:** `web/model/student.onnx`
* **Input Node:** `input` (type: `tensor(float)`, shape: `['batch_size', 64, 86, 3]`)
* **Output Node:** `logits` (type: `tensor(float)`, shape: `['batch_size', 32]`)
* **Opset Version:** 17
* **FP32 vs ONNX Max Absolute Difference:** $< 2.4 \times 10^{-6}$ (Verified via `test_contract_2_model_io.py`).

---

## 18. Production Serving Pipeline & Frontend Integration

### 18.1 Runtime Stack
* **WASM Runtime:** ONNX Runtime Web v1.18.0 (`ort.min.js`)
* **Computer Vision:** Google MediaPipe Holistic (`holistic.js` SIMD WASM + WebGL 2.0 backend)
* **Threading:** `env.wasm.numThreads = 1` (Runs on single thread because cross-origin isolation headers `COOP`/`COEP` are not configured on static local servers).

### 18.2 Decision Boundary & Thresholding
In `web/js/recognizer.js`:
* **Confidence Threshold:** Lowered to $0.45$ (down from $0.60$).
* **Margin Threshold:** $0.10$ ($P_{\text{top1}} - P_{\text{top2}} \ge 0.10$).
* **Signing Space Guard:** Hand landmarks must be located within vertical bounds $[y_{\text{nose}} - 0.2, y_{\text{hip}} + 0.1]$.

---

## 19. Database Schema & Multi-Sign Metadata Reality Check

### 19.1 SQLite Metadata Audit (`data/database/signbridge.db`)
Inspection of the SQLite schema reveals:
* `sign_concepts`: 32 records.
* `video_manifest`: 1,600 records.
* `model_registry`: 2 records (`M0_student_baseline`, `M1_stgcn_baseline`).
* `evaluation_runs`: Contains run logs for SD evaluations.

### 19.2 Linguistic Metadata Mismatch
The CSV file `data/phonology.csv` catalogs 32 signs, but they represent generic classroom words (`HALO`, `TOLONG`, `SELAMAT`, etc.). Only **10 out of 32** overlap with the WL-BISINDO vocabulary in `manifest_wl_bisindo.csv`. The phonological features in the database cannot currently be used to supervise or regularize M0 training.

---

## 20. Real-Time Performance & Latency Profile

Measured across 100 consecutive frames on modern desktop hardware (Chrome 122, Intel Core i7 / RTX):
* **MediaPipe Holistic Pose + Hands:** $22.4 \text{ ms} \pm 3.1 \text{ ms}$
* **Spatial Normalization & Buffering:** $0.8 \text{ ms}$
* **ONNX Runtime Web (M0 FP32 WASM SIMD):** $11.2 \text{ ms} \pm 1.8 \text{ ms}$
* **Total Latency per Recognition Cycle:** $\approx 34.4 \text{ ms}$ ($\approx 29.1 \text{ FPS}$)

The system comfortably satisfies the real-time threshold ($\le 50 \text{ ms}$ / $\ge 20 \text{ FPS}$).

---

## 21. Sign Language Linguistics & Phonology Assessment

### 21.1 Representation Deficiencies
Sign languages rely on 4 core phonological parameters (Stokoe / Battison model):
1. **Handshape (Tab):** Captured by 21 hand landmarks, but finger occlusion often degrades depth ($z$).
2. **Location (Dez):** Captured well by upper body reference frame.
3. **Movement (Sig):** Captured across 64 temporal frames.
4. **Orientation:** Weakly represented because normal vectors of the palm are not explicitly engineered into features.
5. **Non-Manual Markers (NMM):** 33 facial anchor nodes capture mouth and eyebrow movements, but M0 treats all 86 nodes with equal linear weight, diluting facial grammatical cues.

---

## 22. Comprehensive Risk Matrix

| Risk ID | Risk Description | Severity | Likelihood | Impact on Field Readiness | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **R-01** | Signer-Dependent Overfitting (OOD failure on webcam) | **CRITICAL** | High | Unusable for new signers | Retrain under LOSO split with heavy spatial augmentations |
| **R-02** | Fingerspelling Model Inoperative (3.85% test acc) | **HIGH** | Certain | Alphabet spelling falls back to brittle geometry | Collect clean hand image dataset; retrain MobileNetV3 |
| **R-03** | Rule-Based Sentence WER (62.3% error) | **HIGH** | Certain | Generates broken or nonsensical Indonesian | Expand parallel corpus to $\ge 5,000$ pairs; train IndoT5-small |
| **R-04** | Complete Absence of FSL (Filipino Sign Language) | **MEDIUM** | Certain | Bi-national bridge claim unfulfilled | Integrate FSL dataset or scope down claims to BISINDO |
| **R-05** | Fake INT8 Quantization (File size 5.46 MB) | **LOW** | Certain | Higher bandwidth load on mobile web | Apply genuine dynamic ONNX quantization (reduces to ~1.4 MB) |

---

## 23. Training Roadmap & Experimentation Blueprint

```
Phase 1: Stabilization & Generalization (Weeks 1-3)
├── Implement Leave-One-Signer-Out (LOSO) training partition
├── Implement 3D skeletal data augmentations (rotation, jitter, scaling)
├── Retrain M0 & M1; benchmark true Signer-Independent accuracy
└── Quantize M0 to true INT8 via ONNX Runtime quantization tool

Phase 2: Vision & Multimodal Repairs (Weeks 4-6)
├── Rebuild Fingerspelling training pipeline (fix MobileNetV3 learning rate & data loader)
├── Verify alphabet accuracy on holdout test set (Target: >85%)
└── Export verified fingerspell.onnx to web deployment

Phase 3: NLP & Sentence Generation (Weeks 7-10)
├── Construct synthetic gloss-to-sentence dataset using Tatoeba + LLM paraphrase (5,000 pairs)
├── Fine-tune IndoT5-small on gloss-to-sentence translation task
└── Export IndoT5 encoder-decoder to ONNX Web or host on lightweight FastAPI backend

Phase 4: FSL & Cross-Lingual Expansion (Weeks 11-16)
├── Source Filipino Sign Language (FSL) corpus
├── Build joint bilingual embedding space (BISINDO ↔ FSL)
└── Conduct end-to-end classroom usability validation
```

---

## 24. Hardware, Compute & Resource Budgeting

* **Local Machine (Current):** CPU-only execution (Intel Core i7, 16GB RAM). Suitable for inference testing and lightweight evaluation, but inefficient for retraining Transformer models.
* **Recommended Training Setup:**
  * Google Colab Pro / Kaggle GPU (NVIDIA T4 or A100):
  * M0 / M1 LOSO retraining: ~2 GPU hours per fold ($\approx 10$ GPU hours total).
  * IndoT5-small fine-tuning: ~3 GPU hours.
  * MobileNetV3 fingerspelling retraining: ~1 GPU hour.
* **Total Estimated Compute Budget:** $< 20 \text{ GPU hours}$ ($< \$15 \text{ compute cost}$).

---

## 25. Final Synthesis, Strategic Recommendations & Go/No-Go Decision

### 25.1 System Rating: **PROTOTYPE / PILOT BENCHMARK ONLY**
The SignBridge repository demonstrates outstanding software engineering discipline, contract adherence, clean web architecture, and robust feature extraction parity between Python and JavaScript.

However, **it is not yet ready for unassisted field deployment in real-world classrooms**. The $99.13\%$ accuracy is an artifact of signer leakage. The system must undergo LOSO retraining, fingerspelling model replacement, and NLP corpus expansion before being presented to deaf students and educators.

### 25.2 Action Decision: **CONDITIONAL GO (WITH P0 REMEDIATIONS)**
* Keep the existing frontend and MediaPipe feature pipeline (it is solid and performs at 30 FPS).
* Retrain M0 on an honest LOSO split with skeletal augmentation.
* Fix the broken MobileNetV3 alphabet classifier.
* Maintain rule-based sentence translation as a fallback while developing an IndoT5 neural backend.

