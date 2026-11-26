# Requirements — Rombak SignBridge-XMF (arahan Dosen, 26-11-2026)

1. **Satu sumber, modal berpasangan.** Video dan citra berasal dari klip WL-BISINDO yang sama (kunci signer/label/sample);
   audio dan teks dipasangkan di tingkat konsep. Alfabet: citra + landmark tangan dari foto yang sama.
2. **Ingestion & preprocessing bersamaan.** Satu perintah menghasilkan satu rekaman per sampel berisi keempat modal + mask.
3. **Satu model fusion.** Keempat modal masuk satu model (Cross-Modal Attention Fusion Transformer) yang tetap bekerja bila
   sebagian modal hilang.
4. **Label benar.** Label dibaca dari nama file; ketidakcocokan nama folder dilaporkan.
5. **Mode cicil.** Pipeline bisa dijalankan saat upload citra belum lengkap dan diulang secara inkremental.
6. **Evaluasi jujur.** Metrik utama V+I, protokol SD dan SI, ablation per subset modal.
7. **Akurat di browser.** Preprocessing numerik di dalam graf ONNX; paritas Python↔JS diuji; web memakai model XMF.
