"""
signbridge.multimodal — Pipeline data & fitur untuk model fusion 4 modalitas (M6).

Empat modalitas per sampel (satu klip dari Perekam Dataset Multimodal):
  1. video  : keypoint 86 titik MediaPipe  -> tensor [64, 86, 3]
  2. citra  : foto crop tangan              -> tensor [3, 112, 112] (ImageNet-normalized)
  3. audio  : rekaman suara WAV             -> log-mel [64, 250] (16 kHz, 2,5 dtk)
  4. teks   : kalimat konteks / transkrip   -> id karakter [64]

Setiap sampel juga membawa `modality_mask` [4] (1 = modalitas tersedia, 0 = hilang),
sehingga model fusion tetap bisa dilatih & dipakai ketika sebagian modalitas tidak ada.

Modul di paket ini hanya bergantung pada NumPy (+ Pillow untuk citra) agar preprocessing
identik di pelatihan (PyTorch) maupun di server (onnxruntime), dan dapat diuji tanpa GPU.
"""

from signbridge.multimodal.constants import (  # noqa: F401
    MODALITIES,
    NUM_MODALITIES,
    AUDIO_SAMPLE_RATE,
    AUDIO_NUM_MELS,
    AUDIO_NUM_FRAMES,
    IMAGE_SIDE,
    TEXT_MAX_LEN,
)
