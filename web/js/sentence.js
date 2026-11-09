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

/**
 * Konstruksi kalimat dengan fallback otomatis:
 * Mencoba endpoint server POST /sentence (IndoT5/mT5) jika tersedia,
 * dan kembali ke glossToSentenceLocal (B0) bila luring/gagal.
 */
export async function buildNaturalSentence(glossList, { apiBaseUrl = "", lang = "id", preferServer = true } = {}) {
  const localSentence = glossToSentenceLocal(glossList, lang);
  if (!preferServer || !glossList || glossList.length === 0) {
    return { text: localSentence, source: "B0-local" };
  }

  try {
    const glossStr = Array.isArray(glossList) ? glossList.join(" ") : String(glossList);
    const resp = await fetch(`${apiBaseUrl}/sentence`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ gloss: glossStr, lang })
    });
    if (resp.ok) {
      const data = await resp.json();
      if (data && data.text) {
        return { text: data.text, source: data.model || "T2-server" };
      }
    }
  } catch (_err) {
    // Offline atau server tidak aktif -> gunakan B0 lokal
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

