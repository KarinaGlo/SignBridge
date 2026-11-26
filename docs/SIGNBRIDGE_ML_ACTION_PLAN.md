# SIGNBRIDGE ML ACTION PLAN
**Prioritized Engineering & Research Remediation Roadmap**

**Document Version:** 1.0.0  
**Status:** Approved for Execution  
**Target Branch:** `feature/field-test-readiness`

---

## 1. Overview of Priority Levels

* **P0 — Critical (Blocker):** Flaws causing direct failure in live real-world usage or fundamentally invalidating published accuracy claims. Must be fixed before any field testing.
* **P1 — High Priority (Production Quality):** Deficiencies causing high error rates, unhandled edge cases, or broken feature components.
* **P2 — Medium Priority (Feature Completeness):** Enhancements required to fulfill core product specifications (e.g. true sentence generation, genuine quantization).
* **P3 — Long-Term / Strategic (Ecosystem Expansion):** Cross-lingual expansion (FSL), bilingual embeddings, and classroom pilot integrations.

---

## 2. P0: Critical Actions (Immediate Remediation)

### P0-1: Eliminate Signer-Dependent Data Leakage via LOSO Training
* **Problem Statement:** The current M0/M1 models achieve 99.13% test accuracy because all 5 recorded signers are present in both the training set (960 clips) and the test set (460 clips). The models memorize signer body morphology and camera angles, causing catastrophic false negatives on unseen users.
* **Evidence:** In `data/manifest_wl_bisindo.csv`, `split_sd` divides clips randomly within each signer. Signers 0–4 appear in all partitions.
* **Impact:** Real webcam users fail to trigger signs or receive wildly inaccurate predictions.
* **Recommended Solution:**
  1. Define a strict **Leave-One-Signer-Out (LOSO)** partition in `manifest_wl_bisindo.csv`:
     - `train_loso`: Signer 1, Signer 2, Signer 3 (1,160 clips)
     - `val_loso`: Signer 0 (120 clips)
     - `test_loso`: Signer 4 (320 clips)
  2. Implement spatial data augmentations in `signbridge/data/dataset.py`:
     - Random scaling: $s \sim \mathcal{U}(0.85, 1.15)$
     - Joint coordinate jitter: $\mathcal{N}(0, 0.015)$
     - Temporal speed perturbation: resampling between $0.8\times$ and $1.2\times$ before uniform resampling to $T=64$.
  3. Retrain M0 and benchmark the true Signer-Independent accuracy.
* **Involved Files:**
  - `data/manifest_wl_bisindo.csv`
  - `signbridge/data/dataset.py`
  - `train.py`
* **Success Criteria:** True Signer-Independent test accuracy $\ge 82.0\%$ on completely unseen Signer 4.

---

### P0-2: Replace Broken Alphabet Classifier (Fix MobileNetV3 Training Collapse)
* **Problem Statement:** The fingerspelling neural model `image_i1_mobilenetv3` has a test accuracy of **3.85%** (random chance $1/26$). The deployed `web/model/fingerspell.onnx` is dead weight, forcing reliance on a brittle heuristic.
* **Evidence:** `runs/image_i1_mobilenetv3/result.json` shows test loss 3.258 and test accuracy 0.03846 across all epochs.
* **Impact:** Fingerspelling recognition in web interface is erratic and fails across varying angles.
* **Recommended Solution:**
  1. Re-download or verify Mendeley BISINDO Alphabet images in `data/raw/image/bisindo_alphabet/`.
  2. Audit `scripts/train_image_classifier.py`:
     - Fix learning rate ($1\times 10^{-4}$ with AdamW instead of excessive or decaying LR).
     - Fix class indexing to match `A` through `Z` (26 classes).
     - Add ImageNet normalization ($mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]$).
  3. Retrain MobileNetV3-Small for 20 epochs.
  4. Export to `web/model/fingerspell.onnx` and verify parity.
* **Involved Files:**
  - `scripts/train_image_classifier.py`
  - `web/model/fingerspell.onnx`
  - `web/js/fingerspell.js`
* **Success Criteria:** Test accuracy on holdout alphabet set $\ge 88.0\%$; ONNX model loads and runs in under 15 ms in browser.

---

## 3. P1: High Priority (Production Quality)

### P1-1: True Dynamic INT8 ONNX Quantization
* **Problem Statement:** `web/model/student_int8.onnx` is an exact byte-for-byte duplicate of `student.onnx` (5,458,187 bytes). Real quantization was never executed.
* **Evidence:** SHA256 hashes for both files match identically (`48ca673f60fa1491936d0289778e6d1adef9c6931c51145ecb896667fc733572`).
* **Impact:** Excessive initial download size (5.46 MB instead of ~1.4 MB) degrading mobile / low-bandwidth classroom loading.
* **Recommended Solution:**
  1. Run `onnxruntime.quantization.quantize_dynamic` targeting `weight_type=QuantType.QInt8` on `student.onnx`.
  2. Verify parity using `tests/test_contract_2_model_io.py` ensuring maximum degradation in accuracy $\le 0.5\%$.
  3. Replace `web/model/student_int8.onnx` with the genuine ~1.4 MB quantized artifact.
* **Involved Files:**
  - `signbridge/export/onnx_exporter.py`
  - `web/model/student_int8.onnx`
* **Success Criteria:** File size $\le 1.6 \text{ MB}$; inference latency reduced by $\ge 25\%$ on WASM.

---

### P1-2: Realign Phonology Database with WL-BISINDO Vocabulary
* **Problem Statement:** `data/phonology.csv` catalogs 32 classroom signs, but only 10 overlap with the 32 WL-BISINDO vocabulary words currently recognized by M0.
* **Evidence:** Cross-referencing `data/phonology.csv` with `web/model/labels.json` reveals 22 missing signs (e.g., `ADA`, `BELAJAR`, `BUKU`, `GURU` are missing from phonology).
* **Impact:** Linguistic regularizers and multi-task learning heads cannot be leveraged to guide training.
* **Recommended Solution:**
  1. Complete the phonological annotation for all 32 WL-BISINDO signs in `data/phonology.csv` (handshape, active hands, location, movement type, contact).
  2. Update `data/database/signbridge.db` schema and tables.
* **Involved Files:**
  - `data/phonology.csv`
  - `signbridge/data/phonology.py`
  - `data/database/signbridge.db`
* **Success Criteria:** 32/32 WL-BISINDO words have complete, linguistically validated phonological feature vectors.

---

## 4. P2: Medium Priority (Feature Completeness)

### P2-1: Synthetic Expansion of Parallel Gloss-to-Sentence Corpus
* **Problem Statement:** The parallel translation corpus consists of only 305 sentence pairs (170 train, 30 val, 105 test), forcing the frontend to use a naive rule-based dictionary with 62.3% WER.
* **Evidence:** `data/text/parallel_sentences/*.tsv` contains only 305 total rows.
* **Impact:** Translation output is robotic, gramatically fragmented, and fails on complex expressions.
* **Recommended Solution:**
  1. Leverage `data/text/monolingual/ind_sentences.tsv` (28,418 Tatoeba sentences).
  2. Use a deterministic rule parser and LLM pseudo-glosser to generate 5,000 synthetic `(gloss_sequence, indonesian_sentence)` pairs.
  3. Fine-tune a lightweight seq2seq model (e.g. `IndoT5-small` or 2-layer GRU).
* **Involved Files:**
  - `scripts/expand_parallel_corpus.py`
  - `data/text/parallel_sentences/`
  - `signbridge/nlp/gloss_translator.py`
* **Success Criteria:** Parallel corpus $\ge 5,000$ pairs; validation BLEU-4 score $\ge 35.0$ (up from 3.21).

---

### P2-2: Full Parity Evaluation for ST-GCN (M1) on Web
* **Problem Statement:** M1 (ST-GCN) is currently confined to PyTorch offline evaluation and lacks an export pipeline for ONNX Web.
* **Evidence:** `web/model/` contains only `student.onnx` (M0).
* **Impact:** Inability to compare graph convolution performance against transformer attention in real-world browser environments.
* **Recommended Solution:**
  1. Implement ONNX export for `signbridge/models/stgcn.py` with static or dynamic adjacency tensors.
  2. Validate numerical parity with `test_contract_2_model_io.py`.
  3. Add toggle switch in `web/index.html` to allow A/B testing between M0 and M1.
* **Involved Files:**
  - `signbridge/models/stgcn.py`
  - `signbridge/export/onnx_exporter.py`
  - `web/js/recognizer.js`
* **Success Criteria:** M1 successfully exports to `web/model/stgcn.onnx` and executes in browser WASM runtime in $\le 20 \text{ ms}$.

---

## 5. P3: Long-Term & Strategic (Ecosystem Expansion)

### P3-1: Filipino Sign Language (FSL) Integration
* **Problem Statement:** The repository name specifies "ID–PH Multimodal Classroom Bridge", but zero FSL dataset, labels, or models exist.
* **Evidence:** No FSL manifest or video directory exists in the codebase.
* **Impact:** Core thesis requirement for bi-national classroom bridge remains unfulfilled.
* **Recommended Solution:**
  1. Source public FSL datasets (e.g. FSL-105 or Philippine Deaf community recordings).
  2. Align FSL vocabulary with common educational concepts (30–50 core classroom signs).
  3. Train a bilingual dual-head model or dual-branch encoder.
* **Success Criteria:** Balanced bilingual test set demonstrating $\ge 80\%$ accuracy on both BISINDO and FSL vocabulary sets.

