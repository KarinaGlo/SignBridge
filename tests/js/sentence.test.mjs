import test from "node:test";
import assert from "node:assert/strict";
import {
  glossToSentenceLocal,
  buildNaturalSentence,
  resetServerSentenceStatus,
  sentenceToConceptGlosses
} from "../../web/js/sentence.js";

test("glossToSentenceLocal: konstruksi kalimat B0 lokal bahasa Indonesia", () => {
  // 1. Template kalimat sopan
  const s1 = glossToSentenceLocal(["HALO", "GURU"], "id");
  assert.equal(s1, "Halo Bapak/Ibu Guru.");

  const s2 = glossToSentenceLocal(["SAYA", "MAU", "TANYA", "GURU"], "id");
  assert.equal(s2, "Saya ingin bertanya kepada guru.");

  // 2. Kalimat tanya
  const s3 = glossToSentenceLocal(["DIMANA", "KELAS"], "id");
  assert.equal(s3, "Di mana ruang kelas kita?");

  // 3. Kalimat bebas 32 WL-BISINDO dengan dedup
  const s4 = glossToSentenceLocal(["SAYA", "SAYA", "MAKAN", "PAGI"], "id");
  assert.equal(s4, "Saya makan pagi.");
});

test("glossToSentenceLocal: konstruksi kalimat B0 lokal bahasa Filipina", () => {
  const f1 = glossToSentenceLocal(["HALO", "GURU"], "fil");
  assert.equal(f1, "Kumusta po, guro.");

  const f2 = glossToSentenceLocal(["TERIMA_KASIH", "GURU"], "fil");
  assert.equal(f2, "Maraming salamat po, guro.");

  const f3 = glossToSentenceLocal(["SAYA", "MAKAN"], "fil");
  assert.ok(f3.toLowerCase().includes("kumain"));
});

test("buildNaturalSentence: bebas HTTP 501 saat apiBaseUrl kosong (Edge/Offline Mode)", async () => {
  resetServerSentenceStatus();

  // Simpan fetch asli
  const originalFetch = globalThis.fetch;
  let fetchCalled = false;
  globalThis.fetch = async () => {
    fetchCalled = true;
    throw new Error("fetch tidak boleh dipanggil saat apiBaseUrl kosong!");
  };

  try {
    const res = await buildNaturalSentence(["SAYA", "BELAJAR"], {
      apiBaseUrl: "",
      lang: "id"
    });

    assert.equal(fetchCalled, false, "fetch TIDAK boleh dipanggil saat apiBaseUrl kosong");
    assert.equal(res.source, "B0-local");
    assert.ok(res.text.length > 0);
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test("buildNaturalSentence: circuit-breaker aktif saat server mengembalikan 501", async () => {
  resetServerSentenceStatus();

  const originalFetch = globalThis.fetch;
  let callCount = 0;

  // Mock fetch yang mengembalikan HTTP 501 Unsupported Method
  globalThis.fetch = async () => {
    callCount++;
    return {
      ok: false,
      status: 501,
      statusText: "Unsupported method ('POST')",
      json: async () => ({})
    };
  };

  try {
    // Panggilan pertama: mencoba server, menerima 501, beralih ke B0-local
    const res1 = await buildNaturalSentence(["SAYA", "MAKAN"], {
      apiBaseUrl: "http://localhost:8000",
      lang: "id"
    });
    assert.equal(callCount, 1, "Panggilan pertama memverifikasi endpoint");
    assert.equal(res1.source, "B0-local");

    // Panggilan kedua (seketika): circuit-breaker aktif, tidak boleh memanggil fetch lagi!
    const res2 = await buildNaturalSentence(["AIR", "MINUM"], {
      apiBaseUrl: "http://localhost:8000",
      lang: "id"
    });
    assert.equal(callCount, 1, "Circuit-breaker harus mencegah request POST berulang saat server 501");
    assert.equal(res2.source, "B0-local");
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test("buildNaturalSentence: sukses menggunakan server saat endpoint 200 OK", async () => {
  resetServerSentenceStatus();

  const originalFetch = globalThis.fetch;
  globalThis.fetch = async (url, opts) => {
    assert.ok(url.includes("/sentence"));
    assert.equal(opts.method, "POST");
    return {
      ok: true,
      status: 200,
      json: async () => ({
        gloss: "SAYA BELAJAR",
        text: "Saya sedang belajar bahasa isyarat di kelas.",
        model: "IndoT5-Server"
      })
    };
  };

  try {
    const res = await buildNaturalSentence(["SAYA", "BELAJAR"], {
      apiBaseUrl: "http://localhost:8080",
      lang: "id"
    });
    assert.equal(res.source, "IndoT5-Server");
    assert.equal(res.text, "Saya sedang belajar bahasa isyarat di kelas.");
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test("sentenceToConceptGlosses: konversi teks ucapan menjadi konsep isyarat", () => {
  const glosses = sentenceToConceptGlosses("Halo guru, saya mau belajar membaca buku");
  assert.ok(glosses.length >= 3);
  const bisindoNames = glosses.map((g) => g.bisindo);
  assert.ok(bisindoNames.includes("HALO"));
  assert.ok(bisindoNames.includes("GURU"));
  assert.ok(bisindoNames.includes("BELAJAR"));
});

