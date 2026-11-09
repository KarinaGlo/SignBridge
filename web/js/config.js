/**
 * web/js/config.js
 * Konfigurasi kanonis & Database Lokal SignBridge ASEAN:
 * - 32 Kosakata Utama Model M0 WL-BISINDO (Tervalidasi 100% dengan best_model.pt & manifest_wl_bisindo.csv)
 * - Metadata Padanan Bahasa Isyarat Ruang Kelas & FSL Filipina
 * - 26 Abjad Ejaan Jari (A-Z) sesuai web/model/fingerspell.json
 */

export const APP_CONFIG = {
  appName: "SignBridge ASEAN",
  version: "2.3.0",
  apiBaseUrl: "",
  studentModelUrl: "./model/student.onnx",
  // CATATAN AUDIT TEKNIS: student_int8.onnx saat ini adalah salinan unquantized FP32.
  // Jangan digunakan sebagai representasi kuantisasi INT8 nyata hingga kuantisasi offline selesai.
  studentInt8ModelUrl: "./model/student_int8.onnx",
  labelsUrl: "./model/labels.json",
  fingerspellModelUrl: "./model/fingerspell.onnx",
  fingerspellLabelsUrl: "./model/fingerspell.json",
  seqLen: 64,
  numNodes: 86,
  numCoords: 3,
  cropSize: 224,
  motionStartThreshold: 0.012,
  motionStopThreshold: 0.007,
  minActiveFrames: 7,
  holdFramesToClassify: 10,
  maxActiveFrames: 36,
  pauseFramesToClassify: 5,
  confidenceThreshold: 0.55
};

/**
 * 32 Kosakata WL-BISINDO resmi hasil training M0 Student Baseline.
 * Indeks 0..31 terikat ketat (strictly synchronized) dengan neuron output [1, 32] pada student.onnx:
 * 0: AIR, 1: BELAJAR, ..., 31: MALAM.
 */
export const BISINDO_GLOSSES = [
  "AIR",          // Idx 0
  "BELAJAR",      // Idx 1
  "CARI",         // Idx 2
  "HARI",         // Idx 3
  "INGAT",        // Idx 4
  "LAGI",         // Idx 5
  "MAAF",         // Idx 6
  "MAKAN",        // Idx 7
  "MOTOR",        // Idx 8
  "SAYA",         // Idx 9
  "TERIMA_KASIH", // Idx 10
  "TULI",         // Idx 11
  "APA",          // Idx 12
  "SIAPA",        // Idx 13
  "KAPAN",        // Idx 14
  "DIMANA",       // Idx 15
  "MENGAPA",      // Idx 16
  "BAGAIMANA",    // Idx 17
  "MERAH",        // Idx 18
  "KUNING",       // Idx 19
  "HIJAU",        // Idx 20
  "HITAM",        // Idx 21
  "DENGAR",       // Idx 22
  "BERANGKAT",    // Idx 23
  "DATANG",       // Idx 24
  "TEMAN",        // Idx 25
  "KELUARGA",     // Idx 26
  "RUMAH",        // Idx 27
  "PAGI",         // Idx 28
  "SIANG",        // Idx 29
  "SORE",         // Idx 30
  "MALAM"         // Idx 31
];

export const FINGERSPELL_LABELS = [
  "A", "B", "C", "D", "E", "F", "G", "H", "I", "J",
  "K", "L", "M", "N", "O", "P", "Q", "R", "S", "T",
  "U", "V", "W", "X", "Y", "Z"
];

/**
 * Database Fonologi Stokoe (data/phonology.csv).
 * PERHATIAN: Pada arsitektur inferensi baru, fonologi Stokoe HANYA digunakan
 * sebagai anotasi fitur diagnostik (auxiliary metadata) dan TIDAK DIGUNAKAN
 * untuk menentukan/mengubah prediksi probabilitas neural network M0.
 */
export const PHONOLOGY_DB = {
  // 32 Kosakata WL-BISINDO M0
  AIR:          { handshape: 0, location: 1, movement: 3, two_handed: 0, guide: "Mengetuk atau mengarahkan jari W/tangan di dekat bibir/dagu" },
  BELAJAR:      { handshape: 5, location: 0, movement: 4, two_handed: 1, guide: "5 jari terbuka diangkat dari depan ke arah dahi" },
  CARI:         { handshape: 4, location: 0, movement: 4, two_handed: 0, guide: "Jari membentuk lingkaran huruf C berputar kecil di depan mata" },
  HARI:         { handshape: 0, location: 3, movement: 1, two_handed: 0, guide: "Tangan membentuk lengkungan melambangkan perjalanan matahari" },
  INGAT:        { handshape: 1, location: 0, movement: 0, two_handed: 0, guide: "Ujung jari telunjuk menyentuh pelipis lalu bergerak mantap" },
  LAGI:         { handshape: 0, location: 4, movement: 3, two_handed: 1, guide: "Dua telapak/ujung jari dipertemukan berulang di depan dada" },
  MAAF:         { handshape: 2, location: 2, movement: 4, two_handed: 0, guide: "1 tangan di depan dada dengan gerakan memutar" },
  MAKAN:        { handshape: 4, location: 1, movement: 3, two_handed: 0, guide: "Tangan menguncup digerakkan berulang mendekati mulut" },
  MOTOR:        { handshape: 2, location: 3, movement: 4, two_handed: 1, guide: "Dua tangan mengepal memegang stang dan memutar gas motor" },
  SAYA:         { handshape: 1, location: 2, movement: 0, two_handed: 0, guide: "1 tangan menunjuk/menyentuh dada sendiri (tahan)" },
  TERIMA_KASIH: { handshape: 0, location: 1, movement: 1, two_handed: 0, guide: "1 tangan telapak rapat dari dagu/mulut digerakkan maju ke depan" },
  TULI:         { handshape: 1, location: 0, movement: 3, two_handed: 0, guide: "Telunjuk menyentuh telinga lalu bergerak ke arah mulut atau dada" },
  APA:          { handshape: 5, location: 3, movement: 2, two_handed: 1, guide: "2 tangan 5 jari terbuka menghadap atas digeser kiri-kanan" },
  SIAPA:        { handshape: 1, location: 1, movement: 4, two_handed: 0, guide: "1 jari telunjuk memutar kecil di dekat dagu/mulut" },
  KAPAN:        { handshape: 6, location: 3, movement: 4, two_handed: 1, guide: "2 jari (V/telunjuk) memutar melingkar seperti jarum jam" },
  DIMANA:       { handshape: 5, location: 3, movement: 2, two_handed: 0, guide: "1 tangan 5 jari terbuka digoyangkan kiri-kanan di ruang netral" },
  MENGAPA:      { handshape: 5, location: 0, movement: 1, two_handed: 0, guide: "Jari menyentuh dahi lalu ditarik membuka membentuk tanya" },
  BAGAIMANA:    { handshape: 5, location: 3, movement: 4, two_handed: 1, guide: "2 tangan 5 jari terbuka diputar menghadap ke atas" },
  MERAH:        { handshape: 1, location: 1, movement: 3, two_handed: 0, guide: "Ujung telunjuk mengusap bibir bawah (melambangkan merah)" },
  KUNING:       { handshape: 7, location: 3, movement: 2, two_handed: 0, guide: "Bentuk tangan huruf Y digetarkan lembut di depan dada" },
  HIJAU:        { handshape: 0, location: 3, movement: 2, two_handed: 0, guide: "Bentuk tangan huruf H/G digetarkan di depan badan" },
  HITAM:        { handshape: 1, location: 0, movement: 2, two_handed: 0, guide: "Telunjuk mengusap kening/alis mendatar (melambangkan hitam)" },
  DENGAR:       { handshape: 1, location: 0, movement: 0, two_handed: 0, guide: "Telunjuk atau telapak tangan didekatkan ke daun telinga" },
  BERANGKAT:    { handshape: 0, location: 3, movement: 1, two_handed: 1, guide: "Dua tangan meluncur dari dekat badan mengarah ke depan/luar" },
  DATANG:       { handshape: 1, location: 3, movement: 1, two_handed: 1, guide: "Dua telunjuk melengkung ditarik dari arah depan mendekati tubuh" },
  TEMAN:        { handshape: 1, location: 4, movement: 4, two_handed: 1, guide: "2 tangan jari telunjuk saling mengait di depan badan" },
  KELUARGA:     { handshape: 4, location: 4, movement: 4, two_handed: 1, guide: "Dua tangan membentuk huruf F atau lingkaran bertemu di depan dada" },
  RUMAH:        { handshape: 0, location: 4, movement: 0, two_handed: 1, guide: "Dua telapak tangan membentuk segitiga atap rumah di depan dada" },
  PAGI:         { handshape: 0, location: 3, movement: 1, two_handed: 1, guide: "Satu tangan terbit naik dari balik lengan telapak yang mendatar" },
  SIANG:        { handshape: 0, location: 3, movement: 0, two_handed: 0, guide: "Lengan berdiri tegak lurus ke atas melambangkan matahari di puncak" },
  SORE:         { handshape: 0, location: 3, movement: 3, two_handed: 0, guide: "Lengan condong turun melambangkan matahari mulai terbenam" },
  MALAM:        { handshape: 0, location: 3, movement: 3, two_handed: 1, guide: "Satu telapak tangan melengkung turun menutupi lengan bawah (gelap)" },

  // Konsep Ruang Kelas Tambahan (Disimpan untuk backward compatibility glosarium)
  HALO:         { handshape: 0, location: 0, movement: 2, two_handed: 0, guide: "1 tangan telapak terbuka di samping kepala/dahi, lambaikan kiri-kanan" },
  TOLONG:       { handshape: 0, location: 4, movement: 1, two_handed: 1, guide: "2 tangan bertemu di depan dada lalu diangkat sedikit ke atas" },
  KAMU:         { handshape: 1, location: 3, movement: 1, two_handed: 0, guide: "1 tangan jari telunjuk menunjuk lurus ke depan" },
  GURU:         { handshape: 0, location: 0, movement: 1, two_handed: 1, guide: "2 tangan di samping pelipis/dahi digerakkan ke depan" },
  MAU:          { handshape: 5, location: 2, movement: 3, two_handed: 1, guide: "5 jari terbuka ditarik ke arah dada" },
  SUDAH:        { handshape: 0, location: 3, movement: 3, two_handed: 1, guide: "2 tangan telapak terbuka diayun turun (selesai)" },
  BELUM:        { handshape: 7, location: 3, movement: 2, two_handed: 0, guide: "1 tangan jempol+kelingking/telapak digoyangkan kiri-kanan" },
  BISA:         { handshape: 2, location: 3, movement: 3, two_handed: 1, guide: "2 tangan mengepal diayun mantap ke bawah" },
  TIDAK:        { handshape: 1, location: 3, movement: 2, two_handed: 0, guide: "1 tangan jari telunjuk digoyangkan kiri-kanan di depan" },
  ADA:          { handshape: 0, location: 3, movement: 3, two_handed: 0, guide: "1 tangan telapak terbuka diturunkan satu kali di depan" },
  PAHAM:        { handshape: 1, location: 0, movement: 3, two_handed: 0, guide: "1 tangan jari telunjuk di dekat pelipis/kepala" },
  TANYA:        { handshape: 1, location: 1, movement: 1, two_handed: 0, guide: "1 tangan telunjuk/5 jari dari dekat dagu melengkung ke depan" },
  BACA:         { handshape: 6, location: 4, movement: 2, two_handed: 1, guide: "2 jari (V) menyapu di atas telapak tangan satunya" },
  TULIS:        { handshape: 4, location: 4, movement: 2, two_handed: 1, guide: "Jari menguncup (memegang pena) menulis di atas telapak tangan" },
  JAWAB:        { handshape: 1, location: 1, movement: 1, two_handed: 1, guide: "2 jari telunjuk dari dekat mulut diarahkan ke depan" },
  BUKU:         { handshape: 0, location: 4, movement: 4, two_handed: 1, guide: "2 telapak tangan dirapatkan lalu dibuka seperti membuka buku" },
  TUGAS:        { handshape: 4, location: 4, movement: 3, two_handed: 1, guide: "2 tangan mengetuk punggung pergelangan tangan" },
  KELAS:        { handshape: 5, location: 3, movement: 4, two_handed: 1, guide: "2 tangan membentuk lingkaran ruang kelas di depan dada" },
  SEKOLAH:      { handshape: 0, location: 4, movement: 3, two_handed: 1, guide: "2 telapak tangan bertepuk dua kali secara lembut" },
  BAIK:         { handshape: 3, location: 3, movement: 0, two_handed: 0, guide: "1 tangan acungan jempol (Thumb-Up) di depan dada" },
  BENAR:        { handshape: 3, location: 3, movement: 3, two_handed: 0, guide: "1 tangan jempol/telunjuk dianggukkan mantap ke depan" },
  SALAH:        { handshape: 7, location: 1, movement: 2, two_handed: 0, guide: "Jempol & kelingking (Y) digoyangkan di dekat dagu/depan" }
};

/**
 * Daftar Konsep Bahasa Isyarat SignBridge:
 * - 32 Kosakata WL-BISINDO didukung penuh oleh model inferensi M0 (supported: true).
 * - Konsep ruang kelas lainnya ditandai secara transparan (supported: false) sebagai roadmap M2/Ekspansi.
 */
export const CLASSROOM_CONCEPTS = [
  // --- 32 Kosakata Utama Model M0 (WL-BISINDO) ---
  { id: "M01", category: "Kebutuhan", bisindo: "AIR", fsl: "WATER", id_text: "Air", fil_text: "Tubig", en_text: "Water", supported: true, guide: PHONOLOGY_DB.AIR.guide },
  { id: "M02", category: "Aktivitas", bisindo: "BELAJAR", fsl: "STUDY", id_text: "Belajar", fil_text: "Mag-aral", en_text: "Study", supported: true, guide: PHONOLOGY_DB.BELAJAR.guide },
  { id: "M03", category: "Aktivitas", bisindo: "CARI", fsl: "SEARCH", id_text: "Mencari", fil_text: "Maghanap", en_text: "Search", supported: true, guide: PHONOLOGY_DB.CARI.guide },
  { id: "M04", category: "Waktu", bisindo: "HARI", fsl: "DAY", id_text: "Hari", fil_text: "Araw", en_text: "Day", supported: true, guide: PHONOLOGY_DB.HARI.guide },
  { id: "M05", category: "Kognitif", bisindo: "INGAT", fsl: "REMEMBER", id_text: "Ingat", fil_text: "Matandaan", en_text: "Remember", supported: true, guide: PHONOLOGY_DB.INGAT.guide },
  { id: "M06", category: "Kuantitas", bisindo: "LAGI", fsl: "AGAIN", id_text: "Lagi / Ulangi", fil_text: "Muli", en_text: "Again", supported: true, guide: PHONOLOGY_DB.LAGI.guide },
  { id: "M07", category: "Sapaan", bisindo: "MAAF", fsl: "SORRY", id_text: "Maaf", fil_text: "Paumanhin", en_text: "Sorry", supported: true, guide: PHONOLOGY_DB.MAAF.guide },
  { id: "M08", category: "Aktivitas", bisindo: "MAKAN", fsl: "EAT", id_text: "Makan", fil_text: "Kumain", en_text: "Eat", supported: true, guide: PHONOLOGY_DB.MAKAN.guide },
  { id: "M09", category: "Transportasi", bisindo: "MOTOR", fsl: "MOTORCYCLE", id_text: "Sepeda Motor", fil_text: "Motorsiklo", en_text: "Motorcycle", supported: true, guide: PHONOLOGY_DB.MOTOR.guide },
  { id: "M10", category: "Subjek", bisindo: "SAYA", fsl: "ME", id_text: "Saya", fil_text: "Ako", en_text: "I / Me", supported: true, guide: PHONOLOGY_DB.SAYA.guide },
  { id: "M11", category: "Sapaan", bisindo: "TERIMA_KASIH", fsl: "THANK_YOU", id_text: "Terima kasih", fil_text: "Salamat", en_text: "Thank you", supported: true, guide: PHONOLOGY_DB.TERIMA_KASIH.guide },
  { id: "M12", category: "Identitas", bisindo: "TULI", fsl: "DEAF", id_text: "Tuli / Tunarungu", fil_text: "Bingi", en_text: "Deaf", supported: true, guide: PHONOLOGY_DB.TULI.guide },
  { id: "M13", category: "Tanya", bisindo: "APA", fsl: "WHAT", id_text: "Apa", fil_text: "Ano", en_text: "What", supported: true, guide: PHONOLOGY_DB.APA.guide },
  { id: "M14", category: "Tanya", bisindo: "SIAPA", fsl: "WHO", id_text: "Siapa", fil_text: "Sino", en_text: "Who", supported: true, guide: PHONOLOGY_DB.SIAPA.guide },
  { id: "M15", category: "Tanya", bisindo: "KAPAN", fsl: "WHEN", id_text: "Kapan", fil_text: "Kailan", en_text: "When", supported: true, guide: PHONOLOGY_DB.KAPAN.guide },
  { id: "M16", category: "Tanya", bisindo: "DIMANA", fsl: "WHERE", id_text: "Di mana", fil_text: "Saan", en_text: "Where", supported: true, guide: PHONOLOGY_DB.DIMANA.guide },
  { id: "M17", category: "Tanya", bisindo: "MENGAPA", fsl: "WHY", id_text: "Mengapa", fil_text: "Bakit", en_text: "Why", supported: true, guide: PHONOLOGY_DB.MENGAPA.guide },
  { id: "M18", category: "Tanya", bisindo: "BAGAIMANA", fsl: "HOW", id_text: "Bagaimana", fil_text: "Paano", en_text: "How", supported: true, guide: PHONOLOGY_DB.BAGAIMANA.guide },
  { id: "M19", category: "Warna", bisindo: "MERAH", fsl: "RED", id_text: "Merah", fil_text: "Pula", en_text: "Red", supported: true, guide: PHONOLOGY_DB.MERAH.guide },
  { id: "M20", category: "Warna", bisindo: "KUNING", fsl: "YELLOW", id_text: "Kuning", fil_text: "Dilaw", en_text: "Yellow", supported: true, guide: PHONOLOGY_DB.KUNING.guide },
  { id: "M21", category: "Warna", bisindo: "HIJAU", fsl: "GREEN", id_text: "Hijau", fil_text: "Berde", en_text: "Green", supported: true, guide: PHONOLOGY_DB.HIJAU.guide },
  { id: "M22", category: "Warna", bisindo: "HITAM", fsl: "BLACK", id_text: "Hitam", fil_text: "Itim", en_text: "Black", supported: true, guide: PHONOLOGY_DB.HITAM.guide },
  { id: "M23", category: "Indera", bisindo: "DENGAR", fsl: "HEAR", id_text: "Mendengar", fil_text: "Makinig", en_text: "Hear", supported: true, guide: PHONOLOGY_DB.DENGAR.guide },
  { id: "M24", category: "Aktivitas", bisindo: "BERANGKAT", fsl: "DEPART", id_text: "Berangkat", fil_text: "Umalis", en_text: "Depart", supported: true, guide: PHONOLOGY_DB.BERANGKAT.guide },
  { id: "M25", category: "Aktivitas", bisindo: "DATANG", fsl: "ARRIVE", id_text: "Datang", fil_text: "Dumating", en_text: "Arrive", supported: true, guide: PHONOLOGY_DB.DATANG.guide },
  { id: "M26", category: "Sosial", bisindo: "TEMAN", fsl: "FRIEND", id_text: "Teman", fil_text: "Kaibigan", en_text: "Friend", supported: true, guide: PHONOLOGY_DB.TEMAN.guide },
  { id: "M27", category: "Sosial", bisindo: "KELUARGA", fsl: "FAMILY", id_text: "Keluarga", fil_text: "Pamilya", en_text: "Family", supported: true, guide: PHONOLOGY_DB.KELUARGA.guide },
  { id: "M28", category: "Tempat", bisindo: "RUMAH", fsl: "HOUSE", id_text: "Rumah", fil_text: "Bahay", en_text: "House", supported: true, guide: PHONOLOGY_DB.RUMAH.guide },
  { id: "M29", category: "Waktu", bisindo: "PAGI", fsl: "MORNING", id_text: "Pagi", fil_text: "Umaga", en_text: "Morning", supported: true, guide: PHONOLOGY_DB.PAGI.guide },
  { id: "M30", category: "Waktu", bisindo: "SIANG", fsl: "NOON", id_text: "Siang", fil_text: "Tanghali", en_text: "Noon", supported: true, guide: PHONOLOGY_DB.SIANG.guide },
  { id: "M31", category: "Waktu", bisindo: "SORE", fsl: "EVENING", id_text: "Sore", fil_text: "Hapon", en_text: "Evening", supported: true, guide: PHONOLOGY_DB.SORE.guide },
  { id: "M32", category: "Waktu", bisindo: "MALAM", fsl: "NIGHT", id_text: "Malam", fil_text: "Gabi", en_text: "Night", supported: true, guide: PHONOLOGY_DB.MALAM.guide },

  // --- Konsep Ruang Kelas Tambahan (Belum Didukung Model M0 - Target Roadmap M2) ---
  { id: "C01", category: "Sapaan", bisindo: "HALO", fsl: "HELLO", id_text: "Halo", fil_text: "Kumusta", en_text: "Hello", supported: false, guide: PHONOLOGY_DB.HALO.guide },
  { id: "C04", category: "Sapaan", bisindo: "TOLONG", fsl: "PLEASE_HELP", id_text: "Tolong", fil_text: "Tulong", en_text: "Please / Help", supported: false, guide: PHONOLOGY_DB.TOLONG.guide },
  { id: "C06", category: "Subjek", bisindo: "KAMU", fsl: "YOU", id_text: "Kamu", fil_text: "Ikaw", en_text: "You", supported: false, guide: PHONOLOGY_DB.KAMU.guide },
  { id: "C07", category: "Subjek", bisindo: "GURU", fsl: "TEACHER", id_text: "Guru", fil_text: "Guro", en_text: "Teacher", supported: false, guide: PHONOLOGY_DB.GURU.guide },
  { id: "C09", category: "Modalitas", bisindo: "MAU", fsl: "WANT", id_text: "Ingin / Mau", fil_text: "Gusto", en_text: "Want", supported: false, guide: PHONOLOGY_DB.MAU.guide },
  { id: "C10", category: "Modalitas", bisindo: "SUDAH", fsl: "ALREADY", id_text: "Sudah", fil_text: "Tapos na", en_text: "Already / Done", supported: false, guide: PHONOLOGY_DB.SUDAH.guide },
  { id: "C11", category: "Modalitas", bisindo: "BELUM", fsl: "NOT_YET", id_text: "Belum", fil_text: "Hindi pa", en_text: "Not yet", supported: false, guide: PHONOLOGY_DB.BELUM.guide },
  { id: "C12", category: "Modalitas", bisindo: "BISA", fsl: "CAN", id_text: "Bisa", fil_text: "Kaya", en_text: "Can", supported: false, guide: PHONOLOGY_DB.BISA.guide },
  { id: "C13", category: "Modalitas", bisindo: "TIDAK", fsl: "NO", id_text: "Tidak", fil_text: "Hindi", en_text: "No / Not", supported: false, guide: PHONOLOGY_DB.TIDAK.guide },
  { id: "C14", category: "Modalitas", bisindo: "ADA", fsl: "HAVE", id_text: "Ada", fil_text: "Mayroon", en_text: "Have", supported: false, guide: PHONOLOGY_DB.ADA.guide },
  { id: "C16", category: "Aktivitas", bisindo: "PAHAM", fsl: "UNDERSTAND", id_text: "Paham / Mengerti", fil_text: "Naiintindihan", en_text: "Understand", supported: false, guide: PHONOLOGY_DB.PAHAM.guide },
  { id: "C17", category: "Aktivitas", bisindo: "TANYA", fsl: "ASK", id_text: "Bertanya", fil_text: "Magtanong", en_text: "Ask", supported: false, guide: PHONOLOGY_DB.TANYA.guide },
  { id: "C18", category: "Aktivitas", bisindo: "BACA", fsl: "READ", id_text: "Membaca", fil_text: "Magbasa", en_text: "Read", supported: false, guide: PHONOLOGY_DB.BACA.guide },
  { id: "C19", category: "Aktivitas", bisindo: "TULIS", fsl: "WRITE", id_text: "Menulis", fil_text: "Magsulat", en_text: "Write", supported: false, guide: PHONOLOGY_DB.TULIS.guide },
  { id: "C20", category: "Aktivitas", bisindo: "JAWAB", fsl: "ANSWER", id_text: "Menjawab", fil_text: "Sumagot", en_text: "Answer", supported: false, guide: PHONOLOGY_DB.JAWAB.guide },
  { id: "C21", category: "Objek Kelas", bisindo: "BUKU", fsl: "BOOK", id_text: "Buku", fil_text: "Libro", en_text: "Book", supported: false, guide: PHONOLOGY_DB.BUKU.guide },
  { id: "C22", category: "Objek Kelas", bisindo: "TUGAS", fsl: "ASSIGNMENT", id_text: "Tugas", fil_text: "Takdang-aralin", en_text: "Assignment", supported: false, guide: PHONOLOGY_DB.TUGAS.guide },
  { id: "C23", category: "Objek Kelas", bisindo: "KELAS", fsl: "CLASS", id_text: "Kelas", fil_text: "Klase", en_text: "Class", supported: false, guide: PHONOLOGY_DB.KELAS.guide },
  { id: "C24", category: "Objek Kelas", bisindo: "SEKOLAH", fsl: "SCHOOL", id_text: "Sekolah", fil_text: "Paaralan", en_text: "School", supported: false, guide: PHONOLOGY_DB.SEKOLAH.guide },
  { id: "C30", category: "Evaluasi", bisindo: "BAIK", fsl: "GOOD", id_text: "Baik", fil_text: "Mabuti", en_text: "Good", supported: false, guide: PHONOLOGY_DB.BAIK.guide },
  { id: "C31", category: "Evaluasi", bisindo: "BENAR", fsl: "CORRECT", id_text: "Benar", fil_text: "Tama", en_text: "Correct", supported: false, guide: PHONOLOGY_DB.BENAR.guide },
  { id: "C32", category: "Evaluasi", bisindo: "SALAH", fsl: "WRONG", id_text: "Salah", fil_text: "Mali", en_text: "Wrong", supported: false, guide: PHONOLOGY_DB.SALAH.guide }
];

/**
 * Database 26 Abjad Ejaan Jari (A-Z) BISINDO & FSL sesuai web/model/fingerspell.json
 */
export const FINGERSPELL_DB = [
  { letter: "A", guide: "Kepalkan keempat jari, ibu jari menempel tegak di sisi telunjuk", example_id: "Aku / Ada", example_fil: "Ako / Araw" },
  { letter: "B", guide: "Keempat jari lurus rapat ke atas, ibu jari ditekuk melintang di telapak", example_id: "Buku / Belajar", example_fil: "Basa / Bukas" },
  { letter: "C", guide: "Kelima jari melengkung membentuk setengah lingkaran huruf C", example_id: "Cerdas / Cari", example_fil: "Klase" },
  { letter: "D", guide: "Jari telunjuk lurus ke atas, ujung ibu jari menyentuh jari tengah-manis-kelingking", example_id: "Duduk / Dengar", example_fil: "Dito /oo" },
  { letter: "E", guide: "Keempat ujung jari ditekuk rapat menyentuh ibu jari di tengah telapak", example_id: "Empat / Eja", example_fil: "Eskwela" },
  { letter: "F", guide: "Ujung ibu jari & telunjuk bertemu (OK), tiga jari lainnya lurus terbuka ke atas", example_id: "Fokus / Foto", example_fil: "Filipino" },
  { letter: "G", guide: "Jari telunjuk dan ibu jari menunjuk mendatar sejajar ke samping", example_id: "Guru / Gambar", example_fil: "Guro / Gusto" },
  { letter: "H", guide: "Jari telunjuk dan jari tengah lurus rapat menunjuk mendatar ke samping", example_id: "Halo / Hari", example_fil: "Hindi / Hapon" },
  { letter: "I", guide: "Hanya jari kelingking lurus ke atas, empat jari lainnya mengepal", example_id: "Ibu / Ini", example_fil: "Ikaw / Isa" },
  { letter: "J", guide: "Jari kelingking lurus lalu digerakkan melengkung membentuk kait huruf J", example_id: "Jawab / Jam", example_fil: "Diyan" },
  { letter: "K", guide: "Telunjuk & jari tengah lurus terbuka, ibu jari menyentuh pangkal jari tengah", example_id: "Kelas / Kamu", example_fil: "Klase / Kaibigan" },
  { letter: "L", guide: "Jari telunjuk lurus ke atas dan ibu jari terbuka ke samping membentuk siku L", example_id: "Lima / Lihat", example_fil: "Libro / Lima" },
  { letter: "M", guide: "Ibu jari diselipkan di bawah tiga jari (telunjuk, tengah, manis) yang menangkup", example_id: "Maaf / Mau", example_fil: "Mabuti / Mali" },
  { letter: "N", guide: "Ibu jari diselipkan di bawah dua jari (telunjuk dan jari tengah)", example_id: "Nama / Nanti", example_fil: "Naiintindihan" },
  { letter: "O", guide: "Ujung kelima jari dipertemukan membentuk bulatan huruf O", example_id: "Orang / Oke", example_fil: "Oo / Oras" },
  { letter: "P", guide: "Bentuk huruf K (telunjuk & tengah) diarahkan menunjuk miring ke bawah", example_id: "Paham / Pagi", example_fil: "Paaralan / Paano" },
  { letter: "Q", guide: "Telunjuk dan ibu jari (bentuk G) diarahkan menunjuk ke bawah", example_id: "Quran / Quiz", example_fil: "Quiz" },
  { letter: "R", guide: "Jari telunjuk dan jari tengah lurus disilangkan", example_id: "Rumah / Ruang", example_fil: "Respeto" },
  { letter: "S", guide: "Kepalan tangan penuh dengan ibu jari mengunci di depan keempat jari", example_id: "Saya / Sekolah", example_fil: "Salamat / Sino" },
  { letter: "T", guide: "Kepalan tangan dengan ibu jari terselip di antara jari telunjuk dan jari tengah", example_id: "Teman / Tugas", example_fil: "Tama / Tulong" },
  { letter: "U", guide: "Jari telunjuk dan jari tengah lurus rapat berdampingan ke atas", example_id: "Ujian / Untuk", example_fil: "Umaga / Upo" },
  { letter: "V", guide: "Jari telunjuk dan jari tengah lurus merenggang membentuk huruf V", example_id: "Video / Visual", example_fil: "Boses" },
  { letter: "W", guide: "Tiga jari (telunjuk, tengah, manis) lurus merenggang membentuk huruf W", example_id: "Waktu / Warna", example_fil: "Wika / Wala" },
  { letter: "X", guide: "Jari telunjuk ditekuk membentuk kait, jari lainnya mengepal", example_id: "Silang / X", example_fil: "Ekis" },
  { letter: "Y", guide: "Ibu jari dan jari kelingking dibuka lebar, tiga jari tengah mengepal", example_id: "Ya / Yang", example_fil: "Yung / Oo" },
  { letter: "Z", guide: "Jari telunjuk lurus menggambar garis zig-zag huruf Z di udara", example_id: "Zaman / Zona", example_fil: "Zero" }
];
