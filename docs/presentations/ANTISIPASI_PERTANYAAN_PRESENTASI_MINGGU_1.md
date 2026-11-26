# PANDUAN LENGKAP ANTISIPASI PERTANYAAN & JAWABAN (Q&A DEFENSE)
## Presentasi Progres Minggu 1 — Proyek SignBridge ID–PH (BISINDO ↔ FSL)
*Mata Kuliah: Machine Learning (Semester 5) — Projek 1*

Dokumen ini disusun untuk mempersiapkan seluruh anggota tim pengembang (**Farrel, Jonnathan, Gloria**) menghadapi sesi tanya jawab dengan **Dosen Penguji / Pembimbing** dan **Teman-teman Mahasiswa**.

---

## DAFTAR KATEGORI PERTANYAAN

- [BAGIAN 1: Pertanyaan Dosen — Metodologi, Validitas Data & Evaluasi ML](#bagian-1-pertanyaan-dosen--metodologi-validitas-data--evaluasi-ml)
- [BAGIAN 2: Pertanyaan Dosen — Arsitektur Model, Komputasi & Deployment](#bagian-2-pertanyaan-dosen--arsitektur-model-komputasi--deployment)
- [BAGIAN 3: Pertanyaan Dosen — Ruang Lingkup, Kelayakan (Feasibility) & Bahasa Isyarat](#bagian-3-pertanyaan-dosen--ruang-lingkup-kelayakan-feasibility--bahasa-isyarat)
- [BAGIAN 4: Pertanyaan Teman — Teknis Implementasi, Deployment Browser & Coding](#bagian-4-pertanyaan-teman--teknis-implementasi-deployment-browser--coding)
- [BAGIAN 5: Pertanyaan Teman — Edge Cases, User Experience & Cara Pakai](#bagian-5-pertanyaan-teman--edge-cases-user-experience--cara-pakai)

---

## BAGIAN 1: Pertanyaan Dosen — Metodologi, Validitas Data & Evaluasi ML

### Q1.1 (Dosen): *"Akurasi data uji kalian mencapai 99.13%. Bukankah angka ini mencurigakan untuk model isyarat di minggu pertama? Apakah model kalian tidak overfit?"*
* **Tingkat Bahaya:** 🔴 Sangat Kritis (Pertanyaan jebakan validitas evaluasi).
* **Poin Kunci:** Akui dengan jujur bahwa angka tersebut berasal dari partisi *Signer-Dependent*, tunjukkan bahwa tim sudah melakukan audit internal, dan paparkan solusi partisi *Leave-One-Signer-Out (LOSO)* di minggu kedua.
* **Jawaban yang Diucapkan:**
  > *"Terima kasih atas pertanyaannya, Bapak/Ibu. Pertanyaan ini sangat krusial dan persis seperti temuan audit internal kami di Slide 9. Angka 99.13% tersebut diperoleh dari partisi **Signer-Dependent**, di mana 5 orang penutur isyarat yang sama terdistribusi merata di data latih (960 klip) dan data uji (460 klip).*
  > 
  > *Model Transformer kami sangat efektif dalam memetakan relasi spasial, namun akibatnya model cenderung menghafal ciri fisik dan proporsi tubuh dari 5 penutur tersebut. Ketika kami uji coba langsung di webcam oleh anggota tim yang belum pernah ada di dataset, kami menemukan adanya penurunan keyakinan prediksi akibat domain shift.*
  > 
  > *Oleh karena itu, kami tidak berpuas diri dengan angka 99.13% ini. Di minggu kedua, kami mewajibkan protokol evaluasi **Signer-Independent (LOSO)**: Signer 1, 2, dan 3 murni untuk pelatihan, Signer 0 untuk validasi, dan Signer 4 sebagai unseen test set. Target akurasi Signer-Independent realistis kami berada di angka $\ge 82\%$."*

---

### Q1.2 (Dosen): *"Mengapa model abjad (fingerspelling) MobileNetV3 kalian menghasilkan akurasi hanya 3.85%? Apa penyebabnya dan bagaimana penanganannya?"*
* **Tingkat Bahaya:** 🔴 Kritis (Menguji pemahaman terhadap kegagalan training).
* **Poin Kunci:** Jelaskan angka $3.85\%$ secara matematis ($1/26 = 0.03846$ alias *random guessing*), sebutkan diagnosis akar masalah (learning rate / unnormalized inputs), dan jelaskan *safety fallback* yang dibuat frontend.
* **Jawaban yang Diucapkan:**
  > *"Berdasarkan file log eksperimen kami di `runs/image_i1_mobilenetv3/result.json`, akurasi 3.85% tersebut persis sama dengan nilai peluang acak untuk 26 kelas abjad, yaitu $1 / 26 = 3.846\%$. Ini menandakan model mengalami **training collapse** (gradien tidak konvergen).*
  > 
  > *Setelah kami telusuri, penyebab utamanya adalah learning rate awal yang terlalu agresif sehingga bobot konvolusi terjebak pada loss plateau, ditambah belum diterapkannya standardisasi mean dan standard deviation ImageNet pada input crop citra 224x224.*
  > 
  > *Sebagai mitigasi agar aplikasi web tetap bisa mendeteksi abjad di minggu pertama, tim frontend membuat fallback sementara menggunakan aturan geometri sendi jari MediaPipe (`classifyAlphabetGeometry`). Di minggu kedua, kami akan memperbaiki skrip pelatihan dengan optimizer AdamW, learning rate $1\times 10^{-4}$, dan scheduler Cosine Annealing."*

---

### Q1.3 (Dosen): *"Dataset kalian hanya memiliki 1.600 video dari 5 orang signer. Apakah jumlah sampel ini cukup untuk melatih model deep learning sebesar 1,3 juta parameter?"*
* **Tingkat Bahaya:** 🟡 Sedang (Menguji pemahaman kapasitas model vs ukuran data).
* **Poin Kunci:** Jelaskan bahwa input bukan piksel mentah melainkan 86 koordinat skeletal yang sudah dinormalisasi, jelaskan teknik kompresi dimensi, dan rencana augmentasi 3D.
* **Jawaban yang Diucapkan:**
  > *"Jika kita melatih model video RGB dari piksel mentah (seperti 3D-CNN atau VideoMAE), 1.600 klip jelas sangat kurang dan pasti overfit parah. Namun pada SignBridge, kami tidak memproses piksel gambar utuh, melainkan **86 koordinat skeletal yang telah diekstraksi oleh MediaPipe**.*
  > 
  > *Dimensi input kami telah tereduksi dari jutaan piksel menjadi hanya $86 \times 3 = 258$ nilai float per frame. Arsitektur M0 Student Transformer kami juga sangat ringkas (hanya 2 layer encoder dengan embedding dimension 128 dan total 1,33 juta parameter).*
  > 
  > *Selain itu, untuk memperkaya variasi data pada minggu kedua, kami menerapkan **augmentasi koordinat 3D** di pipeline DataLoader: random spatial scaling antara 85%–115%, rotasi sumbu bahu $\pm 10^\circ$, penambahan Gaussian jitter pada sendi jari, serta temporal speed perturbation. Dengan augmentasi ini, variasi efektif data latih meningkat lebih dari 4 kali lipat."*

---

### Q1.4 (Dosen): *"Bagaimana kalian menangani perbedaan panjang durasi isyarat antar-video? Ada orang yang memperagakan isyarat cepat (15 frame), ada yang lambat (90 frame)?"*
* **Poin Kunci:** Jelaskan pemangkasan frame pasif (*trim inactive frames*) dan teknik *uniform linear temporal resampling* ke tepat 64 frame (Kontrak 2 & 3).
* **Jawaban yang Diucapkan:**
  > *"Kami menerapkan standarisasi temporal dua tahap di `signbridge/features.py` dan `web/js/features.js`:*
  > 1. *Tahap pertama adalah **Trim Inactive Frames**: Kami menghitung magnitude kecepatan gerak pergelangan tangan. Frame di awal dan di akhir video di mana tangan masih diam di bawah dipangkas.*
  > 2. *Tahap kedua adalah **Uniform Linear Resampling**: Sekuens frame dinamis (berapapun panjangnya, $T$) diinterpolasi secara linear pada domain waktu menjadi tepat $T = 64$ frame.*
  > 
  > *Dengan panjang sekuens yang tepat 64 frame, input tensor yang masuk ke model ONNX selalu berdimensi konsisten `[1, 64, 86, 3]` tanpa memerlukan padding nol yang bisa merusak kalkulasi self-attention."*

---

## BAGIAN 2: Pertanyaan Dosen — Arsitektur Model, Komputasi & Deployment

### Q2.1 (Dosen): *"Mengapa kalian memilih pendekatan skeletal MediaPipe + Transformer/ST-GCN daripada langsung menggunakan model Vision Transformer (seperti VideoMAE atau TimeSformer) langsung dari frame video?"*
* **Tingkat Bahaya:** 🔴 Kritis (Alasan mendasar pemilihan arsitektur).
* **Poin Kunci:** Latensi browser edge ($< 50\text{ ms}$), ketiadaan GPU diskrit pada laptop sekolah, dan privasi siswa.
* **Jawaban yang Diucapkan:**
  > *"Keputusan ini didasari oleh prinsip rekayasa sistem yang kami tetapkan di awal: **zero cloud cost, browser-first, dan inklusivitas perangkat**.*
  > 
  > *Model Vision Transformer berbasis video RGB seperti VideoMAE membutuhkan komputasi lebih dari 150 GFLOPs per klip dan memori GPU dedicated yang besar. Jika dijalankan di browser laptop atau Chromebook standar sekolah tanpa kartu grafis dedicated, inferensi akan menghasilkan lag parah (di bawah 2 FPS) dan membebani memori laptop siswa.*
  > 
  > *Dengan menggunakan MediaPipe Holistic yang diakselerasi WebGL 2.0, ekstraksi pose selesai dalam 22 ms, dan model Student Transformer M0 kami yang hanya 1,3 juta parameter selesai dieksekusi oleh ONNX WebAssembly hanya dalam **11,2 milidetik pada CPU biasa**. Total waktu proses hanya 34 ms (29 FPS), sekaligus menjamin privasi siswa karena frame kamera tidak pernah diunggah ke internet."*

---

### Q2.2 (Dosen): *"Apa perbedaan mendasar antara model M0 (Student Pose Transformer) dan M1 (ST-GCN), dan mengapa M0 yang dipilih untuk deployment web?"*
* **Poin Kunci:** Jelaskan perbedaan mekanisme pemodelan spasial (Self-Attention vs Graph Convolution dengan Adjacency Matrix) dan efisiensi eksekusi runtime WebAssembly.
* **Jawaban yang Diucapkan:**
  > *"Perbedaan mendasarnya terletak pada cara pemodelan topologi sendi tubuh:*
  > * **M1 (ST-GCN):** Menggunakan graf fisik anatomis eksplisit dengan matriks ketetanggaan 3-partisi (centripetal, centrifugal, dan root). Model ini sangat kokoh secara struktur biologis, tetapi membutuhkan representasi tensor graf dan konvolusi spasial-temporal yang lebih kompleks.*
  > * **M0 (Student Pose Transformer):** Memproyeksikan seluruh 86 titik koordinat ke dalam ruang vektor laten 128 dimensi, lalu menggunakan multi-head self-attention untuk membiarkan model mempelajari korelasi bebas antar-sendi tubuh secara dinamis.*
  > 
  > *Keduanya menghasilkan akurasi yang sama-sama tinggi pada data uji ($99.13\%$), namun M0 dipilih sebagai model utama web karena graf komputasinya jauh lebih linear dan ramah dioptimasi oleh runtime ONNX WebAssembly (latensi inferensi M0 hanya 11,2 ms berbanding sekitar 18,5 ms pada ST-GCN)."*

---

### Q2.3 (Dosen): *"Bagaimana kalian menjamin bahwa model yang ditraining di PyTorch akan menghasilkan angka yang sama persis saat dijalankan di browser via JavaScript?"*
* **Poin Kunci:** Sebutkan Kontrak Antarmuka 2 dan 3, pengujian paritas numerik otomatis (`test_contract_2_model_io.py` dan `tests/js/parity.test.mjs`), serta toleransi error $< 1\times 10^{-4}$.
* **Jawaban yang Diucapkan:**
  > *"Kami menerapkan prinsip Continuous Integration yang sangat ketat melalui **Kontrak Antarmuka 2 dan 3**:*
  > 1. *Untuk preprocessing, kami memiliki automated unit test di `tests/js/parity.test.mjs`. Tes ini mengalirkan data koordinat sintetik yang sama ke modul Python (`features.py`) dan modul JavaScript (`features.js`), lalu memverifikasi bahwa selisih absolut maksimum antar koordinat lebih kecil dari $1\times 10^{-5}$.*
  > 2. *Untuk model ONNX, script ekspor kami di `signbridge/export_onnx.py` secara otomatis membandingkan output logits PyTorch dengan output ONNX Runtime. Hasil verifikasi pada model M0 menunjukkan selisih presisi mengambang maksimum hanya sebesar $2.4\times 10^{-6}$.*
  > 
  > *Dengan demikian, kami menjamin secara matematis bahwa tidak ada perbedaan perilaku antara fase pelatihan di server dan fase inferensi di browser."*

---

### Q2.4 (Dosen): *"Di Slide 9 kalian menyebutkan tentang 'Fake INT8 Quantization'. Apa maksudnya?"*
* **Poin Kunci:** Jelaskan bahwa file `student_int8.onnx` di disk ternyata memiliki SHA-256 dan ukuran (5,46 MB) yang persis sama dengan model FP32, dan sebutkan rencana kuantisasi dinamis nyata.
* **Jawaban yang Diucapkan:**
  > *"Maksud dari temuan tersebut adalah transparansi teknis. Pada dokumentasi awal tim, ditargetkan model terkuantisasi INT8 berukuran sekitar 1,4 MB. Namun saat kami melakukan audit integritas file dan pengecekan hash SHA-256 pada file `web/model/student_int8.onnx`, kami menemukan bahwa file tersebut ternyata masih berupa salinan biner FP32 dengan ukuran 5,46 MB (hash SHA-256 identik dengan `student.onnx`).*
  > 
  > *Artinya, kuantisasi dinamis baru disiapkan di fungsi ekspor tetapi belum dieksekusi secara aktual pada biner produksi web. Pada roadmap Minggu 2 (P1), Gloria akan menjalankan tool `onnxruntime.quantization.quantize_dynamic` untuk memangkas ukuran biner menjadi $\approx 1,4\text{ MB}$ agar proses download awal di browser pengguna jauh lebih cepat."*

---

## BAGIAN 3: Pertanyaan Dosen — Ruang Lingkup, Kelayakan (Feasibility) & Bahasa Isyarat

### Q3.1 (Dosen): *"Proyek kalian berjudul BISINDO ↔ FSL (Filipino Sign Language) dengan 4 modalitas, tetapi saat ini kalian baru memiliki 32 kata BISINDO dan FSL belum ada. Apakah proyek ini terlalu muluk-muluk (overambitious) untuk 1 semester?"*
* **Tingkat Bahaya:** 🔴 Kritis (Menguji manajemen risiko dan scoping proyek).
* **Poin Kunci:** Jelaskan pendekatan bertahap (*modular iterative development*): pondasi core engine dibangun di BISINDO terlebih dahulu, FSL diintegrasikan via konsep jembatan L1 (Kamus Konsep Semantik), dan speech/NLP dibangun di atas interface yang sudah siap.
* **Jawaban yang Diucapkan:**
  > *"Kekhawatiran Bapak/Ibu sangat beralasan. Oleh karena itu, strategi rekayasa kami menggunakan pendekatan **Modular Milestone Development**:*
  > * *Fase 1 (Minggu 1–2): Fokus penuh menyelesaikan 'Core Vision Engine' pada 32 kata kosakata kelas BISINDO dan 26 abjad sampai terbukti stabil dan tahan terhadap variasi penutur.*
  > * *Fase 2 (Minggu 3): Menghubungkan modul NLP dan Speech menggunakan interface yang sudah kami siapkan di Kontrak 6.*
  > * *Fase 3 (Jembatan FSL): Kami tidak melatih model FSL dari nol secara terpisah. Kami menggunakan arsitektur **Jembatan 3 Lapis**: Lapis 1 adalah tabel pemetaan konsep semantik (`concepts.csv`) yang mencocokkan ID konsep BISINDO dengan FSL (misal konsep 'TERIMA KASIH' di BISINDO langsung dipetakan ke konsep 'SALAMAT/THANK YOU' di FSL).*
  > 
  > *Dengan pemisahan modul yang jelas ini, sistem inti kami tetap memiliki deliverable fungsional yang kuat meskipun jika dataset FSL baru diuji pada skala kamus konsep."*

---

### Q3.2 (Dosen): *"Mengapa kosakata yang dipilih hanya 32 kata? Apakah 32 kata ini cukup representatif untuk percakapan di ruang kelas?"*
* **Poin Kunci:** Jelaskan bahwa 32 kata ini adalah set kosakata standar dari WL-BISINDO yang merepresentasikan konsep inti kelas inklusif (kata ganti, kata tanya, instruksi belajar, kata benda kelas), dan kata-kata di luar 32 kata ini ditangani oleh modalitas ejaan abjad (fingerspelling).
* **Jawaban yang Diucapkan:**
  > *"32 kata pada dataset WL-BISINDO ini dipilih secara cermat berdasarkan frekuensi penggunaannya di ruang kelas inklusif:*
  > * *Kata Ganti:* `SAYA`, `KAMU`, `TEMAN`, `GURU`.
  > * *Kata Tanya:* `APA`, `BAGAIMANA`, `MANA`.
  > * *Aktivitas Belajar:* `BELAJAR`, `BUKU`, `BANTU`, `BISA`, `KERJA`, `SEKOLAH`.
  > * *Sopan Santun & Sosial:* `MAAF`, `TERIMA_KASIH`, `SAMA`.
  > 
  > *Tentu 32 kata belum mencakup seluruh leksikon bahasa Indonesia. Namun strategi kami adalah **sistem hibrida**: kata-kata umum dikenali secara instan melalui model isyarat dinamis (M0), sedangkan nama orang, istilah ilmiah, atau kata khusus yang belum ada di kamus dapat dieja huruf demi huruf menggunakan modalitas fingerspelling abjad A–Z."*

---

### Q3.3 (Dosen): *"Bagaimana sistem kalian membedakan antara orang yang sedang diam/istirahat dengan orang yang benar-benar sedang memperagakan isyarat?"*
* **Poin Kunci:** Jelaskan fitur *Signing Space Guard* dan *Two-Tier Dynamic Thresholding* di `recognizer.js`.
* **Jawaban yang Diucapkan:**
  > *"Kami menerapkan dua lapisan penyaring (filtering) di `web/js/recognizer.js`:*
  > 1. *Lapisan Spasial (**Signing Space Guard**): Secara linguistik bahasa isyarat, isyarat BISINDO dilakukan di dalam 'ruang isyarat' antara batas atas kepala hingga pinggang. Jika kedua tangan pengguna terdeteksi berada di bawah pinggang (area istirahat), buffer inferensi langsung diabaikan.*
  > 2. *Lapisan Probabilistik (**Confidence & Margin Threshold**): Prediksi hanya dinyatakan valid jika probabilitas top-1 $\ge 0.45$ DAN selisih antara probabilitas top-1 dengan top-2 (margin) $\ge 0.10$. Jika gerakannya ambigu atau transisi acak, margin akan kecil dan sistem menolak prediksi tersebut sebagai noise."*

---

## BAGIAN 4: Pertanyaan Teman — Teknis Implementasi, Deployment Browser & Coding

### Q4.1 (Teman): *"Gimana caranya kalian bisa ngejalanin model deep learning PyTorch langsung di browser tanpa backend Python/Flask/Django?"*
* **Poin Kunci:** Jelaskan proses ekspor ONNX $\to$ runtime ONNX Web (`ort.min.js`) $\to$ backend WebAssembly SIMD.
* **Jawaban yang Diucapkan:**
  > *"Kuncinya ada di format **ONNX (Open Neural Network Exchange)**. Model PyTorch yang dilatih Jonnathan diekspor menggunakan fungsi `torch.onnx.export` menjadi file biner `.onnx`.*
  > 
  > *Di browser, kami menggunakan library resmi Microsoft bernama `onnxruntime-web`. Library ini membaca file `.onnx` dan mengompilasinya menjadi instruksi **WebAssembly (WASM)** dengan instruksi paralel SIMD. Jadi komputasi matriksnya dieksekusi langsung oleh CPU komputer kalian di dalam tab browser, persis seperti menjalankan program C++ di laptop kalian tanpa perlu menghubungi server sama sekali."*

---

### Q4.2 (Teman): *"Library MediaPipe Holistic itu kan output-nya ada 543 titik. Gimana cara kalian membuang titik-titik yang nggak kepakai dan menyusunnya jadi 86 titik?"*
* **Poin Kunci:** Jelaskan pemetaan indeks array yang didefinisikan di `signbridge/constants.py` dan array mapping di `web/js/config.js`.
* **Jawaban yang Diucapkan:**
  > *"MediaPipe Holistic menghasilkan 4 objek koordinat terpisah: pose (33 titik), tangan kiri (21 titik), tangan kanan (21 titik), dan face mesh (468 titik). Totalnya 543 titik.*
  > 
  > *Di file `signbridge/constants.py`, kami membuat array indeks seleksi:*
  > * *Untuk pose:* kami hanya mengambil 11 titik tubuh bagian atas (bahu, siku, pergelangan tangan, dan pinggul), membuang lutut dan kaki.*
  > * *Untuk tangan:* kami ambil lengkap 21 titik tangan kiri dan 21 titik tangan kanan.*
  > * *Untuk wajah:* kami hanya menyeleksi 33 titik yang mewakili bentuk bibir, alis, dan kontur mata (karena ekspresi wajah adalah penanda gramatikal pada bahasa isyarat).*
  > 
  > *Indeks ini disusun berurutan sehingga menghasilkan matriks shape `[86, 3]` yang identik di Python maupun JavaScript."*

---

### Q4.3 (Teman): *"Kalian bagi tugas bertiga (Farrel, Jonnathan, Gloria) lewat Git. Gimana caranya supaya nggak sering merge conflict pas ngerjain bareng?"*
* **Poin Kunci:** Pemisahan folder modular, kepatuhan pada 6 kontrak antarmuka, dan testing otomatis sebelum commit.
* **Jawaban yang Diucapkan:**
  > *"Strategi kami adalah pemisahan domain kerja berdasarkan struktur direktori:*
  > * *Farrel fokus di direktori `signbridge/data/` dan skrip preprocessing.*
  > * *Jonnathan fokus di direktori `signbridge/models/` dan skrip pelatihan deep learning.*
  > * *Gloria fokus di direktori `signbridge/export/`, notebook evaluasi, server backend `server/`, serta integrasi browser di `web/`.*
  > 
  > *Titik temu kode kami diatur oleh **6 Kontrak Antarmuka**. Selama tidak ada yang mengubah nama fungsi atau bentuk tensor yang sudah disepakati di kontrak, kode kami bisa berkembang secara paralel tanpa pernah bentrok di Git."*

---

### Q4.4 (Teman): *"Kenapa kalian nggak pakai TensorFlow.js (tfjs) aja yang biasanya lebih populer buat AI di browser?"*
* **Poin Kunci:** Ekosistem PyTorch lebih modern, ONNX Runtime Web lebih cepat dalam eksekusi Transformer, dan ukuran runtime lebih ringan.
* **Jawaban yang Diucapkan:**
  > *"Kami sempat mempertimbangkan TF.js, tapi kami memilih ONNX Runtime Web karena tiga alasan utama:*
  > 1. *Mayoritas riset state-of-the-art bahasa isyarat dan graf saat ini dikembangkan dengan **PyTorch**. Mengonversi PyTorch ke ONNX jauh lebih mulus dan stabil dibanding mengonversi PyTorch ke format Layers Model TF.js.*
  > 2. *ONNX Runtime Web memiliki backend WebAssembly SIMD yang sangat cepat dan teroptimasi khusus untuk arsitektur berbasis Transformer.*
  > 3. *Ukuran runtime library ONNX Web lebih kompak, sehingga waktu loading halaman web pertama kali menjadi jauh lebih singkat."*

---

## BAGIAN 5: Pertanyaan Teman — Edge Cases, User Experience & Cara Pakai

### Q5.1 (Teman): *"Gimana kalau penggunanya kidal (tangan dominannya tangan kiri)? Apakah modelnya tetap bisa mendeteksi isyaratnya?"*
* **Poin Kunci:** Jelaskan representasi 86 titik saat ini (memiliki tangan kiri dan kanan) serta rencana augmentasi *horizontal flip* di minggu kedua.
* **Jawaban yang Diucapkan:**
  > *"Ini pertanyaan yang sangat menarik! Pada arsitektur kami, kedua tangan (21 titik kiri dan 21 titik kanan) diproses secara bersamaan dalam topologi 86 node.*
  > 
  > *Untuk isyarat yang menggunakan dua tangan (dua-tangan simetris), sistem tidak terpengaruh kidal atau tidak. Namun untuk isyarat satu-tangan dominan, model saat ini lebih banyak melihat contoh tangan kanan di dataset WL-BISINDO.*
  > 
  > *Solusi yang sedang diimplementasikan Farrel di minggu kedua adalah **Augmentasi Horizontal Flip**: koordinat sumbu X dibalik dan indeks tangan kiri ditukar dengan tangan kanan ($X_{\text{flip}} = -X$). Dengan cara ini, model otomatis belajar bahwa memperagakan isyarat dengan tangan kiri adalah ekuivalen secara semantik dengan tangan kanan."*

---

### Q5.2 (Teman): *"Kalau pencahayaan di ruangan agak gelap atau background di belakang orangnya ramai, apakah pengenalannya bakal rusak?"*
* **Poin Kunci:** Jelaskan keunggulan representasi skeletal koordinat vs piksel RGB mentah, serta ketahanan MediaPipe terhadap background.
* **Jawaban yang Diucapkan:**
  > *"Inilah salah satu keuntungan terbesar menggunakan representasi skeletal keypoints dibanding memproses piksel gambar secara langsung.*
  > 
  > *Model deep learning kami (M0) hanya menerima koordinat $X, Y, Z$. Selama model deteksi MediaPipe di lapisan terdepan masih bisa mengidentifikasi sendi tubuh, variasi warna dinding, orang yang berjalan di belakang, atau perubahan warna baju **sama sekali tidak mempengaruhi model M0** karena seluruh informasi background sudah tereliminasi.*
  > 
  > *Namun jika ruangan terlalu gelap gulita sampai kamera tidak bisa melihat tangan, MediaPipe akan menurunkan nilai visibility titik, dan sistem kami secara aman akan menampilkan peringatan di layar bahwa pose belum terdeteksi sempurna."*

---

### Q5.3 (Teman): *"Bagaimana cara sistem tahu kapan suatu kata selesai dan kata berikutnya dimulai saat pengguna memperagakan isyarat secara bersambung?"*
* **Poin Kunci:** Jelaskan sistem *sliding window buffer*, deteksi batas isyarat via kecepatan tangan, dan FIFO de-duplication di `sentence.js`.
* **Jawaban yang Diucapkan:**
  > *"Sistem kami menggunakan mekanisme **Sliding Window Buffer** dengan de-duplikasi:*
  > 1. *Frame koordinat terus dimasukkan ke buffer geser berkapasitas 64–96 frame.*
  > 2. *Ketika isyarat selesai, tangan biasanya mengalami penurunan kecepatan sesaat atau kembali ke posisi netral.*
  > 3. *Modul `sentence.js` memiliki filter debounce: jika model memprediksi kata yang sama secara beruntun dalam rentang 1,5 detik (misalnya 'MAKAN', 'MAKAN', 'MAKAN'), sistem menggabungkannya menjadi satu kata tunggal 'MAKAN'. Kata baru hanya akan dicatat jika ada transisi jeda atau perubahan kelas isyarat yang melewati ambang margin."*

---

### Q5.4 (Teman): *"Laptop aku speknya biasa aja (Core i3 tanpa VGA). Apakah bakal lag kalau buka SignBridge?"*
* **Poin Kunci:** Jelaskan profil latensi riil $34,4\text{ ms}$ di browser biasa, penggunaan 1-thread WASM, dan ketiadaan kebutuhan GPU diskrit.
* **Jawaban yang Diucapkan:**
  > *"Sama sekali tidak lag. Kami sengaja merancang sistem ini agar dapat berjalan di laptop sekolah standar.*
  > 
  > *MediaPipe Holistic berjalan menggunakan akselerasi WebGL standar yang didukung oleh semua GPU terintegrasi (Intel UHD Graphics bawaan processor), sedangkan model Student Transformer M0 kami hanya membutuhkan 1 thread CPU WebAssembly dan memakan waktu sekitar **11 milidetik per prediksi**.*
  > 
  > *Total waktu komputasi sekitar 34 milidetik, yang berarti laptop Core i3 sekalipun dapat menjalankannya dengan mulus di kisaran 25–30 FPS tanpa membuat kipas laptop berisik."*

---

## RINGKASAN STRATEGI MENJAWAB UNTUK SETIAP ANGGOTA TIM

Agar pembagian suara saat presentasi dan tanya jawab terlihat solid dan kompak di depan dosen:

| Anggota Tim | Domain Pertanyaan Utama | Rekomendasi Jawaban |
| :--- | :--- | :--- |
| **Farrel** | Preprocessing, Dataset, Normalisasi Bahu, Augmentasi, Hand Crop | Tangani Q1.3, Q1.4, Q4.2, Q5.1 |
| **Jonnathan** | Arsitektur M0/M1, Model Training, ST-GCN vs Transformer, Loss | Tangani Q1.1, Q2.1, Q2.2 |
| **Gloria (KarinaGlo)** | Evaluasi, Paritas PyTorch-ONNX, Kuantisasi INT8, Web WASM/WebGL, Frontend PWA, Speech/NLP, & Backend FastAPI | Tangani Q1.2, Q2.3, Q2.4, Q3.1, Q3.3, Q4.1, Q4.3, Q5.2, Q5.3, Q5.4 |

---
*Dokumen ini telah disimpan di `docs/presentations/ANTISIPASI_PERTANYAAN_PRESENTASI_MINGGU_1.md`. Bawa dokumen ini atau buka di ponsel/laptop saat sesi presentasi untuk referensi cepat.*

