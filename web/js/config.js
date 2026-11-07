/**
 * web/js/config.js
 * Konfigurasi kanonis & Database Lokal SignBridge ASEAN:
 * - 32 Konsep Bahasa Isyarat Ruang Kelas (BISINDO <-> FSL Filipina) sesuai data/bridge/concepts.csv
 * - 32 Parameter Fonologi Stokoe sesuai data/phonology.csv
 * - 26 Abjad Ejaan Jari (A-Z) sesuai web/model/fingerspell.json
 */

export const APP_CONFIG = {
  appName: "SignBridge ASEAN",
  version: "2.2.0",
  apiBaseUrl: "",
  studentModelUrl: "./model/student.onnx",
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

export const BISINDO_GLOSSES = [
  "HALO", "TERIMA_KASIH", "MAAF", "TOLONG",
  "SAYA", "KAMU", "GURU", "TEMAN",
  "MAU", "SUDAH", "BELUM", "BISA", "TIDAK", "ADA",
  "BELAJAR", "PAHAM", "TANYA", "BACA", "TULIS", "JAWAB",
  "BUKU", "TUGAS", "KELAS", "SEKOLAH",
  "APA", "SIAPA", "DIMANA", "KAPAN", "BAGAIMANA",
  "BAIK", "BENAR", "SALAH"
];

export const FINGERSPELL_LABELS = [
  "A", "B", "C", "D", "E", "F", "G", "H", "I", "J",
  "K", "L", "M", "N", "O", "P", "Q", "R", "S", "T",
  "U", "V", "W", "X", "Y", "Z"
];

/**
 * Database Fonologi 32 Kata Isyarat (Sinkron 100% dengan data/phonology.csv):
 * handshape: 0=Telapak Rapat(B), 1=Telunjuk(1), 2=Kepal(S), 3=Jempol(A/Thumb), 4=Kuncup(O), 5=Lima Jari Mekar(5), 6=Dua Jari(V), 7=Jempol+Kelingking(Y)
 * location : 0=Kepala/Dahi, 1=Mulut/Dagu, 2=Dada, 3=Ruang Netral Depan, 4=Dua Telapak Bertemu
 * movement : 0=Tahan Statis, 1=Maju/Naik, 2=Ayun Kiri-Kanan, 3=Angguk/Turun, 4=Putar/Buka-Tutup
 * two_handed: 0=Satu Tangan, 1=Dua Tangan
 */
export const PHONOLOGY_DB = {
  HALO:         { handshape: 0, location: 0, movement: 2, two_handed: 0, guide: "1 tangan telapak terbuka di samping kepala/dahi, lambaikan kiri-kanan" },
  TERIMA_KASIH: { handshape: 0, location: 1, movement: 1, two_handed: 0, guide: "1 tangan telapak rapat dari dagu/mulut digerakkan maju ke depan" },
  MAAF:         { handshape: 2, location: 2, movement: 4, two_handed: 0, guide: "1 tangan di depan dada dengan gerakan memutar" },
  TOLONG:       { handshape: 0, location: 4, movement: 1, two_handed: 1, guide: "2 tangan bertemu di depan dada lalu diangkat sedikit ke atas" },
  SAYA:         { handshape: 1, location: 2, movement: 0, two_handed: 0, guide: "1 tangan menunjuk/menyentuh dada sendiri (tahan)" },
  KAMU:         { handshape: 1, location: 3, movement: 1, two_handed: 0, guide: "1 tangan jari telunjuk menunjuk lurus ke depan" },
  GURU:         { handshape: 0, location: 0, movement: 1, two_handed: 1, guide: "2 tangan di samping pelipis/dahi digerakkan ke depan" },
  TEMAN:        { handshape: 1, location: 4, movement: 4, two_handed: 1, guide: "2 tangan jari telunjuk saling mengait di depan badan" },
  MAU:          { handshape: 5, location: 2, movement: 3, two_handed: 1, guide: "5 jari terbuka ditarik ke arah dada" },
  SUDAH:        { handshape: 0, location: 3, movement: 3, two_handed: 1, guide: "2 tangan telapak terbuka diayun turun (selesai)" },
  BELUM:        { handshape: 7, location: 3, movement: 2, two_handed: 0, guide: "1 tangan jempol+kelingking/telapak digoyangkan kiri-kanan" },
  BISA:         { handshape: 2, location: 3, movement: 3, two_handed: 1, guide: "2 tangan mengepal diayun mantap ke bawah" },
  TIDAK:        { handshape: 1, location: 3, movement: 2, two_handed: 0, guide: "1 tangan jari telunjuk digoyangkan kiri-kanan di depan" },
  ADA:          { handshape: 0, location: 3, movement: 3, two_handed: 0, guide: "1 tangan telapak terbuka diturunkan satu kali di depan" },
  BELAJAR:      { handshape: 5, location: 0, movement: 4, two_handed: 1, guide: "5 jari terbuka diangkat dari depan ke arah dahi" },
  PAHAM:        { handshape: 1, location: 0, movement: 3, two_handed: 0, guide: "1 tangan jari telunjuk di dekat pelipis/kepala" },
  TANYA:        { handshape: 1, location: 1, movement: 1, two_handed: 0, guide: "1 tangan telunjuk/5 jari dari dekat dagu melengkung ke depan" },
  BACA:         { handshape: 6, location: 4, movement: 2, two_handed: 1, guide: "2 jari (V) menyapu di atas telapak tangan satunya" },
  TULIS:        { handshape: 4, location: 4, movement: 2, two_handed: 1, guide: "Jari menguncup (memegang pena) menulis di atas telapak tangan" },
  JAWAB:        { handshape: 1, location: 1, movement: 1, two_handed: 1, guide: "2 jari telunjuk dari dekat mulut diarahkan ke depan" },
  BUKU:         { handshape: 0, location: 4, movement: 4, two_handed: 1, guide: "2 telapak tangan dirapatkan lalu dibuka seperti membuka buku" },
  TUGAS:        { handshape: 4, location: 4, movement: 3, two_handed: 1, guide: "2 tangan mengetuk punggung pergelangan tangan" },
  KELAS:        { handshape: 5, location: 3, movement: 4, two_handed: 1, guide: "2 tangan membentuk lingkaran ruang kelas di depan dada" },
  SEKOLAH:      { handshape: 0, location: 4, movement: 3, two_handed: 1, guide: "2 telapak tangan bertepuk dua kali secara lembut" },
  APA:          { handshape: 5, location: 3, movement: 2, two_handed: 1, guide: "2 tangan 5 jari terbuka menghadap atas digeser kiri-kanan" },
  SIAPA:        { handshape: 1, location: 1, movement: 4, two_handed: 0, guide: "1 jari telunjuk memutar kecil di dekat dagu/mulut" },
  DIMANA:       { handshape: 5, location: 3, movement: 2, two_handed: 0, guide: "1 tangan 5 jari terbuka digoyangkan kiri-kanan di ruang netral" },
  KAPAN:        { handshape: 6, location: 3, movement: 4, two_handed: 1, guide: "2 jari (V/telunjuk) memutar seperti jarum jam" },
  BAGAIMANA:    { handshape: 5, location: 3, movement: 4, two_handed: 1, guide: "2 tangan 5 jari terbuka diputar menghadap ke atas" },
  BAIK:         { handshape: 3, location: 3, movement: 0, two_handed: 0, guide: "1 tangan acungan jempol (Thumb-Up) di depan dada" },
  BENAR:        { handshape: 3, location: 3, movement: 3, two_handed: 0, guide: "1 tangan jempol/telunjuk dianggukkan mantap ke depan" },
  SALAH:        { handshape: 7, location: 1, movement: 2, two_handed: 0, guide: "Jempol & kelingking (Y) digoyangkan di dekat dagu/depan" }
};

export const CLASSROOM_CONCEPTS = [
  { id: "C01", category: "Sapaan", bisindo: "HALO", fsl: "HELLO", id_text: "Halo", fil_text: "Kumusta", en_text: "Hello", guide: PHONOLOGY_DB.HALO.guide },
  { id: "C02", category: "Sapaan", bisindo: "TERIMA_KASIH", fsl: "THANK_YOU", id_text: "Terima kasih", fil_text: "Salamat", en_text: "Thank you", guide: PHONOLOGY_DB.TERIMA_KASIH.guide },
  { id: "C03", category: "Sapaan", bisindo: "MAAF", fsl: "SORRY", id_text: "Maaf", fil_text: "Paumanhin", en_text: "Sorry", guide: PHONOLOGY_DB.MAAF.guide },
  { id: "C04", category: "Sapaan", bisindo: "TOLONG", fsl: "PLEASE_HELP", id_text: "Tolong", fil_text: "Tulong / Pakiusap", en_text: "Please / Help", guide: PHONOLOGY_DB.TOLONG.guide },

  { id: "C05", category: "Subjek", bisindo: "SAYA", fsl: "ME", id_text: "Saya", fil_text: "Ako", en_text: "I / Me", guide: PHONOLOGY_DB.SAYA.guide },
  { id: "C06", category: "Subjek", bisindo: "KAMU", fsl: "YOU", id_text: "Kamu", fil_text: "Ikaw", en_text: "You", guide: PHONOLOGY_DB.KAMU.guide },
  { id: "C07", category: "Subjek", bisindo: "GURU", fsl: "TEACHER", id_text: "Guru", fil_text: "Guro", en_text: "Teacher", guide: PHONOLOGY_DB.GURU.guide },
  { id: "C08", category: "Subjek", bisindo: "TEMAN", fsl: "FRIEND", id_text: "Teman", fil_text: "Kaibigan", en_text: "Friend", guide: PHONOLOGY_DB.TEMAN.guide },

  { id: "C09", category: "Modalitas", bisindo: "MAU", fsl: "WANT", id_text: "Ingin / Mau", fil_text: "Gusto", en_text: "Want", guide: PHONOLOGY_DB.MAU.guide },
  { id: "C10", category: "Modalitas", bisindo: "SUDAH", fsl: "ALREADY", id_text: "Sudah", fil_text: "Tapos na", en_text: "Already / Done", guide: PHONOLOGY_DB.SUDAH.guide },
  { id: "C11", category: "Modalitas", bisindo: "BELUM", fsl: "NOT_YET", id_text: "Belum", fil_text: "Hindi pa", en_text: "Not yet", guide: PHONOLOGY_DB.BELUM.guide },
  { id: "C12", category: "Modalitas", bisindo: "BISA", fsl: "CAN", id_text: "Bisa", fil_text: "Kaya / Pwede", en_text: "Can", guide: PHONOLOGY_DB.BISA.guide },
  { id: "C13", category: "Modalitas", bisindo: "TIDAK", fsl: "NO", id_text: "Tidak", fil_text: "Hindi", en_text: "No / Not", guide: PHONOLOGY_DB.TIDAK.guide },
  { id: "C14", category: "Modalitas", bisindo: "ADA", fsl: "HAVE", id_text: "Ada", fil_text: "Mayroon", en_text: "Have / There is", guide: PHONOLOGY_DB.ADA.guide },

  { id: "C15", category: "Aktivitas", bisindo: "BELAJAR", fsl: "STUDY", id_text: "Belajar", fil_text: "Mag-aral", en_text: "Study / Learn", guide: PHONOLOGY_DB.BELAJAR.guide },
  { id: "C16", category: "Aktivitas", bisindo: "PAHAM", fsl: "UNDERSTAND", id_text: "Paham / Mengerti", fil_text: "Naiintindihan", en_text: "Understand", guide: PHONOLOGY_DB.PAHAM.guide },
  { id: "C17", category: "Aktivitas", bisindo: "TANYA", fsl: "ASK", id_text: "Bertanya", fil_text: "Magtanong", en_text: "Ask", guide: PHONOLOGY_DB.TANYA.guide },
  { id: "C18", category: "Aktivitas", bisindo: "BACA", fsl: "READ", id_text: "Membaca", fil_text: "Magbasa", en_text: "Read", guide: PHONOLOGY_DB.BACA.guide },
  { id: "C19", category: "Aktivitas", bisindo: "TULIS", fsl: "WRITE", id_text: "Menulis", fil_text: "Magsulat", en_text: "Write", guide: PHONOLOGY_DB.TULIS.guide },
  { id: "C20", category: "Aktivitas", bisindo: "JAWAB", fsl: "ANSWER", id_text: "Menjawab", fil_text: "Sumagot", en_text: "Answer", guide: PHONOLOGY_DB.JAWAB.guide },

  { id: "C21", category: "Objek Kelas", bisindo: "BUKU", fsl: "BOOK", id_text: "Buku", fil_text: "Libro", en_text: "Book", guide: PHONOLOGY_DB.BUKU.guide },
  { id: "C22", category: "Objek Kelas", bisindo: "TUGAS", fsl: "ASSIGNMENT", id_text: "Tugas", fil_text: "Takdang-aralin", en_text: "Assignment", guide: PHONOLOGY_DB.TUGAS.guide },
  { id: "C23", category: "Objek Kelas", bisindo: "KELAS", fsl: "CLASS", id_text: "Kelas", fil_text: "Klase", en_text: "Class", guide: PHONOLOGY_DB.KELAS.guide },
  { id: "C24", category: "Objek Kelas", bisindo: "SEKOLAH", fsl: "SCHOOL", id_text: "Sekolah", fil_text: "Paaralan", en_text: "School", guide: PHONOLOGY_DB.SEKOLAH.guide },

  { id: "C25", category: "Tanya", bisindo: "APA", fsl: "WHAT", id_text: "Apa", fil_text: "Ano", en_text: "What", guide: PHONOLOGY_DB.APA.guide },
  { id: "C26", category: "Tanya", bisindo: "SIAPA", fsl: "WHO", id_text: "Siapa", fil_text: "Sino", en_text: "Who", guide: PHONOLOGY_DB.SIAPA.guide },
  { id: "C27", category: "Tanya", bisindo: "DIMANA", fsl: "WHERE", id_text: "Di mana", fil_text: "Saan", en_text: "Where", guide: PHONOLOGY_DB.DIMANA.guide },
  { id: "C28", category: "Tanya", bisindo: "KAPAN", fsl: "WHEN", id_text: "Kapan", fil_text: "Kailan", en_text: "When", guide: PHONOLOGY_DB.KAPAN.guide },
  { id: "C29", category: "Tanya", bisindo: "BAGAIMANA", fsl: "HOW", id_text: "Bagaimana", fil_text: "Paano", en_text: "How", guide: PHONOLOGY_DB.BAGAIMANA.guide },

  { id: "C30", category: "Evaluasi", bisindo: "BAIK", fsl: "GOOD", id_text: "Baik", fil_text: "Mabuti", en_text: "Good", guide: PHONOLOGY_DB.BAIK.guide },
  { id: "C31", category: "Evaluasi", bisindo: "BENAR", fsl: "CORRECT", id_text: "Benar", fil_text: "Tama", en_text: "Correct", guide: PHONOLOGY_DB.BENAR.guide },
  { id: "C32", category: "Evaluasi", bisindo: "SALAH", fsl: "WRONG", id_text: "Salah", fil_text: "Mali", en_text: "Wrong", guide: PHONOLOGY_DB.SALAH.guide }
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
