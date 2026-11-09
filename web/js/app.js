/**
 * web/js/app.js
 * Pengendali utama antarmuka web SignBridge ASEAN (BISINDO <-> FSL Filipina + 26 Abjad A-Z).
 * Sistem Desain SaaS Inklusif & Komprehensif — 100% Bahasa Indonesia.
 * Sinkron dengan Model ONNX Runtime Web, MediaPipe Holistic, dan Server FastAPI.
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
    this.currentView = "landing"; // "landing" | "app"
    this.currentAppTab = "panel-translate"; // "panel-translate" | "panel-classroom" | ...
    this.bridgeDirection = "ID-PH";
    this.recognitionMode = "hybrid"; // "hybrid" | "video" | "fingerspell"
    this.autoSpeak = true;
    this.accumulatedGlosses = [];
    this.spelledLetters = [];
    this.currentSentence = "";
    this.practiceTarget = "SAYA";
    this.practiceStreak = 0;
    this.captionSizeIndex = 0;
    this.captionSizes = ["normal", "large", "xlarge"];

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
    this.bindNavigation();
    this.bindLandingPageInteractions();
    this.bindLiveTranslationControls();
    this.bindClassroomControls();
    this.bindBridgeControls();
    this.bindPracticeControls();
    this.bindRecorderControls();
    this.bindAccessibilityAndSettings();
    this.renderConceptBoard("Semua");

    const recStatus = await this.recognizer.init();
    await this.fingerspeller.init();
    const engineText = document.getElementById("engine-status-text");
    const enginePill = document.getElementById("engine-status-pill");
    if (engineText) {
      if (recStatus.ready && recStatus.engine === "onnx-web") {
        engineText.textContent = "ONNX Web M0 (Aktif - 32 WL-BISINDO)";
      } else {
        engineText.textContent = recStatus.error ? `Model M0 Standby: ${recStatus.error}` : "Model AI M0 Standby";
        if (enginePill) {
          enginePill.style.background = "var(--surface-sunken)";
          enginePill.style.color = "var(--text-muted)";
          enginePill.style.borderColor = "var(--border-subtle)";
          const dot = enginePill.querySelector(".dot");
          if (dot) {
            dot.style.backgroundColor = "var(--status-warning)";
            dot.style.boxShadow = "none";
          }
        }
      }
    }

    this.playReferenceSign("HALO", "l3-canvas");
    this.playReferenceSign("SAYA", "practice-ref-canvas");
  }

  /* ==========================================================================
     NAVIGASI UTAMA (LANDING PAGE <-> DASHBOARD APP SHELL)
     ========================================================================== */
  bindNavigation() {
    // Tombol masuk ke App Shell dari Landing Page
    const startBtns = [
      document.getElementById("btn-landing-login"),
      document.getElementById("btn-landing-start"),
      document.getElementById("btn-hero-translate"),
      document.getElementById("btn-bottom-start")
    ];
    startBtns.forEach((btn) => {
      if (btn) {
        btn.addEventListener("click", () => {
          this.switchView("app");
          this.switchAppTab("panel-translate");
        });
      }
    });

    const classBtns = [
      document.getElementById("btn-hero-classroom"),
      document.getElementById("btn-showcase-class")
    ];
    classBtns.forEach((btn) => {
      if (btn) {
        btn.addEventListener("click", () => {
          this.switchView("app");
          this.switchAppTab("panel-classroom");
        });
      }
    });

    // Link footer yang mengarah ke panel aplikasi
    document.querySelectorAll(".nav-to-app").forEach((link) => {
      link.addEventListener("click", (e) => {
        e.preventDefault();
        const target = link.getAttribute("data-target") || "panel-translate";
        this.switchView("app");
        this.switchAppTab(target);
      });
    });

    // Tombol kembali ke Landing Page
    const backBtn = document.getElementById("btn-back-to-landing");
    if (backBtn) {
      backBtn.addEventListener("click", () => this.switchView("landing"));
    }
    const sidebarBrand = document.getElementById("sidebar-brand-click");
    if (sidebarBrand) {
      sidebarBrand.addEventListener("click", () => this.switchView("landing"));
    }

    // Navigasi Tab Sidebar Dashboard
    const navItems = document.querySelectorAll("[data-app-tab]");
    navItems.forEach((item) => {
      item.addEventListener("click", () => {
        const tabTarget = item.getAttribute("data-app-tab");
        this.switchAppTab(tabTarget);
        this.closeMobileDrawer();
      });
    });

    // Mobile Drawer Toggle
    const mobileMenuBtn = document.getElementById("btn-mobile-menu");
    const backdrop = document.getElementById("sidebar-backdrop");
    if (mobileMenuBtn) {
      mobileMenuBtn.addEventListener("click", () => this.toggleMobileDrawer());
    }
    if (backdrop) {
      backdrop.addEventListener("click", () => this.closeMobileDrawer());
    }
  }

  switchView(viewName) {
    this.currentView = viewName;
    const landingView = document.getElementById("view-landing");
    const appView = document.getElementById("view-app");

    if (landingView && appView) {
      landingView.classList.toggle("active", viewName === "landing");
      appView.classList.toggle("active", viewName === "app");
      window.scrollTo({ top: 0, behavior: "smooth" });
    }
  }

  switchAppTab(tabId) {
    this.currentAppTab = tabId;
    const navItems = document.querySelectorAll("[data-app-tab]");
    navItems.forEach((item) => {
      item.classList.toggle("active", item.getAttribute("data-app-tab") === tabId);
    });

    const panels = document.querySelectorAll(".app-view-panel");
    panels.forEach((p) => {
      p.classList.toggle("active", p.id === tabId);
    });

    // Perbarui breadcrumb
    const breadcrumbEl = document.getElementById("breadcrumb-current-view");
    if (breadcrumbEl) {
      const titleMap = {
        "panel-translate": "Terjemahkan",
        "panel-classroom": "Ruang Kelas",
        "panel-sessions": "Riwayat Sesi",
        "panel-guide": "Panduan Bahasa",
        "panel-practice": "Latihan Mandiri",
        "panel-recorder": "Perekam Dataset",
        "panel-settings": "Pengaturan & Aksesibilitas"
      };
      breadcrumbEl.textContent = titleMap[tabId] || "Ruang Kerja";
    }
  }

  toggleMobileDrawer() {
    const sidebar = document.getElementById("app-sidebar");
    const backdrop = document.getElementById("sidebar-backdrop");
    if (sidebar) sidebar.classList.toggle("open");
    if (backdrop) backdrop.classList.toggle("active");
  }

  closeMobileDrawer() {
    const sidebar = document.getElementById("app-sidebar");
    const backdrop = document.getElementById("sidebar-backdrop");
    if (sidebar) sidebar.classList.remove("open");
    if (backdrop) backdrop.classList.remove("active");
  }

  /* ==========================================================================
     INTERAKSI LANDING PAGE (FAQ ACCORDION & PREVIEW)
     ========================================================================== */
  bindLandingPageInteractions() {
    const faqItems = document.querySelectorAll(".faq-item");
    faqItems.forEach((item) => {
      const btn = item.querySelector(".faq-question");
      if (btn) {
        btn.addEventListener("click", () => {
          const isActive = item.classList.contains("active");
          faqItems.forEach((f) => f.classList.remove("active"));
          if (!isActive) item.classList.add("active");
        });
      }
    });
  }

  /* ==========================================================================
     KONTROL TERJEMAHAN LANGSUNG (LIVE TRANSLATION)
     ========================================================================== */
  bindLiveTranslationControls() {
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
          this.recognizer.pushFrame(kp86, { hasVisibleHand });
        }
      }
    });

    const camBtn = document.getElementById("btn-toggle-camera");
    const camPill = document.getElementById("camera-state-pill");
    if (camBtn) {
      camBtn.addEventListener("click", async () => {
        unlockSpeechAudio();
        if (!this.vision.running) {
          const ok = await this.vision.startCamera();
          camBtn.textContent = ok ? "Matikan Kamera" : "Simulasi Kamera (Webcam Siap)";
          if (camPill) camPill.textContent = ok ? "Kamera Aktif" : "Simulasi Kamera";
          if (ok) {
            speakText("Kamera aktif. Angkat tangan untuk mulai berisyarat.", "id-ID");
          } else {
            this.simulateSignInput("SAYA");
          }
        } else {
          this.vision.stopCamera();
          camBtn.textContent = "Aktifkan Kamera";
          if (camPill) camPill.textContent = "Kamera Nonaktif";
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
      const submitText = () => {
        const txt = hearingInput.value.trim();
        if (txt) {
          this.handleSpeechResult({ text: txt, isFinal: true, engine: "Manual" });
          hearingInput.value = "";
        }
      };
      sendHearingBtn.addEventListener("click", submitText);
      hearingInput.addEventListener("keydown", (e) => {
        if (e.key === "Enter") submitText();
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

    // Fullscreen kamera toggle
    const fsBtn = document.getElementById("btn-fullscreen-camera");
    if (fsBtn) {
      fsBtn.addEventListener("click", () => {
        const viewport = document.querySelector(".camera-viewport-wrap");
        if (viewport) {
          if (!document.fullscreenElement) {
            viewport.requestFullscreen().catch(() => {});
          } else {
            document.exitFullscreen().catch(() => {});
          }
        }
      });
    }

    // Tombol Ubah Ukuran Teks Caption Cepat
    const captionSizeBtn = document.getElementById("btn-adjust-caption-size");
    if (captionSizeBtn) {
      captionSizeBtn.addEventListener("click", () => {
        this.captionSizeIndex = (this.captionSizeIndex + 1) % this.captionSizes.length;
        const newSize = this.captionSizes[this.captionSizeIndex];
        this.applyCaptionSize(newSize);
      });
    }

    // Mode Switcher Pills (Isyarat -> Teks & Suara / Suara -> Teks / Jembatan BISINDO <-> FSL)
    const modeTabs = document.querySelectorAll("[data-translate-mode]");
    modeTabs.forEach((tab) => {
      tab.addEventListener("click", () => {
        modeTabs.forEach((t) => t.classList.remove("active"));
        tab.classList.add("active");
        const m = tab.getAttribute("data-translate-mode");
        if (m === "speech" && !this.speechListener.isListening) {
          this.speechListener.start();
        }
      });
    });
  }

  applyCaptionSize(sizeName) {
    const root = document.documentElement;
    const sizeMap = {
      normal: "1.15rem",
      large: "1.5rem",
      xlarge: "2rem"
    };
    root.style.setProperty("--caption-current-size", sizeMap[sizeName] || "1.15rem");
    const selectEl = document.getElementById("setting-caption-size");
    if (selectEl) selectEl.value = sizeName;
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
    this.appendConversationMessage("Ayu Putri (Anda)", "Tuli · BISINDO", text, "mine");
  }

  appendConversationMessage(sender, role, text, type = "normal") {
    const list = document.getElementById("conversation-messages-list");
    if (!list) return;

    const timeStr = new Date().toLocaleTimeString("id-ID", { hour: "2-digit", minute: "2-digit" });
    const bubble = document.createElement("div");
    bubble.className = `chat-bubble ${type === "mine" ? "mine" : ""}`;
    bubble.innerHTML = `
      <div class="chat-bubble-meta">
        <span class="chat-bubble-author">${sender}</span>
        <span>${timeStr}</span>
      </div>
      <div>${text}</div>
      <div style="font-size:0.72rem; color:${type === "mine" ? "var(--teal-dark)" : "var(--text-secondary)"}; font-weight:600; margin-top:0.25rem;">
        ${role}
      </div>
    `;
    list.appendChild(bubble);
    list.scrollTop = list.scrollHeight;
  }

  async simulateSignInput(glossName) {
    const seq = generateReferenceSignKeypoints(glossName, 40);
    const canvasEl = document.getElementById("camera-canvas");
    if (canvasEl) {
      const ctx = canvasEl.getContext("2d");
      drawSkeleton86(ctx, seq[20], canvasEl.width, canvasEl.height, {
        hudText: `PERAGA DATABASE 86 TITIK: [${glossName}]`
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
            `<span class="state-pill" style="font-size:0.75rem;">Huruf ${item.letter} <strong>${Math.round(item.confidence * 100)}%</strong></span>`
        )
        .join("");
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
    if (top3El && pred && Array.isArray(pred.top3) && pred.top3.length > 0) {
      top3El.innerHTML = pred.top3
        .map((item) => {
          const c = CLASSROOM_CONCEPTS.find((x) => x.bisindo === item.gloss);
          const fslTag = c ? ` / ${c.fsl}` : "";
          return `<span class="state-pill" style="font-size:0.75rem;">${item.gloss}${fslTag} <strong>${Math.round(item.confidence * 100)}%</strong></span>`;
        })
        .join("");
    }

    if (pred && pred.success && pred.gloss) {
      const concept = CLASSROOM_CONCEPTS.find((c) => c.bisindo === pred.gloss);
      await this.appendGloss(pred.gloss, pred.confidence || 0.90);

      if (this.autoSpeak) {
        const isID = this.bridgeDirection === "ID-PH";
        const wordToSpeak = concept ? (isID ? concept.id_text : concept.fil_text) : pred.gloss;
        const textToSpeak = this.accumulatedGlosses.length <= 3 ? this.currentSentence : wordToSpeak;
        this.speakCurrentSentence(textToSpeak);
      }
    } else if (pred && pred.error) {
      console.warn("[App] Prediksi isyarat tidak berhasil:", pred.error);
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
        statusEl.textContent = `Tepat! Isyarat ${cleanGloss} berhasil dikenali (${Math.round(confidence * 100)}%).`;
      }
    }
  }

  renderGlossSequence() {
    const container = document.getElementById("gloss-sequence-chips");
    if (!container) return;
    if (this.accumulatedGlosses.length === 0) {
      container.innerHTML = `<span class="muted" style="font-size:0.82rem;">Belum ada isyarat terdeteksi.</span>`;
      const sentEl = document.getElementById("natural-sentence-output");
      if (sentEl) sentEl.textContent = "Menunggu deret isyarat...";
      return;
    }
    container.innerHTML = this.accumulatedGlosses
      .map((g) => {
        const c = CLASSROOM_CONCEPTS.find((item) => item.bisindo === g);
        return c ? `<span class="state-pill live" style="font-size:0.75rem;">[${c.bisindo} / ${c.fsl}]</span>` : `<span class="state-pill" style="font-size:0.75rem;">[${g}]</span>`;
      })
      .join(" ");
  }

  async refreshNaturalSentence() {
    const sentEl = document.getElementById("natural-sentence-output");
    if (!sentEl || this.accumulatedGlosses.length === 0) return;

    const srcLang = this.bridgeDirection === "ID-PH" ? "id" : "fil";
    const built = await buildNaturalSentence(this.accumulatedGlosses, {
      apiBaseUrl: APP_CONFIG.apiBaseUrl,
      lang: srcLang
    });
    this.currentSentence = built.text;
    sentEl.textContent = built.text;
  }

  handleSpeechResult({ text, isFinal }) {
    const capEl = document.getElementById("giant-caption");
    if (capEl && text) {
      capEl.textContent = text;
    }
    if (isFinal && text) {
      const concepts = sentenceToConceptGlosses(text);
      this.room.broadcast({
        type: "hearing_to_deaf",
        text,
        concepts: concepts.map((c) => c.bisindo)
      });
      this.appendConversationMessage("Raka Pratama", "Dengar · Suara", text, "normal");
    }
  }

  /* ==========================================================================
     KONTROL RUANG KELAS INKLUSIF
     ========================================================================== */
  bindClassroomControls() {
    // Tombol Salin Kode Kelas
    const copyBtn = document.getElementById("btn-copy-class-code");
    if (copyBtn) {
      copyBtn.addEventListener("click", () => {
        navigator.clipboard.writeText("BRIDGE-204").catch(() => {});
        const span = copyBtn.querySelector("span");
        if (span) {
          const old = span.textContent;
          span.textContent = "Disalin! ✓";
          setTimeout(() => { span.textContent = old; }, 1800);
        }
      });
    }

    // Tombol Berikan Kesempatan Bicara (Give Floor)
    const floorBtn = document.getElementById("btn-give-floor");
    if (floorBtn) {
      floorBtn.addEventListener("click", () => {
        floorBtn.textContent = "Kesempatan Diberikan! ✓";
        floorBtn.classList.remove("btn-primary");
        floorBtn.classList.add("btn-outline");
        speakText("Ayu Putri, silakan menyampaikan isyarat kepada kelas.", "id-ID");
        setTimeout(() => {
          floorBtn.textContent = "Berikan Kesempatan";
          floorBtn.classList.add("btn-primary");
          floorBtn.classList.remove("btn-outline");
        }, 3000);
      });
    }
  }

  /* ==========================================================================
     PANDUAN BAHASA & FONOLOGI
     ========================================================================== */
  bindBridgeControls() {
    const filterBtns = document.querySelectorAll("[data-concept-filter]");
    filterBtns.forEach((btn) => {
      btn.addEventListener("click", () => {
        filterBtns.forEach((b) => b.classList.remove("active"));
        btn.classList.add("active");
        this.renderConceptBoard(btn.getAttribute("data-concept-filter"));
      });
    });
  }

  renderConceptBoard(categoryFilter = "Semua") {
    const grid = document.getElementById("concept-board-grid");
    if (!grid) return;

    if (categoryFilter === "Abjad") {
      grid.innerHTML = FINGERSPELL_DB.map(
        (item, idx) => `
        <article class="concept-card">
          <div class="concept-card-header">
            <span class="concept-gloss">Huruf ${item.letter}</span>
            <span class="concept-category-badge">Ejaan Jari A${String(idx + 1).padStart(2, "0")}</span>
          </div>
          <p style="font-size:0.84rem; color:var(--text-secondary); margin-bottom:0.5rem;">${item.guide}</p>
          <div style="font-size:0.8rem; display:flex; gap:0.5rem; margin-bottom:0.75rem;">
            <span>ID: <strong>${item.example_id}</strong></span> · <span>PH: <strong>${item.example_fil}</strong></span>
          </div>
          <div style="display:flex; gap:0.4rem;">
            <button type="button" class="btn btn-outline btn-sm" data-speak-id="Huruf ${item.letter}, ${item.example_id}">Suara</button>
            <button type="button" class="btn btn-primary btn-sm" data-preview-sign="${item.letter}">Peraga L3</button>
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
          <article class="concept-card">
            <div class="concept-card-header">
              <span class="concept-gloss">${c.bisindo} / ${c.fsl}</span>
              <span class="concept-category-badge">${c.category}</span>
              ${c.supported !== false ? '<span class="state-pill live" style="font-size:0.7rem; margin-left:auto;">Didukung M0</span>' : '<span class="state-pill" style="font-size:0.7rem; margin-left:auto; background:var(--surface-sunken); color:var(--text-muted);">Roadmap M2</span>'}
            </div>
            <p style="font-size:0.88rem; font-weight:700; color:var(--teal-dark); margin-bottom:0.25rem;">
              "${c.id_text}" &harr; "${c.fil_text}"
            </p>
            <p style="font-size:0.8rem; color:var(--text-secondary); line-height:1.4; margin-bottom:0.5rem;">${c.guide}</p>
            <div style="display:flex; gap:0.4rem; margin-top:auto;">
              <button type="button" class="btn btn-outline btn-sm" data-speak-id="${c.id_text}">Suara</button>
              <button type="button" class="btn btn-primary btn-sm" data-preview-sign="${c.bisindo}">Peraga L3</button>
            </div>
          </article>`
        )
        .join("");
    }

    grid.querySelectorAll("[data-speak-id]").forEach((btn) => {
      btn.addEventListener("click", () => speakText(btn.getAttribute("data-speak-id"), "id-ID"));
    });
    grid.querySelectorAll("[data-preview-sign]").forEach((btn) => {
      btn.addEventListener("click", () => {
        const g = btn.getAttribute("data-preview-sign");
        this.playReferenceSign(g, "l3-canvas");
        window.scrollTo({ top: 0, behavior: "smooth" });
      });
    });
  }

  /* ==========================================================================
     LATIHAN MANDIRI & PEREKAM
     ========================================================================== */
  bindPracticeControls() {
    const selectEl = document.getElementById("practice-target-select");
    if (selectEl) {
      const m0Opts = CLASSROOM_CONCEPTS.filter((c) => c.supported !== false).map(
        (c) => `<option value="${c.bisindo}">M0: ${c.bisindo} / ${c.fsl} (${c.id_text})</option>`
      ).join("");
      const extOpts = CLASSROOM_CONCEPTS.filter((c) => c.supported === false).map(
        (c) => `<option value="${c.bisindo}" disabled>Roadmap M2: ${c.bisindo} / ${c.fsl} (${c.id_text})</option>`
      ).join("");
      const alphaOpts = FINGERSPELL_DB.map(
        (a) => `<option value="${a.letter}">Abjad: Huruf ${a.letter} (${a.guide})</option>`
      ).join("");
      selectEl.innerHTML = `<optgroup label="32 Kata Utama Didukung Model M0">${m0Opts}</optgroup><optgroup label="26 Abjad Ejaan Jari (A-Z)">${alphaOpts}</optgroup><optgroup label="Konsep Kelas Lainnya (Target Roadmap M2)">${extOpts}</optgroup>`;
      selectEl.value = this.practiceTarget;
      selectEl.addEventListener("change", () => {
        this.practiceTarget = selectEl.value;
        this.playReferenceSign(this.practiceTarget, "practice-ref-canvas");
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
        const kpSeq = generateReferenceSignKeypoints(target, 64);
        this.recorder.addClip({
          signer,
          category,
          target,
          keypoints: kpSeq,
          sentence: glossToSentenceLocal([target], "id")
        });
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

  /* ==========================================================================
     PENGATURAN & AKSESIBILITAS
     ========================================================================== */
  bindAccessibilityAndSettings() {
    const sizeSelect = document.getElementById("setting-caption-size");
    if (sizeSelect) {
      sizeSelect.addEventListener("change", () => this.applyCaptionSize(sizeSelect.value));
    }

    const contrastCheck = document.getElementById("setting-high-contrast");
    if (contrastCheck) {
      contrastCheck.addEventListener("change", () => {
        document.body.classList.toggle("high-contrast", contrastCheck.checked);
      });
    }

    const motionCheck = document.getElementById("setting-reduced-motion");
    if (motionCheck) {
      motionCheck.addEventListener("change", () => {
        document.documentElement.style.setProperty(
          "--trans-normal",
          motionCheck.checked ? "0.01ms" : "0.28s cubic-bezier(0.16, 1, 0.3, 1)"
        );
      });
    }

    const autoTtsCheck = document.getElementById("setting-auto-tts");
    if (autoTtsCheck) {
      autoTtsCheck.addEventListener("change", () => {
        this.autoSpeak = autoTtsCheck.checked;
        const mainChk = document.getElementById("chk-auto-speak");
        if (mainChk) mainChk.checked = this.autoSpeak;
      });
    }

    const sensSlider = document.getElementById("setting-sensitivity");
    if (sensSlider) {
      sensSlider.addEventListener("input", () => {
        const val = parseFloat(sensSlider.value);
        if (this.recognizer) this.recognizer.minConfidence = val;
      });
    }
  }

  /* ==========================================================================
     CANVAS PERAGA KERANGKA L3
     ========================================================================== */
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
      IDLE: "Mengenali Isyarat (Idle)",
      RECORDING: `Merekam Gerakan (${frames || 1} frame)`,
      CLASSIFYING: "Mencocokkan Database...",
      SENTENCE: "Isyarat Dikenali",
      SPEAKING: "Menyuarakan (TTS)"
    };
    badge.textContent = labelMap[state] || state;
  }

  updateRoomBadge({ connected, roomCode }) {
    const el = document.getElementById("topbar-room-info");
    if (!el) return;
    el.innerHTML = connected ? `<span>Ruang #${roomCode}</span>` : `<span>Ruang Demo</span>`;
  }

  updateMicButton({ listening }) {
    const btn = document.getElementById("btn-mic-listen");
    if (!btn) return;
    btn.textContent = listening ? "Mendengarkan Suara..." : "Mikrofon Aktif";
    btn.classList.toggle("btn-primary", Boolean(listening));
    btn.classList.toggle("btn-outline", !listening);
  }

  handleRoomMessage(msg) {
    if (!msg) return;
    if (msg.type === "deaf_to_hearing" && msg.sentence) {
      this.appendConversationMessage("Siswa Tuli (Jarak Jauh)", "BISINDO", msg.sentence, "normal");
    } else if (msg.type === "hearing_to_deaf" && msg.text) {
      this.appendConversationMessage("Rekan Dengar (Jarak Jauh)", "Suara Indonesia", msg.text, "normal");
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
