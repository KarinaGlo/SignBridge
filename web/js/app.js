/**
 * web/js/app.js
 * Pengendali utama antarmuka web SignBridge ASEAN (BISINDO <-> FSL Filipina + 26 Abjad A-Z).
 * Sinkron 100% dengan Database:
 *   - data/bridge/concepts.csv (32 Konsep Ruang Kelas BISINDO <-> FSL)
 *   - data/phonology.csv (Parameter Fonologi Bentuk Tangan, Lokasi, Gerakan, 1/2 Tangan)
 *   - web/model/fingerspell.json (26 Abjad Ejaan Jari A-Z)
 */

import {
  APP_CONFIG,
  BISINDO_GLOSSES,
  FINGERSPELL_LABELS,
  FINGERSPELL_DB,
  CLASSROOM_CONCEPTS,
  PHONOLOGY_DB
} from "./config.js";
import { buildNaturalSentence, glossToSentenceLocal, sentenceToConceptGlosses } from "./sentence.js";
import { speakText, unlockSpeechAudio, SpeechListener } from "./speech.js";
import { VisionManager, drawSkeleton86, generateReferenceSignKeypoints } from "./vision.js";
import { SignRecognizer, SIGN_STATE } from "./recognizer.js";
import { FingerspellRecognizer } from "./fingerspell.js";
import { RoomManager } from "./room.js";
import { MultimodalRecorder } from "./recorder.js";

class SignBridgeApp {
  constructor() {
    this.bridgeDirection = "ID-PH";
    this.recognitionMode = "hybrid"; // "hybrid" | "video" | "fingerspell"
    this.autoSpeak = true;
    this.accumulatedGlosses = [];
    this.spelledLetters = [];
    this.currentSentence = "";
    this.practiceTarget = "SAYA";
    this.practiceStreak = 0;

    this.recognizer = new SignRecognizer({
      onStateChange: (info) => this.updateStateBadge(info),
      onPrediction: (pred) => this.handleSignPrediction(pred)
    });
    this.fingerspeller = new FingerspellRecognizer({
      onPrediction: (pred) => this.handleAlphabetPrediction(pred)
    });
    this.recorder = new MultimodalRecorder();
    this.room = new RoomManager({
      onMessage: (msg) => this.handleRoomMessage(msg),
      onStatusChange: (st) => this.updateRoomBadge(st)
    });
    this.speechListener = new SpeechListener({
      onResult: (res) => this.handleSpeechResult(res),
      onStateChange: (st) => this.updateMicButton(st)
    });

    this.vision = null;
    this.refAnimTimer = null;
  }

  async init() {
    this.bindTabs();
    this.bindHeaderControls();
    this.bindClassroomControls();
    this.bindBridgeControls();
    this.bindPracticeControls();
    this.bindRecorderControls();
    this.renderConceptBoard("Semua");

    const recStatus = await this.recognizer.init();
    await this.fingerspeller.init();
    const engineEl = document.getElementById("engine-status");
    if (engineEl) {
      engineEl.textContent =
        recStatus.engine === "onnx-web"
          ? "Database 32 BISINDO/FSL + 26 Abjad A-Z (ONNX Aktif)"
          : "Database 32 BISINDO/FSL + 26 Abjad A-Z (Hibrida Aktif)";
    }

    this.playReferenceSign("HALO", "l3-canvas");
    this.playReferenceSign("HALO", "hearing-sign-canvas");
  }

  bindTabs() {
    const tabBtns = document.querySelectorAll("[data-tab-target]");
    const panels = document.querySelectorAll(".tab-panel");
    tabBtns.forEach((btn) => {
      btn.addEventListener("click", () => {
        const target = btn.getAttribute("data-tab-target");
        tabBtns.forEach((b) => b.classList.toggle("active", b === btn));
        panels.forEach((p) => p.classList.toggle("active", p.id === target));
      });
    });
  }

  bindHeaderControls() {
    const dirSelect = document.getElementById("bridge-direction");
    if (dirSelect) {
      dirSelect.addEventListener("change", () => {
        this.bridgeDirection = dirSelect.value;
        const isFilTarget = this.bridgeDirection === "ID-PH";
        this.speechListener.setLanguage(isFilTarget ? "id-ID" : "fil-PH");
        this.refreshNaturalSentence();
      });
    }

    const joinBtn = document.getElementById("btn-join-room");
    const roomInput = document.getElementById("room-code-input");
    if (joinBtn && roomInput) {
      joinBtn.addEventListener("click", async () => {
        const code = roomInput.value.trim() || RoomManager.generateCode();
        roomInput.value = code;
        await this.room.joinRoom(code);
      });
    }
  }

  bindClassroomControls() {
    const videoEl = document.getElementById("camera-video");
    const canvasEl = document.getElementById("camera-canvas");
    this.vision = new VisionManager({
      videoEl,
      canvasEl,
      onFrameKeypoints: ({ kp86, rightHand21, leftHand21, hasVisibleHand }) => {
        if (this.recognitionMode === "fingerspell") {
          const activeHand = rightHand21 || leftHand21;
          this.fingerspeller.pushHandFrame(activeHand);
        } else if (this.recognitionMode === "video") {
          this.recognizer.pushFrame(kp86, { hasVisibleHand });
        } else {
          // Mode Gabungan (Hybrid):
          // - Jika 2 tangan terlihat, atau tangan di kepala/mulut/dada, atau sedang bergerak -> 32 Kata BISINDO/FSL
          // - Jika 1 tangan ditahan stabil di ruang netral samping -> dapat mengenali Abjad A-Z juga
          this.recognizer.pushFrame(kp86, { hasVisibleHand });
        }
      }
    });

    const camBtn = document.getElementById("btn-toggle-camera");
    if (camBtn) {
      camBtn.addEventListener("click", async () => {
        unlockSpeechAudio();
        if (!this.vision.running) {
          const ok = await this.vision.startCamera();
          camBtn.textContent = ok ? "Matikan Kamera" : "Simulasi Kamera (Tanpa Webcam)";
          if (ok) {
            speakText("Kamera siap. Angkat tangan untuk mulai berisyarat.", "id-ID");
          } else {
            this.simulateSignInput("SAYA");
          }
        } else {
          this.vision.stopCamera();
          camBtn.textContent = "Aktifkan Kamera";
        }
      });
    }

    const autoSpeakCheck = document.getElementById("chk-auto-speak");
    if (autoSpeakCheck) {
      autoSpeakCheck.checked = this.autoSpeak;
      autoSpeakCheck.addEventListener("change", () => {
        this.autoSpeak = autoSpeakCheck.checked;
      });
    }

    const modeSelect = document.getElementById("recognition-mode");
    if (modeSelect) {
      modeSelect.value = this.recognitionMode;
      modeSelect.addEventListener("change", () => {
        this.recognitionMode = modeSelect.value;
        const guideEl = document.getElementById("active-sign-guide");
        if (guideEl) {
          if (this.recognitionMode === "fingerspell") {
            guideEl.innerHTML = `<strong>Mode Abjad A-Z Aktif:</strong> Tunjukkan 1 tangan dengan bentuk huruf A sampai Z di depan kamera (tahan ~0,4 detik).`;
          } else {
            guideEl.innerHTML = `<strong>Mode 32 Kata BISINDO &harr; FSL Aktif:</strong> Angkat tangan ke depan kamera untuk memperagakan kata isyarat sesuai database.`;
          }
        }
      });
    }

    // Render seluruh 32 Kata Isyarat Database (BISINDO <-> FSL)
    const quickContainer = document.getElementById("quick-gloss-buttons");
    if (quickContainer) {
      quickContainer.innerHTML = "";
      CLASSROOM_CONCEPTS.forEach((c) => {
        const chip = document.createElement("button");
        chip.type = "button";
        chip.className = "chip-btn";
        chip.title = `${c.id_text} / ${c.fil_text} — ${c.guide}`;
        chip.textContent = `${c.bisindo} (${c.fsl})`;
        chip.addEventListener("click", () => {
          unlockSpeechAudio();
          this.simulateSignInput(c.bisindo);
        });
        quickContainer.appendChild(chip);
      });
    }

    // Render seluruh 26 Abjad Ejaan Jari (A-Z) Database
    const alphaContainer = document.getElementById("quick-alphabet-buttons");
    if (alphaContainer) {
      alphaContainer.innerHTML = "";
      FINGERSPELL_DB.forEach((item) => {
        const btn = document.createElement("button");
        btn.type = "button";
        btn.className = "chip-btn";
        btn.style.minWidth = "34px";
        btn.style.fontWeight = "700";
        btn.title = `Huruf ${item.letter}: ${item.guide}`;
        btn.textContent = item.letter;
        btn.addEventListener("click", () => {
          unlockSpeechAudio();
          this.simulateAlphabetInput(item.letter);
        });
        alphaContainer.appendChild(btn);
      });
    }

    const commitSpelledBtn = document.getElementById("btn-commit-spelled");
    if (commitSpelledBtn) {
      commitSpelledBtn.addEventListener("click", () => {
        unlockSpeechAudio();
        if (this.spelledLetters.length === 0) return;
        const word = this.spelledLetters.join("");
        this.spelledLetters = [];
        this.renderSpelledWord();
        this.appendGloss(word, 0.95);
        if (this.autoSpeak) {
          this.speakCurrentSentence(word);
        }
      });
    }

    const backSpelledBtn = document.getElementById("btn-back-spelled");
    if (backSpelledBtn) {
      backSpelledBtn.addEventListener("click", () => {
        this.spelledLetters.pop();
        this.renderSpelledWord();
      });
    }

    const clearBtn = document.getElementById("btn-clear-glosses");
    if (clearBtn) {
      clearBtn.addEventListener("click", () => {
        this.accumulatedGlosses = [];
        this.spelledLetters = [];
        this.currentSentence = "";
        this.renderGlossSequence();
        this.renderSpelledWord();
        this.updateStateBadge({ state: SIGN_STATE.IDLE });
      });
    }

    const speakBtn = document.getElementById("btn-speak-sentence");
    if (speakBtn) {
      speakBtn.addEventListener("click", () => {
        unlockSpeechAudio();
        this.speakCurrentSentence();
      });
    }

    const micBtn = document.getElementById("btn-mic-listen");
    if (micBtn) {
      micBtn.addEventListener("click", () => {
        if (this.speechListener.isListening) {
          this.speechListener.stop();
        } else {
          this.speechListener.start();
        }
      });
    }

    const sendHearingBtn = document.getElementById("btn-send-hearing");
    const hearingInput = document.getElementById("hearing-text-input");
    if (sendHearingBtn && hearingInput) {
      sendHearingBtn.addEventListener("click", () => {
        const txt = hearingInput.value.trim();
        if (txt) {
          this.handleSpeechResult({ text: txt, isFinal: true, engine: "Manual" });
        }
      });
    }
  }

  renderSpelledWord() {
    const el = document.getElementById("spelled-word-output");
    if (!el) return;
    el.textContent = this.spelledLetters.length > 0 ? this.spelledLetters.join("") : "-";
  }

  speakCurrentSentence(overrideText = "") {
    const srcLang = this.bridgeDirection === "ID-PH" ? "id" : "fil";
    const text = overrideText || this.currentSentence || glossToSentenceLocal(this.accumulatedGlosses, srcLang);
    if (!text) return;
    this.recognizer.setState(SIGN_STATE.SPEAKING);
    const lang = this.bridgeDirection === "ID-PH" ? "id-ID" : "fil-PH";
    speakText(text, lang);
    if (this.vision) {
      this.vision.setHudText(`SUARA (${lang}): "${text}"`);
    }
    this.room.broadcast({
      type: "deaf_to_hearing",
      glosses: this.accumulatedGlosses,
      sentence: text,
      direction: this.bridgeDirection
    });
  }

  async simulateSignInput(glossName) {
    const seq = generateReferenceSignKeypoints(glossName, 40);
    const canvasEl = document.getElementById("camera-canvas");
    if (canvasEl) {
      const ctx = canvasEl.getContext("2d");
      drawSkeleton86(ctx, seq[20], canvasEl.width, canvasEl.height, {
        hudText: `PERAGA DATABASE 86 NODE: [${glossName}]`
      });
    }
    await this.recognizer.classifySequence(seq, glossName);
  }

  simulateAlphabetInput(letter) {
    const cleanLetter = String(letter).toUpperCase();
    const seq = generateReferenceSignKeypoints(cleanLetter, 32);
    const canvasEl = document.getElementById("camera-canvas");
    if (canvasEl) {
      const ctx = canvasEl.getContext("2d");
      drawSkeleton86(ctx, seq[16], canvasEl.width, canvasEl.height, {
        hudText: `PERAGA ABJAD EJAAN JARI: Huruf [${cleanLetter}]`
      });
    }
    const info = FINGERSPELL_DB.find((item) => item.letter === cleanLetter) || FINGERSPELL_DB[0];
    this.handleAlphabetPrediction({
      letter: cleanLetter,
      confidence: 0.96,
      guide: info.guide,
      example_id: info.example_id,
      example_fil: info.example_fil,
      top3: [
        { letter: cleanLetter, confidence: 0.96 },
        { letter: "A", confidence: 0.03 },
        { letter: "B", confidence: 0.01 }
      ]
    });
  }

  handleAlphabetPrediction(pred) {
    if (!pred || !pred.letter) return;
    const letter = String(pred.letter).toUpperCase();
    this.spelledLetters.push(letter);
    this.renderSpelledWord();

    const top3El = document.getElementById("top3-predictions");
    if (top3El && Array.isArray(pred.top3)) {
      top3El.innerHTML = pred.top3
        .map(
          (item) =>
            `<span class="pred-pill">Huruf ${item.letter} <strong>${Math.round(item.confidence * 100)}%</strong></span>`
        )
        .join("");
    }

    const guideEl = document.getElementById("active-sign-guide");
    if (guideEl) {
      guideEl.innerHTML =
        `<strong>Abjad Ejaan Jari [${letter}]:</strong> ${pred.guide || ""} ` +
        `<span class="muted">(Contoh ID: ${pred.example_id || "-"} | PH: ${pred.example_fil || "-"})</span>`;
    }

    if (this.vision) {
      this.vision.setHudText(`ABJAD TERDETEKSI: Huruf [${letter}] -> Ejaan: ${this.spelledLetters.join("")}`);
    }

    if (this.autoSpeak) {
      const lang = this.bridgeDirection === "ID-PH" ? "id-ID" : "fil-PH";
      speakText(`Huruf ${letter}`, lang);
    }

    if (letter === String(this.practiceTarget).toUpperCase()) {
      this.practiceStreak += 1;
      const streakEl = document.getElementById("practice-streak");
      const statusEl = document.getElementById("practice-feedback");
      if (streakEl) streakEl.textContent = String(this.practiceStreak);
      if (statusEl) {
        statusEl.textContent = `Tepat! Abjad Ejaan Jari [${letter}] berhasil diperagakan (${Math.round((pred.confidence || 0.95) * 100)}%).`;
      }
    }
  }

  async handleSignPrediction(pred) {
    const top3El = document.getElementById("top3-predictions");
    if (top3El && pred && Array.isArray(pred.top3)) {
      top3El.innerHTML = pred.top3
        .map((item) => {
          const c = CLASSROOM_CONCEPTS.find((x) => x.bisindo === item.gloss);
          const fslTag = c ? ` / ${c.fsl}` : "";
          return `<span class="pred-pill">${item.gloss}${fslTag} <strong>${Math.round(item.confidence * 100)}%</strong></span>`;
        })
        .join("");
    }

    if (pred && pred.gloss) {
      const concept = CLASSROOM_CONCEPTS.find((c) => c.bisindo === pred.gloss);
      const guideEl = document.getElementById("active-sign-guide");
      if (guideEl && concept) {
        guideEl.innerHTML =
          `<strong>BISINDO: [${concept.bisindo}] ("${concept.id_text}") &harr; FSL Filipina: [${concept.fsl}] ("${concept.fil_text}")</strong><br/>` +
          `<span>Panduan Gerakan Database: ${concept.guide}</span>`;
      }

      await this.appendGloss(pred.gloss, pred.confidence || 0.90);

      // Suarakan kata/kalimat sesuai arah bahasa (ID atau PH) tepat 1 kali untuk gerakan ini!
      if (this.autoSpeak) {
        const isID = this.bridgeDirection === "ID-PH";
        const wordToSpeak = concept ? (isID ? concept.id_text : concept.fil_text) : pred.gloss;
        const textToSpeak =
          this.accumulatedGlosses.length <= 3 ? this.currentSentence : wordToSpeak;
        this.speakCurrentSentence(textToSpeak);
      }
    }
  }

  async appendGloss(gloss, confidence = 0.9) {
    const cleanGloss = String(gloss).toUpperCase();
    if (
      this.accumulatedGlosses.length === 0 ||
      this.accumulatedGlosses[this.accumulatedGlosses.length - 1] !== cleanGloss
    ) {
      this.accumulatedGlosses.push(cleanGloss);
      if (this.vision && this.vision.running && this.accumulatedGlosses.length > 5) {
        this.accumulatedGlosses = this.accumulatedGlosses.slice(-5);
      }
    }
    this.renderGlossSequence();
    await this.refreshNaturalSentence();

    if (cleanGloss === String(this.practiceTarget).toUpperCase()) {
      this.practiceStreak += 1;
      const streakEl = document.getElementById("practice-streak");
      const statusEl = document.getElementById("practice-feedback");
      if (streakEl) streakEl.textContent = String(this.practiceStreak);
      if (statusEl) {
        statusEl.textContent = `Tepat! Isyarat ${cleanGloss} dikenali (${Math.round(confidence * 100)}%).`;
      }
    }
  }

  renderGlossSequence() {
    const container = document.getElementById("gloss-sequence-chips");
    if (!container) return;
    if (this.accumulatedGlosses.length === 0) {
      container.innerHTML = `<span class="muted">Belum ada isyarat. Angkat tangan di depan kamera atau klik tombol kata/abjad di atas.</span>`;
      const sentEl = document.getElementById("natural-sentence-output");
      if (sentEl) sentEl.textContent = "Menunggu deret isyarat...";
      const bridgeEl = document.getElementById("classroom-bridge-output");
      if (bridgeEl) bridgeEl.textContent = "";
      return;
    }
    container.innerHTML = this.accumulatedGlosses
      .map((g) => {
        const c = CLASSROOM_CONCEPTS.find((item) => item.bisindo === g);
        return c ? `<span class="gloss-chip">[${c.bisindo} / ${c.fsl}]</span>` : `<span class="gloss-chip">[${g}]</span>`;
      })
      .join(" ");
  }

  async refreshNaturalSentence() {
    const sentEl = document.getElementById("natural-sentence-output");
    const bridgeEl = document.getElementById("classroom-bridge-output");
    if (!sentEl || this.accumulatedGlosses.length === 0) return;

    const srcLang = this.bridgeDirection === "ID-PH" ? "id" : "fil";
    const tgtLang = this.bridgeDirection === "ID-PH" ? "fil" : "id";

    const built = await buildNaturalSentence(this.accumulatedGlosses, {
      apiBaseUrl: APP_CONFIG.apiBaseUrl,
      lang: srcLang
    });
    this.currentSentence = built.text;
    sentEl.textContent = built.text;

    if (bridgeEl) {
      const translated = glossToSentenceLocal(this.accumulatedGlosses, tgtLang);
      const fslSeq = this.accumulatedGlosses
        .map((g) => CLASSROOM_CONCEPTS.find((c) => c.bisindo === g)?.fsl || g)
        .join(" ");
      bridgeEl.textContent =
        tgtLang === "fil"
          ? `FSL Filipina [${fslSeq}]: "${translated}"`
          : `BISINDO Indonesia [${this.accumulatedGlosses.join(" ")}]: "${translated}"`;
    }
  }

  handleSpeechResult({ text, isFinal }) {
    const capEl = document.getElementById("giant-caption");
    if (capEl && text) {
      capEl.textContent = text;
    }
    if (isFinal && text) {
      const concepts = sentenceToConceptGlosses(text);
      const tokenContainer = document.getElementById("hearing-gloss-tokens");
      if (tokenContainer) {
        if (concepts.length === 0) {
          tokenContainer.innerHTML = `<span class="muted">Teks ditampilkan penuh pada takarir kontras tinggi di atas.</span>`;
        } else {
          tokenContainer.innerHTML = concepts
            .map(
              (c) =>
                `<button type="button" class="gloss-chip" data-play-gloss="${c.bisindo}">[${c.bisindo} / ${c.fsl}]</button>`
            )
            .join(" ");
          tokenContainer.querySelectorAll("[data-play-gloss]").forEach((btn) => {
            btn.addEventListener("click", () => {
              this.playReferenceSign(btn.getAttribute("data-play-gloss"), "hearing-sign-canvas");
            });
          });
          this.playReferenceSign(concepts[0].bisindo, "hearing-sign-canvas");
        }
      }
      this.room.broadcast({
        type: "hearing_to_deaf",
        text,
        concepts: concepts.map((c) => c.bisindo)
      });
    }
  }

  bindBridgeControls() {
    const translateBtn = document.getElementById("btn-run-bridge");
    const bridgeInput = document.getElementById("bridge-input-text");
    if (translateBtn && bridgeInput) {
      translateBtn.addEventListener("click", () => this.runThreeLayerBridge(bridgeInput.value));
    }

    const filterBtns = document.querySelectorAll("[data-concept-filter]");
    filterBtns.forEach((btn) => {
      btn.addEventListener("click", () => {
        filterBtns.forEach((b) => b.classList.toggle("active", b === btn));
        this.renderConceptBoard(btn.getAttribute("data-concept-filter"));
      });
    });
  }

  async runThreeLayerBridge(rawText) {
    const query = String(rawText || "").trim();
    if (!query) return;

    const src = this.bridgeDirection === "ID-PH" ? "id" : "fil";
    const tgt = this.bridgeDirection === "ID-PH" ? "fil" : "id";

    const matchedConcepts = sentenceToConceptGlosses(query);
    const l1El = document.getElementById("bridge-l1-output");
    if (l1El) {
      if (matchedConcepts.length > 0) {
        l1El.innerHTML = matchedConcepts
          .map(
            (c) =>
              `<div class="concept-match"><strong>${c.id}</strong>: BISINDO <code>${c.bisindo}</code> (${c.id_text}) &leftrightarrow; FSL <code>${c.fsl}</code> (${c.fil_text})</div>`
          )
          .join("");
      } else {
        l1El.textContent = "Tidak ada kecocokan leksikon langsung pada L1; diteruskan ke L2 Neural MT.";
      }
    }

    const l2El = document.getElementById("bridge-l2-output");
    const badgeEl = document.getElementById("bridge-layer-badge");
    let translatedText = "";
    let layerUsed = "L1-Fallback";

    try {
      const resp = await fetch(`${APP_CONFIG.apiBaseUrl}/translate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: query, src, tgt })
      });
      if (resp.ok) {
        const data = await resp.json();
        translatedText = data.translation || "";
        layerUsed = data.layer_used || "L2-Neural";
      }
    } catch (_e) {}

    if (!translatedText) {
      if (matchedConcepts.length > 0) {
        const glosses = matchedConcepts.map((c) => c.bisindo);
        translatedText = glossToSentenceLocal(glosses, tgt);
        layerUsed = "L1-Concept-Offline";
      } else {
        translatedText = query;
        layerUsed = "L1-Fallback";
      }
    }

    if (l2El) l2El.textContent = translatedText;
    if (badgeEl) badgeEl.textContent = layerUsed;

    speakText(translatedText, tgt === "fil" ? "fil-PH" : "id-ID");

    const targetGloss = matchedConcepts.length > 0 ? matchedConcepts[0].bisindo : "HALO";
    this.playReferenceSign(targetGloss, "l3-canvas");
  }

  renderConceptBoard(categoryFilter = "Semua") {
    const grid = document.getElementById("concept-board-grid");
    if (!grid) return;

    if (categoryFilter === "Abjad") {
      grid.innerHTML = FINGERSPELL_DB.map(
        (item, idx) => `
        <article class="concept-card" data-concept-gloss="${item.letter}">
          <div class="concept-card-header">
            <span class="concept-id">A${String(idx + 1).padStart(2, "0")} · Ejaan Jari</span>
            <span class="concept-gloss">Huruf ${item.letter}</span>
          </div>
          <div class="concept-langs">
            <div><span class="flag">ID</span> Contoh: <strong>${item.example_id}</strong></div>
            <div><span class="flag">PH</span> Contoh: <strong>${item.example_fil}</strong></div>
            <div class="muted" style="font-size:0.8rem; margin-top:0.25rem;">${item.guide}</div>
          </div>
          <div class="concept-actions">
            <button type="button" class="btn-sm" data-speak-id="Huruf ${item.letter}, ${item.example_id}">Suara ID</button>
            <button type="button" class="btn-sm" data-speak-fil="${item.letter}, ${item.example_fil}">Suara PH</button>
            <button type="button" class="btn-sm btn-accent" data-preview-sign="${item.letter}">Peraga L3</button>
          </div>
        </article>`
      ).join("");
    } else {
      const items =
        categoryFilter === "Semua"
          ? CLASSROOM_CONCEPTS
          : CLASSROOM_CONCEPTS.filter((c) => c.category === categoryFilter);

      grid.innerHTML = items
        .map(
          (c) => `
          <article class="concept-card" data-concept-gloss="${c.bisindo}">
            <div class="concept-card-header">
              <span class="concept-id">${c.id} · ${c.category}</span>
              <span class="concept-gloss">${c.bisindo} / ${c.fsl}</span>
            </div>
            <div class="concept-langs">
              <div><span class="flag">ID</span> <strong>${c.id_text}</strong></div>
              <div><span class="flag">PH</span> <strong>${c.fil_text}</strong></div>
              <div class="muted"><span class="flag">EN</span> ${c.en_text}</div>
              <div class="muted" style="font-size:0.78rem; margin-top:0.25rem;"><strong>Gerakan:</strong> ${c.guide}</div>
            </div>
            <div class="concept-actions">
              <button type="button" class="btn-sm" data-speak-id="${c.id_text}">Suara ID</button>
              <button type="button" class="btn-sm" data-speak-fil="${c.fil_text}">Suara PH</button>
              <button type="button" class="btn-sm btn-accent" data-preview-sign="${c.bisindo}">Peraga L3</button>
            </div>
          </article>`
        )
        .join("");
    }

    grid.querySelectorAll("[data-speak-id]").forEach((btn) => {
      btn.addEventListener("click", () => speakText(btn.getAttribute("data-speak-id"), "id-ID"));
    });
    grid.querySelectorAll("[data-speak-fil]").forEach((btn) => {
      btn.addEventListener("click", () => speakText(btn.getAttribute("data-speak-fil"), "fil-PH"));
    });
    grid.querySelectorAll("[data-preview-sign]").forEach((btn) => {
      btn.addEventListener("click", () => {
        const g = btn.getAttribute("data-preview-sign");
        this.playReferenceSign(g, "l3-canvas");
      });
    });
  }

  bindPracticeControls() {
    const selectEl = document.getElementById("practice-target-select");
    if (selectEl) {
      const glossOpts = CLASSROOM_CONCEPTS.map(
        (c) => `<option value="${c.bisindo}">Kata: ${c.bisindo} / ${c.fsl} (${c.id_text} - ${c.fil_text})</option>`
      ).join("");
      const alphaOpts = FINGERSPELL_DB.map(
        (a) => `<option value="${a.letter}">Abjad: Huruf ${a.letter} (${a.guide})</option>`
      ).join("");
      selectEl.innerHTML = `<optgroup label="32 Kata BISINDO <-> FSL">${glossOpts}</optgroup><optgroup label="26 Abjad Ejaan Jari (A-Z)">${alphaOpts}</optgroup>`;
      selectEl.value = this.practiceTarget;
      selectEl.addEventListener("change", () => {
        this.practiceTarget = selectEl.value;
        this.playReferenceSign(this.practiceTarget, "practice-ref-canvas");
        this.updatePracticeInstruction();
      });
    }

    const randomBtn = document.getElementById("btn-practice-random");
    if (randomBtn && selectEl) {
      randomBtn.addEventListener("click", () => {
        const allTargets = [...BISINDO_GLOSSES, ...FINGERSPELL_LABELS];
        const idx = Math.floor(Math.random() * allTargets.length);
        this.practiceTarget = allTargets[idx];
        selectEl.value = this.practiceTarget;
        this.playReferenceSign(this.practiceTarget, "practice-ref-canvas");
        this.updatePracticeInstruction();
      });
    }

    const testBtn = document.getElementById("btn-practice-try");
    if (testBtn) {
      testBtn.addEventListener("click", () => {
        unlockSpeechAudio();
        if (this.practiceTarget.length === 1) {
          this.simulateAlphabetInput(this.practiceTarget);
        } else {
          this.simulateSignInput(this.practiceTarget);
        }
      });
    }
    this.playReferenceSign(this.practiceTarget, "practice-ref-canvas");
    this.updatePracticeInstruction();
  }

  updatePracticeInstruction() {
    const statusEl = document.getElementById("practice-feedback");
    if (!statusEl) return;
    if (this.practiceTarget.length === 1) {
      const info = FINGERSPELL_DB.find((x) => x.letter === this.practiceTarget);
      statusEl.textContent = info
        ? `Target Abjad [${info.letter}]: ${info.guide}`
        : `Peragakan Abjad ${this.practiceTarget}`;
    } else {
      const c = CLASSROOM_CONCEPTS.find((x) => x.bisindo === this.practiceTarget);
      statusEl.textContent = c
        ? `Target [${c.bisindo} / ${c.fsl}] (${c.id_text} / ${c.fil_text}): ${c.guide}`
        : `Peragakan Isyarat ${this.practiceTarget}`;
    }
  }

  bindRecorderControls() {
    const catSelect = document.getElementById("rec-category");
    const targetSelect = document.getElementById("rec-target");
    const populateTargets = () => {
      if (!catSelect || !targetSelect) return;
      const list = catSelect.value === "letter" ? FINGERSPELL_LABELS : BISINDO_GLOSSES;
      targetSelect.innerHTML = list.map((item) => `<option value="${item}">${item}</option>`).join("");
    };
    if (catSelect) {
      catSelect.addEventListener("change", populateTargets);
      populateTargets();
    }

    const recBtn = document.getElementById("btn-record-clip");
    const exportBtn = document.getElementById("btn-export-zip");
    const countEl = document.getElementById("rec-clip-count");

    if (recBtn) {
      recBtn.addEventListener("click", () => {
        const signer = document.getElementById("rec-signer")?.value || "S01";
        const category = catSelect?.value || "gloss";
        const target = targetSelect?.value || "HALO";
        const liveBuffer =
          this.vision?.running && Array.isArray(this.recognizer?.buffer) && this.recognizer.buffer.length >= 8
            ? this.recognizer.buffer.slice(-64)
            : null;
        const kpSeq = liveBuffer || generateReferenceSignKeypoints(target, 64);
        const clip = this.recorder.addClip({
          signer,
          category,
          target,
          keypoints: kpSeq,
          sentence: glossToSentenceLocal([target], "id")
        });
        const rep = this.recorder.clips.length;
        const recCode = clip?.clipId || clip?.clip_id || `SBK_${signer}_${target}_${String(rep).padStart(3, "0")}`;
        fetch(`${APP_CONFIG.apiBaseUrl}/db/recordings`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            recording_code: recCode,
            signer_id: signer,
            gloss: target,
            repetition: rep,
            duration: 2.6,
            file_path: `data/raw/selfrec/${recCode}.webm`,
            keypoint_path: `data/keypoints/selfrec/${recCode}.npz`,
            consent_status: "approved",
            validation_status: "valid"
          })
        }).catch(() => {});
        if (countEl) countEl.textContent = String(this.recorder.clips.length);
        speakText(`Klip ${target} tersimpan`, "id-ID");
      });
    }

    if (exportBtn) {
      exportBtn.addEventListener("click", () => {
        const signer = document.getElementById("rec-signer")?.value || "S01";
        if (this.recorder.clips.length === 0) {
          this.recorder.addClip({
            signer,
            category: "gloss",
            target: "HALO",
            keypoints: generateReferenceSignKeypoints("HALO", 64),
            sentence: "Halo."
          });
        }
        const { filename, blob } = this.recorder.exportZipBlob(signer);
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = filename;
        a.click();
        URL.revokeObjectURL(url);
      });
    }
  }

  playReferenceSign(glossName, canvasId) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    const frames = generateReferenceSignKeypoints(glossName, 64);
    let idx = 0;

    if (this.refAnimTimer && this.refAnimTimer[canvasId]) {
      clearInterval(this.refAnimTimer[canvasId]);
    }
    if (!this.refAnimTimer) this.refAnimTimer = {};

    const c = CLASSROOM_CONCEPTS.find((item) => item.bisindo === glossName);
    const labelText = c
      ? `Peraga Kerangka L3: ${c.bisindo} / ${c.fsl} (${c.id_text} — ${c.fil_text})`
      : `Peraga Kerangka L3: ${glossName}`;

    const labelEl = document.getElementById(`${canvasId}-label`);
    if (labelEl) labelEl.textContent = labelText;

    this.refAnimTimer[canvasId] = setInterval(() => {
      drawSkeleton86(ctx, frames[idx % frames.length], canvas.width, canvas.height, {
        hudText: labelText
      });
      idx += 1;
    }, 45);
  }

  updateStateBadge({ state, frames }) {
    const badge = document.getElementById("sign-state-badge");
    if (!badge) return;
    const labelMap = {
      IDLE: "Menunggu Tangan (Idle)",
      RECORDING: `Merekam Gerakan (${frames || 1} frame)`,
      CLASSIFYING: "Mencocokkan Database...",
      SENTENCE: "Isyarat Dikenali",
      SPEAKING: "Menyuarakan (TTS)"
    };
    badge.textContent = labelMap[state] || state;
    badge.setAttribute("data-state", state);
  }

  updateRoomBadge({ connected, roomCode, transport }) {
    const el = document.getElementById("room-status-badge");
    if (!el) return;
    el.textContent = connected ? `Ruang #${roomCode} (${transport})` : "Lokal (1 Perangkat)";
  }

  updateMicButton({ listening, engine }) {
    const btn = document.getElementById("btn-mic-listen");
    if (!btn) return;
    btn.textContent = listening ? `Mendengarkan (${engine})...` : "Mulai Bicara (STT)";
    btn.classList.toggle("active", Boolean(listening));
  }

  handleRoomMessage(msg) {
    if (!msg) return;
    if (msg.type === "deaf_to_hearing" && msg.sentence) {
      const capEl = document.getElementById("giant-caption");
      if (capEl) capEl.textContent = `[Siswa Tuli]: ${msg.sentence}`;
    } else if (msg.type === "hearing_to_deaf" && msg.text) {
      const capEl = document.getElementById("giant-caption");
      if (capEl) capEl.textContent = msg.text;
      if (Array.isArray(msg.concepts) && msg.concepts.length > 0) {
        this.playReferenceSign(msg.concepts[0], "hearing-sign-canvas");
      }
    }
  }
}

if (typeof window !== "undefined") {
  window.addEventListener("DOMContentLoaded", () => {
    const app = new SignBridgeApp();
    app.init();
    window.signBridgeApp = app;
  });
}
