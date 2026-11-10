/**
 * web/js/sentence.js
 * Kontrak B0 & T1-T3 (PDF Hal. 21 & 29):
 *   - Konstruksi kalimat natural dari deret gloss secara lokal (B0 rules)
 *   - Maupun peningkatan ke server IndoT5 / mT5 via POST /sentence.
 *   - Juga memetakan kalimat suara/teks menjadi deret gloss BISINDO/FSL untuk animasi L3.
 */

import { CLASSROOM_CONCEPTS } from "./config.js";

const GLOSS_TO_ID_WORD = {
  // 32 Kosakata Utama Model M0 WL-BISINDO
  AIR: "air",
  BELAJAR: "belajar",
  CARI: "mencari",
  HARI: "hari",
  INGAT: "mengingat",
  LAGI: "lagi",
  MAAF: "maaf",
  MAKAN: "makan",
  MOTOR: "sepeda motor",
  SAYA: "saya",
  TERIMA_KASIH: "terima kasih",
  TULI: "teman tuli",
  APA: "apa",
  SIAPA: "siapa",
  KAPAN: "kapan",
  DIMANA: "di mana",
  MENGAPA: "mengapa",
  BAGAIMANA: "bagaimana",
  MERAH: "merah",
  KUNING: "kuning",
  HIJAU: "hijau",
  HITAM: "hitam",
  DENGAR: "mendengar",
  BERANGKAT: "berangkat",
  DATANG: "datang",
  TEMAN: "teman",
  KELUARGA: "keluarga",
  RUMAH: "rumah",
  PAGI: "pagi",
  SIANG: "siang",
  SORE: "sore",
  MALAM: "malam",

  // Kosakata Ruang Kelas Tambahan
  HALO: "halo",
  TOLONG: "tolong",
  KAMU: "kamu",
  GURU: "guru",
  MAU: "ingin",
  SUDAH: "sudah",
  BELUM: "belum",
  BISA: "bisa",
  TIDAK: "tidak",
  ADA: "ada",
  PAHAM: "mengerti",
  TANYA: "bertanya",
  BACA: "membaca",
  TULIS: "menulis",
  JAWAB: "menjawab",
  BUKU: "buku",
  TUGAS: "tugas",
  KELAS: "di kelas",
  SEKOLAH: "di sekolah",
  BAIK: "baik",
  BENAR: "benar",
  SALAH: "salah"
};

const GLOSS_TO_FIL_WORD = {
  // 32 Kosakata Utama Model M0 WL-BISINDO
  AIR: "tubig",
  BELAJAR: "mag-aral",
  CARI: "maghanap",
  HARI: "araw",
  INGAT: "alalahanin",
  LAGI: "muli",
  MAAF: "paumanhin",
  MAKAN: "kumain",
  MOTOR: "motorsiklo",
  SAYA: "ako ay",
  TERIMA_KASIH: "salamat",
  TULI: "bingi",
  APA: "ano",
  SIAPA: "sino",
  KAPAN: "kailan",
  DIMANA: "saan",
  MENGAPA: "bakit",
  BAGAIMANA: "paano",
  MERAH: "pula",
  KUNING: "dilaw",
  HIJAU: "berde",
  HITAM: "itim",
  DENGAR: "makinig",
  BERANGKAT: "aalis",
  DATANG: "dumating",
  TEMAN: "kaibigan",
  KELUARGA: "pamilya",
  RUMAH: "bahay",
  PAGI: "umaga",
  SIANG: "tanghali",
  SORE: "hapon",
  MALAM: "gabi",

  // Kosakata Ruang Kelas Tambahan
  HALO: "kumusta",
  TOLONG: "pakiusap tulungan",
  KAMU: "ikaw ay",
  GURU: "sa guro",
  MAU: "gustong",
  SUDAH: "tapos nang",
  BELUM: "hindi pa",
  BISA: "kaya nang",
  TIDAK: "hindi",
  ADA: "mayroon",
  PAHAM: "nakakaintindi",
  TANYA: "magtanong",
  BACA: "magbasa",
  TULIS: "magsulat",
  JAWAB: "sumagot",
  BUKU: "ng libro",
  TUGAS: "ng takdang-aralin",
  KELAS: "sa klase",
  SEKOLAH: "sa paaralan",
  BAIK: "mabuti",
  BENAR: "tama",
  SALAH: "mali"
};

const QUESTION_GLOSSES = new Set(["APA", "SIAPA", "DIMANA", "KAPAN", "BAGAIMANA", "MENGAPA"]);

/**
 * B0 Rule-based Gloss -> Kalimat Natural (berjalan instan < 1 ms di peramban).
 */
export function glossToSentenceLocal(glossList, lang = "id") {
  if (!glossList || glossList.length === 0) return "";

  const tokens = Array.isArray(glossList)
    ? glossList.map((g) => String(g).trim().toUpperCase()).filter(Boolean)
    : String(glossList).trim().toUpperCase().split(/\s+/).filter(Boolean);

  if (tokens.length === 0) return "";

  // Dedup berurutan (mis. ["SAYA", "SAYA", "MAU"] -> ["SAYA", "MAU"])
  const dedup = [];
  for (const t of tokens) {
    if (dedup.length === 0 || dedup[dedup.length - 1] !== t) {
      dedup.push(t);
    }
  }

  const isQuestion = dedup.some((g) => QUESTION_GLOSSES.has(g));
  const key = dedup.join(" ");

  if (lang === "fil" || lang === "tl") {
    const filTemplates = {
      "HALO GURU": "Kumusta po, guro.",
      "HALO TEMAN": "Kumusta, kaibigan.",
      "SAYA MAU TANYA GURU": "Gusto ko pong magtanong sa guro.",
      "SAYA BELUM PAHAM TUGAS": "Hindi ko pa po naiintindihan ang takdang-aralin.",
      "SAYA SUDAH PAHAM": "Naiintindihan ko na po.",
      "TOLONG BACA BUKU": "Pakibasa po ang libro.",
      "TERIMA_KASIH GURU": "Maraming salamat po, guro."
    };
    if (filTemplates[key]) return filTemplates[key];
    const words = dedup.map((g) => GLOSS_TO_FIL_WORD[g] || g.toLowerCase().replace(/_/g, " "));
    const raw = words.join(" ").replace(/\s+/g, " ").trim();
    const cap = raw.charAt(0).toUpperCase() + raw.slice(1);
    return cap + (isQuestion ? "?" : ".");
  }

  const idTemplates = {
    "HALO GURU": "Halo Bapak/Ibu Guru.",
    "HALO TEMAN": "Halo teman-teman.",
    "SAYA MAU TANYA GURU": "Saya ingin bertanya kepada guru.",
    "SAYA MAU TANYA": "Saya ingin bertanya.",
    "SAYA BELUM PAHAM": "Maaf, saya belum mengerti.",
    "SAYA BELUM PAHAM TUGAS": "Maaf, saya belum memahami tugas ini.",
    "SAYA SUDAH PAHAM": "Saya sudah mengerti.",
    "SAYA SUDAH BACA BUKU": "Saya sudah membaca buku.",
    "SAYA SEDANG BELAJAR": "Saya sedang belajar di kelas.",
    "TOLONG JAWAB": "Tolong bantu menjawab pertanyaan ini.",
    "TERIMA_KASIH GURU": "Terima kasih banyak, Guru.",
    "DIMANA KELAS": "Di mana ruang kelas kita?",
    "KAPAN TUGAS": "Kapan tugas ini dikumpulkan?"
  };
  if (idTemplates[key]) return idTemplates[key];

  const words = [];
  for (let i = 0; i < dedup.length; i++) {
    const g = dedup[i];
    const prev = i > 0 ? dedup[i - 1] : null;
    if (g === "GURU" && (prev === "TANYA" || prev === "JAWAB")) {
      words.push("kepada guru");
    } else if (g === "TEMAN" && (prev === "TANYA" || prev === "JAWAB")) {
      words.push("kepada teman");
    } else {
      words.push(GLOSS_TO_ID_WORD[g] || g.toLowerCase().replace(/_/g, " "));
    }
  }

  const raw = words.join(" ").replace(/\s+/g, " ").trim();
  const cap = raw.charAt(0).toUpperCase() + raw.slice(1);
  return cap + (isQuestion ? "?" : ".");
}

// State circuit-breaker untuk ketersediaan server endpoint /sentence
let isServerSentenceEndpointActive = true;
let lastServerEndpointAttempt = 0;
const SERVER_RETRY_INTERVAL_MS = 60000; // Coba kembali setelah 60 detik jika sebelumnya gagal

/**
 * Reset status ketersediaan server endpoint /sentence (berguna untuk pengujian atau jika backend baru dinyalakan).
 */
export function resetServerSentenceStatus() {
  isServerSentenceEndpointActive = true;
  lastServerEndpointAttempt = 0;
}

/**
 * Konstruksi kalimat dengan fallback otomatis & perlindungan HTTP 501:
 * 1. Jika apiBaseUrl kosong ("") -> Langsung gunakan B0-local tanpa mengirim HTTP POST yang tidak perlu ke server statis.
 * 2. Jika apiBaseUrl didefinisikan dan endpoint aktif -> Panggil endpoint backend POST /sentence.
 * 3. Jika backend mengembalikan 501 / 404 / error jaringan -> Aktifkan circuit-breaker dan fallback ke B0-local.
 */
export async function buildNaturalSentence(glossList, { apiBaseUrl = "", lang = "id", preferServer = true } = {}) {
  const localSentence = glossToSentenceLocal(glossList, lang);
  if (!glossList || glossList.length === 0) {
    return { text: localSentence, source: "B0-local" };
  }

  // Jika apiBaseUrl tidak dikonfigurasi atau preferServer bernilai false -> gunakan pemrosesan lokal B0 murni.
  // Ini mengeliminasi request HTTP 501 ke server statis (seperti python http.server pada localhost:8000).
  const trimmedUrl = String(apiBaseUrl || "").trim().replace(/\/+$/, "");
  if (!trimmedUrl || !preferServer) {
    return { text: localSentence, source: "B0-local" };
  }

  // Periksa apakah server endpoint sedang dalam masa cooldown circuit-breaker
  const now = Date.now();
  if (!isServerSentenceEndpointActive && (now - lastServerEndpointAttempt) < SERVER_RETRY_INTERVAL_MS) {
    return { text: localSentence, source: "B0-local" };
  }

  try {
    const glossStr = Array.isArray(glossList) ? glossList.join(" ") : String(glossList);
    const controller = typeof AbortController !== "undefined" ? new AbortController() : null;
    const timeoutId = controller ? setTimeout(() => controller.abort(), 3000) : null;

    const resp = await fetch(`${trimmedUrl}/sentence`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ gloss: glossStr, lang }),
      signal: controller ? controller.signal : undefined
    });

    if (timeoutId) clearTimeout(timeoutId);

    if (resp.ok) {
      const data = await resp.json();
      if (data && data.text) {
        isServerSentenceEndpointActive = true;
        return { text: data.text, source: data.model || "T2-server" };
      }
    } else {
      // Jika server mengembalikan 501 (Not Implemented) atau 404 (Not Found) -> Server tidak mendukung endpoint ini
      if (resp.status === 501 || resp.status === 404 || resp.status === 405) {
        isServerSentenceEndpointActive = false;
        lastServerEndpointAttempt = now;
        console.info(`[Sentence] Endpoint ${trimmedUrl}/sentence mengembalikan HTTP ${resp.status}. Beralih ke pemrosesan lokal B0.`);
      }
    }
  } catch (_err) {
    // Offline atau server tidak aktif -> aktifkan circuit-breaker dan gunakan B0 lokal
    isServerSentenceEndpointActive = false;
    lastServerEndpointAttempt = now;
  }
  return { text: localSentence, source: "B0-local" };
}

/**
 * Konversi teks ucapan guru/siswa (Indonesia / Filipina / Inggris) menjadi
 * deret konsep gloss BISINDO/FSL untuk divisualisasikan pada peraga kerangka L3.
 */
export function sentenceToConceptGlosses(text) {
  if (!text) return [];
  const clean = String(text)
    .toLowerCase()
    .replace(/[^\w\s-]/g, " ")
    .split(/\s+/)
    .filter(Boolean);

  const matched = [];
  for (const word of clean) {
    for (const c of CLASSROOM_CONCEPTS) {
      const idWords = c.id_text.toLowerCase().split(/[\s/]+/);
      const filWords = c.fil_text.toLowerCase().split(/[\s/]+/);
      const enWords = c.en_text.toLowerCase().split(/[\s/]+/);
      if (
        c.bisindo.toLowerCase() === word ||
        c.fsl.toLowerCase() === word ||
        idWords.includes(word) ||
        filWords.includes(word) ||
        enWords.includes(word)
      ) {
        if (matched.length === 0 || matched[matched.length - 1].id !== c.id) {
          matched.push(c);
        }
        break;
      }
    }
  }
  return matched;
}

