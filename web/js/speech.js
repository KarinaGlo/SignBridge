/**
 * web/js/speech.js
 * Modul Text-to-Speech (TTS) & Speech-to-Text (STT) Dwibahasa (id-ID & fil-PH)
 * dengan pembuka kunci audio otomatis (audio unlock) dan fallback bunyi bip konfirmasi.
 */

let audioCtx = null;

/**
 * Buka kunci Web Speech API & Web Audio API saat pengguna mengeklik tombol kamera.
 */
export function unlockSpeechAudio() {
  if (typeof window === "undefined") return;
  try {
    if ("speechSynthesis" in window) {
      window.speechSynthesis.cancel();
      const silent = new SpeechSynthesisUtterance("");
      silent.volume = 0;
      window.speechSynthesis.speak(silent);
    }
    const AudioContextClass = window.AudioContext || window.webkitAudioContext;
    if (AudioContextClass && !audioCtx) {
      audioCtx = new AudioContextClass();
    }
    if (audioCtx && audioCtx.state === "suspended") {
      audioCtx.resume();
    }
  } catch (_e) {}
}

/**
 * Bunyi lonceng halus saat isyarat berhasil dikenali dari kamera.
 */
export function playRecognitionChime() {
  if (typeof window === "undefined") return;
  try {
    const AudioContextClass = window.AudioContext || window.webkitAudioContext;
    if (!AudioContextClass) return;
    if (!audioCtx) audioCtx = new AudioContextClass();
    if (audioCtx.state === "suspended") audioCtx.resume();

    const osc = audioCtx.createOscillator();
    const gain = audioCtx.createGain();
    osc.type = "sine";
    osc.frequency.setValueAtTime(587.33, audioCtx.currentTime); // D5
    osc.frequency.setValueAtTime(880.0, audioCtx.currentTime + 0.08); // A5
    gain.gain.setValueAtTime(0.12, audioCtx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + 0.24);
    osc.connect(gain);
    gain.connect(audioCtx.destination);
    osc.start();
    osc.stop(audioCtx.currentTime + 0.25);
  } catch (_e) {}
}

let cachedVoices = [];
if (typeof window !== "undefined" && "speechSynthesis" in window) {
  cachedVoices = window.speechSynthesis.getVoices() || [];
  window.speechSynthesis.onvoiceschanged = () => {
    try {
      cachedVoices = window.speechSynthesis.getVoices() || [];
    } catch (_e) {}
  };
}

export function speakText(text, lang = "id-ID") {
  if (!text || typeof window === "undefined") {
    if (typeof window !== "undefined" && window.signbridgeDebug) {
      window.signbridgeDebug.lastTTS = { text: "", status: "skipped_empty_text", timestamp: Date.now() };
    }
    return false;
  }
  playRecognitionChime();

  if (!("speechSynthesis" in window)) {
    if (window.signbridgeDebug) {
      window.signbridgeDebug.lastTTS = { text, status: "speech_synthesis_unavailable", timestamp: Date.now() };
    }
    return false;
  }

  try {
    const utter = new SpeechSynthesisUtterance(text);
    const targetLang = lang === "fil" || lang === "ph" ? "fil-PH" : lang === "en" ? "en-US" : "id-ID";
    utter.lang = targetLang;
    utter.rate = 0.98;
    utter.pitch = 1.0;
    utter.volume = 1.0;

    const voices = cachedVoices.length > 0 ? cachedVoices : (window.speechSynthesis.getVoices ? window.speechSynthesis.getVoices() : []);
    const matchedVoice =
      voices.find((v) => v.lang && v.lang.toLowerCase().startsWith(targetLang.slice(0, 2).toLowerCase())) ||
      voices.find((v) => v.lang && v.lang.toLowerCase().startsWith("id")) ||
      voices[0];
    if (matchedVoice) {
      utter.voice = matchedVoice;
    }

    const ttsMeta = {
      text,
      lang: targetLang,
      voice: matchedVoice ? matchedVoice.name : "default",
      status: "queued",
      timestamp: Date.now()
    };

    utter.onstart = () => {
      ttsMeta.status = "speaking";
      if (window.signbridgeDebug) window.signbridgeDebug.lastTTS = { ...ttsMeta };
    };

    utter.onend = () => {
      ttsMeta.status = "finished";
      if (window.signbridgeDebug) window.signbridgeDebug.lastTTS = { ...ttsMeta };
    };

    utter.onerror = (err) => {
      ttsMeta.status = "error";
      ttsMeta.error = err?.error || String(err);
      if (window.signbridgeDebug) window.signbridgeDebug.lastTTS = { ...ttsMeta };
      console.warn("[TTS] Utterance error:", err);
    };

    if (window.signbridgeDebug) {
      window.signbridgeDebug.lastTTS = { ...ttsMeta };
    }

    // Hindari Chromium/Edge Bug: Pastikan state tidak ter-pause
    if (window.speechSynthesis.paused) {
      window.speechSynthesis.resume();
    }

    // Hindari Chromium Bug 679437: Jika sedang aktif bicara, batalkan dan beri jeda 30ms
    if (window.speechSynthesis.speaking || window.speechSynthesis.pending) {
      window.speechSynthesis.cancel();
      setTimeout(() => {
        try {
          if (window.speechSynthesis.paused) window.speechSynthesis.resume();
          window.speechSynthesis.speak(utter);
        } catch (e) {
          console.warn("[TTS] Speak failed after cancel:", e);
        }
      }, 30);
    } else {
      window.speechSynthesis.speak(utter);
    }
    return true;
  } catch (err) {
    if (window.signbridgeDebug) {
      window.signbridgeDebug.lastTTS = { text, status: "exception", error: String(err), timestamp: Date.now() };
    }
    return false;
  }
}

export class SpeechListener {
  constructor({ apiBaseUrl = "", lang = "id-ID", onResult = () => {}, onStateChange = () => {} } = {}) {
    this.apiBaseUrl = apiBaseUrl;
    this.lang = lang;
    this.onResult = onResult;
    this.onStateChange = onStateChange;
    this.recognition = null;
    this.mediaRecorder = null;
    this.chunks = [];
    this.isListening = false;
  }

  setLanguage(lang) {
    this.lang = lang === "fil" || lang === "ph" ? "fil-PH" : "id-ID";
    if (this.recognition) {
      this.recognition.lang = this.lang;
    }
  }

  async start() {
    if (this.isListening) return;
    const SpeechRecognition =
      typeof window !== "undefined" && (window.SpeechRecognition || window.webkitSpeechRecognition);

    if (SpeechRecognition) {
      this.recognition = new SpeechRecognition();
      this.recognition.lang = this.lang;
      this.recognition.continuous = false;
      this.recognition.interimResults = true;

      this.recognition.onstart = () => {
        this.isListening = true;
        this.onStateChange({ listening: true, engine: "WebSpeech" });
      };

      this.recognition.onresult = (event) => {
        let transcript = "";
        let isFinal = false;
        for (let i = event.resultIndex; i < event.results.length; i++) {
          transcript += event.results[i][0].transcript;
          if (event.results[i].isFinal) isFinal = true;
        }
        this.onResult({ text: transcript.trim(), isFinal, engine: "WebSpeech" });
      };

      this.recognition.onerror = () => {
        this.isListening = false;
        this.onStateChange({ listening: false, engine: "WebSpeech" });
      };

      this.recognition.onend = () => {
        this.isListening = false;
        this.onStateChange({ listening: false, engine: "WebSpeech" });
      };

      this.recognition.start();
      return;
    }

    if (typeof navigator !== "undefined" && navigator.mediaDevices) {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      this.chunks = [];
      this.mediaRecorder = new MediaRecorder(stream);
      this.mediaRecorder.ondataavailable = (e) => {
        if (e.data && e.data.size > 0) this.chunks.push(e.data);
      };
      this.mediaRecorder.onstop = async () => {
        stream.getTracks().forEach((t) => t.stop());
        const blob = new Blob(this.chunks, { type: "audio/webm" });
        await this._sendToWhisper(blob);
      };
      this.mediaRecorder.start();
      this.isListening = true;
      this.onStateChange({ listening: true, engine: "Whisper-Server" });
    }
  }

  stop() {
    if (!this.isListening) return;
    if (this.recognition) {
      this.recognition.stop();
    } else if (this.mediaRecorder && this.mediaRecorder.state !== "inactive") {
      this.mediaRecorder.stop();
    }
    this.isListening = false;
    this.onStateChange({ listening: false });
  }

  async _sendToWhisper(blob) {
    try {
      const form = new FormData();
      form.append("file", blob, "speech.webm");
      form.append("lang", this.lang.startsWith("fil") ? "tl" : "id");
      const resp = await fetch(`${this.apiBaseUrl}/asr`, {
        method: "POST",
        body: form
      });
      if (resp.ok) {
        const data = await resp.json();
        if (data && data.text) {
          this.onResult({ text: data.text, isFinal: true, engine: "Whisper-Server" });
        }
      }
    } catch (_err) {}
  }
}
