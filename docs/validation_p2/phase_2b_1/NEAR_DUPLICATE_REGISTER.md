# REGISTER KANDIDAT KEMIRIPAN LINTAS-SPLIT (NEAR-DUPLICATE REGISTER)
## SignBridge ASEAN — Modul Image I1 (BISINDO Alphabet)
### Status Klasifikasi: CROSS_SPLIT_SIMILARITY_CANDIDATE

> [!NOTE]
> **KETENTUAN METODOLOGI**: Pasangan citra dalam register ini diklasifikasikan secara formal sebagai **`CROSS_SPLIT_SIMILARITY_CANDIDATE`**.
> Dilarang secara sepihak menyatakan pasangan ini sebagai duplikat terkonfirmasi (*confirmed duplicate*) atau kebocoran peraga (*signer leakage*) definitif tanpa verifikasi manual oleh validator Tuli dan konfirmasi metadata peraga.

---

### 1. Ringkasan Kandidat Kemiripan Lintas-Split
Pada audit Phase 2A dan Phase 2B, ditemukan **enam pasangan citra antarsplit (Train vs Val/Test)** yang memiliki jarak hash persepsi sangat rendah (dHash $\le 4$, pHash $\le 12$) serta berasal dari perangkat dan sesi latar belakang yang sama.
Pasangan ini menunjukkan kemiripan visual yang sangat tinggi antara gestur M vs N dan U vs V yang terpisah di split yang berbeda pada model P1.

---

### 2. Tabel Register Kandidat Kemiripan Lintas-Split (6 Pasangan Kritis)

| Candidate ID | Pair Ref | Sampel Train (File & Label) | Sampel Val/Test (File & Label) | Split Komparasi | dHash | pHash | Inferensi Perangkat & Sesi | Klasifikasi Forensik Visual Phase 2A | Status Register |
| :---: | :---: | :--- | :--- | :---: | :---: | :---: | :--- | :--- | :---: |
| `CAND-DUP-01` | **P01** | `M_Bebas_Samsung_M51.jpg` (`M`) | `N_Bebas_Samsung_M51.jpg` (`N`) | Train vs Val | **1** | **9** | `Samsung_M51` (Sesi Bebas) | Gestur M (3 jari) vs N (2 jari) sangat mirip; latar belakang identik | `CROSS_SPLIT_SIMILARITY_CANDIDATE` |
| `CAND-DUP-02` | **P02** | `N_Polos Terang_Samsung_Galaxy A32 5G.jpg` (`N`) | `M_Polos Terang_Samsung_Galaxy A32 5G.jpg` (`M`) | Train vs Val | **2** | **9** | `Galaxy A32 5G` (Polos Terang) | Siluet tangan, pencahayaan, dan latar belakang hampir identik | `CROSS_SPLIT_SIMILARITY_CANDIDATE` |
| `CAND-DUP-03` | **P03** | `N_Wall Gray_Xiaomi_Redmi Note 9.jpg` (`N`) | `M_Wall Gray_Xiaomi_Redmi Note 9.jpg` (`M`) | Train vs Val | **3** | **6** | `Redmi Note 9` (Wall Gray) | Dinding abu-abu dan pose peraga dari sesi pemotretan berturutan | `CROSS_SPLIT_SIMILARITY_CANDIDATE` |
| `CAND-DUP-04` | **P07** | `V_Body Red_Xiaomi_Redmi Note 9.jpg` (`V`) | `U_Body Red_Xiaomi_Redmi Note 9.jpg` (`U`) | Train vs Test | **4** | **3** | `Redmi Note 9` (Body Red) | Kerapatan dua jari pada U dan V hampir identik (pHash hanya 3) | `CROSS_SPLIT_SIMILARITY_CANDIDATE` |
| `CAND-DUP-05` | **P08** | `N_Polos Terang_Samsung_A53 5G.jpg` (`N`) | `M_Polos Terang_Samsung_A53 5G.jpg` (`M`) | Train vs Test | **4** | **6** | `Samsung_A53 5G` (Polos Terang) | Peraga yang sama memperagakan N di Train dan M di Test | `CROSS_SPLIT_SIMILARITY_CANDIDATE` |
| `CAND-DUP-06` | **P09** | `U_polos gelap_Iphone_13promax.jpg` (`U`) | `V_polos gelap_Iphone_13promax.jpg` (`V`) | Train vs Test | **4** | **12** | `Iphone 13 Pro Max` (Polos Gelap) | Siluet dua jari tegak sangat identik dengan latar belakang gelap sama | `CROSS_SPLIT_SIMILARITY_CANDIDATE` |

---

### 3. Analisis Hubungan terhadap Kebocoran Evaluasi (Evaluation Leakage)
1. **Kebocoran Antara Train dan Validation (P01, P02, P03)**:
   - Mengakibatkan metriks validasi selama pelatihan P1 mengalami *optimistic bias* karena model mengenali latar belakang dan fitur tangan peraga yang sama.
2. **Kebocoran Antara Train dan Test (P07, P08, P09)**:
   - Menyebabkan evaluasi generalisasi pada test set P1 tidak sepenuhnya independen terhadap variasi sesi.
3. **Rekomendasi Tata Kelola Dataset P2**:
   - Seluruh pasangan dalam register ini **wajib dimasukkan ke dalam kelompok split yang sama** melalui strategi *Device/Session-Grouped Splitting*.
   - Tidak ada sampel yang dihapus atau dipindahkan pada fase read-only saat ini.