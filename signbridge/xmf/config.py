"""
signbridge/xmf/config.py — Kontrak tunggal SignBridge-XMF (Cross-Modal Attention Fusion).

SATU sumber kebenaran untuk:
  * daftar kelas (32 gloss WL-BISINDO resmi + 26 huruf alfabet),
  * cara membaca label dari NAMA FILE (bukan nama folder — lihat catatan di bawah),
  * bentuk tensor ke-4 modalitas yang masuk ke model fusion,
  * bank teks & ucapan (audio) per konsep.

CATATAN PENTING (audit 26-11-2026):
  Folder `citra/` di Google Drive diberi nama gloss yang TIDAK sesuai label resmi WL-BISINDO
  (mis. folder `apa` berisi `signer4_label0_*` padahal label 0 = AIR; folder `apa_kabar` berisi
  `label1` = BELAJAR). Karena itu label SELALU diambil dari pola `label{N}` di nama file dan
  dipetakan lewat `GLOSSES` (urutan resmi dataset WL-BISINDO, Kindy dkk., 2025).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Modalitas (urutan TETAP: indeks dipakai modality_mask & modality_weights)
# ---------------------------------------------------------------------------
MODALITIES: List[str] = ["video", "image", "audio", "text"]
NUM_MODALITIES = len(MODALITIES)
M_VIDEO, M_IMAGE, M_AUDIO, M_TEXT = range(4)

# ---------------------------------------------------------------------------
# Kelas
# ---------------------------------------------------------------------------
# Urutan resmi WL-BISINDO (label 0..31) — identik dengan signbridge.constants.BISINDO_32_GLOSSES
GLOSSES: List[str] = [
    "AIR", "BELAJAR", "CARI", "HARI", "INGAT", "LAGI", "MAAF", "MAKAN",
    "MOTOR", "SAYA", "TERIMA_KASIH", "TULI", "APA", "SIAPA", "KAPAN", "DIMANA",
    "MENGAPA", "BAGAIMANA", "MERAH", "KUNING", "HIJAU", "HITAM", "DENGAR", "BERANGKAT",
    "DATANG", "TEMAN", "KELUARGA", "RUMAH", "PAGI", "SIANG", "SORE", "MALAM",
]
LETTERS: List[str] = [chr(ord("A") + i) for i in range(26)]


def classes_for(task: str) -> List[str]:
    if task == "gloss":
        return GLOSSES
    if task == "alphabet":
        return LETTERS
    raise ValueError(f"task tidak dikenal: {task!r} (pakai 'gloss' atau 'alphabet')")


# ---------------------------------------------------------------------------
# Bentuk tensor per tugas (dipakai model, dataset, ekspor ONNX, dan web/js/xmf.js)
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class TaskShapes:
    pose_frames: int      # T  : panjang deret keypoint
    pose_tokens: int      # token keluaran encoder video
    image_frames: int     # F  : jumlah citra per sampel
    image_side: int = 112
    audio_samples: int = 40_000   # 2,5 dtk @ 16 kHz (mentah; log-mel dihitung DI DALAM model)
    text_len: int = 64


SHAPES: Dict[str, TaskShapes] = {
    # 1 klip isyarat = 64 frame keypoint + 16 frame citra dari klip YANG SAMA
    "gloss": TaskShapes(pose_frames=64, pose_tokens=16, image_frames=16),
    # 1 foto huruf = 1 "frame" landmark tangan + 1 crop tangan dari foto YANG SAMA
    "alphabet": TaskShapes(pose_frames=1, pose_tokens=1, image_frames=1),
}

NUM_NODES, NUM_COORDS = 86, 3
AUDIO_SR = 16_000
IMAGENET_MEAN = (0.485, 0.456, 0.406)
IMAGENET_STD = (0.229, 0.224, 0.225)

# Crop badan-atas berpanduan pose (Python preprocess.py == web/js/xmf.js personCropBox)
PERSON_CROP_SIDE_X_SHOULDER = 3.6    # sisi kotak = 3,6 x lebar bahu
PERSON_CROP_CENTER_SHIFT = 0.35      # pusat digeser ke bawah 0,35 x lebar bahu (ruang isyarat)

# ---------------------------------------------------------------------------
# Pembacaan nama file
# ---------------------------------------------------------------------------
_WLB_RE = re.compile(r"signer(?P<signer>\d+)_label(?P<label>\d+)_sample(?P<sample>\d+)(?:_f(?P<frame>\d+))?", re.I)


@dataclass(frozen=True)
class WlbKey:
    signer: int
    label: int
    sample: int
    frame: Optional[int] = None

    @property
    def clip_id(self) -> str:
        return f"signer{self.signer}_label{self.label}_sample{self.sample}"

    @property
    def gloss(self) -> str:
        return GLOSSES[self.label]


def parse_wlb_name(name: str) -> Optional[WlbKey]:
    """'signer4_label0_sample10_f15.jpg' -> WlbKey(4, 0, 10, 15). None jika tidak cocok."""
    m = _WLB_RE.search(name)
    if not m:
        return None
    label = int(m["label"])
    if not 0 <= label < len(GLOSSES):
        return None
    frame = m["frame"]
    return WlbKey(int(m["signer"]), label, int(m["sample"]), int(frame) if frame is not None else None)


def parse_alphabet_name(name: str, folder: str) -> Optional[Tuple[str, str]]:
    """
    'A_Polos Terang_Samsung_A55.jpg' di folder 'A' -> ('A', 'samsung_a55')
    Grup (kontributor/perangkat) dipakai untuk split agar foto dari HP yang sama tidak bocor ke test.
    """
    letter = folder.strip().upper()
    if letter not in LETTERS:
        head = name.split("_", 1)[0].strip().upper()
        letter = head if head in LETTERS else ""
    if not letter:
        return None
    parts = re.sub(r"\.[a-z0-9]+$", "", name, flags=re.I).split("_")
    group = "_".join(p.strip().lower().replace(" ", "") for p in parts[2:4]) or "unknown"
    group = re.sub(r"\(\d+\)$", "", group)
    return letter, group


# ---------------------------------------------------------------------------
# Bank TEKS per konsep (masukan modalitas teks; juga naskah ucapan untuk bank AUDIO)
# ---------------------------------------------------------------------------
GLOSS_TEXTS: Dict[str, List[str]] = {
    "AIR": ["air", "air putih", "minum air"],
    "BELAJAR": ["belajar", "ayo belajar", "sedang belajar"],
    "CARI": ["cari", "mencari", "sedang mencari"],
    "HARI": ["hari", "hari ini", "setiap hari"],
    "INGAT": ["ingat", "mengingat", "saya ingat"],
    "LAGI": ["lagi", "sekali lagi", "ulangi lagi"],
    "MAAF": ["maaf", "mohon maaf", "minta maaf"],
    "MAKAN": ["makan", "ayo makan", "makan nasi"],
    "MOTOR": ["motor", "sepeda motor", "naik motor"],
    "SAYA": ["saya", "aku", "diri saya"],
    "TERIMA_KASIH": ["terima kasih", "makasih", "terima kasih banyak"],
    "TULI": ["tuli", "teman tuli", "orang tuli"],
    "APA": ["apa", "apa itu", "ada apa"],
    "SIAPA": ["siapa", "siapa dia", "siapa namamu"],
    "KAPAN": ["kapan", "kapan waktunya", "sejak kapan"],
    "DIMANA": ["di mana", "dimana", "di mana tempatnya"],
    "MENGAPA": ["mengapa", "kenapa", "mengapa begitu"],
    "BAGAIMANA": ["bagaimana", "gimana", "bagaimana caranya"],
    "MERAH": ["merah", "warna merah", "merah tua"],
    "KUNING": ["kuning", "warna kuning", "kuning cerah"],
    "HIJAU": ["hijau", "warna hijau", "hijau daun"],
    "HITAM": ["hitam", "warna hitam", "hitam pekat"],
    "DENGAR": ["dengar", "mendengar", "dengarkan"],
    "BERANGKAT": ["berangkat", "mau berangkat", "berangkat sekolah"],
    "DATANG": ["datang", "sudah datang", "kedatangan"],
    "TEMAN": ["teman", "kawan", "sahabat"],
    "KELUARGA": ["keluarga", "keluarga saya", "anggota keluarga"],
    "RUMAH": ["rumah", "di rumah", "pulang ke rumah"],
    "PAGI": ["pagi", "selamat pagi", "pagi pagi"],
    "SIANG": ["siang", "selamat siang", "tengah siang"],
    "SORE": ["sore", "selamat sore", "sore sore"],
    "MALAM": ["malam", "selamat malam", "tengah malam"],
}
assert set(GLOSS_TEXTS) == set(GLOSSES)

# Nama huruf dalam bahasa Indonesia (untuk TTS & teks)
LETTER_NAMES: Dict[str, str] = dict(zip(LETTERS, [
    "a", "be", "ce", "de", "e", "ef", "ge", "ha", "i", "je", "ka", "el", "em",
    "en", "o", "pe", "ki", "er", "es", "te", "u", "fe", "we", "eks", "ye", "zet",
]))
LETTER_TEXTS: Dict[str, List[str]] = {
    L: [L.lower(), f"huruf {L.lower()}", LETTER_NAMES[L]] for L in LETTERS
}


def texts_for(task: str) -> Dict[str, List[str]]:
    return GLOSS_TEXTS if task == "gloss" else LETTER_TEXTS


def speech_scripts_for(task: str) -> Dict[str, List[str]]:
    """Naskah yang diucapkan (TTS / perekaman relawan) per konsep."""
    if task == "gloss":
        return GLOSS_TEXTS
    return {L: [LETTER_NAMES[L], f"huruf {LETTER_NAMES[L]}", f"abjad {LETTER_NAMES[L]}"] for L in LETTERS}


# ---------------------------------------------------------------------------
# Tokenisasi teks level-karakter (identik dengan web/js/xmf.js — vocab diekspor ke JSON)
# ---------------------------------------------------------------------------
PAD_ID, UNK_ID = 0, 1
TEXT_ALPHABET = "abcdefghijklmnopqrstuvwxyz0123456789 .,?!-'"
CHAR_TO_ID: Dict[str, int] = {c: i + 2 for i, c in enumerate(TEXT_ALPHABET)}
TEXT_VOCAB_SIZE = len(TEXT_ALPHABET) + 2


def normalize_text(text: str) -> str:
    return " ".join(str(text).lower().replace("_", " ").split())


def encode_text(text: Optional[str], max_len: int = 64) -> List[int]:
    ids = [PAD_ID] * max_len
    if not text:
        return ids
    for i, ch in enumerate(normalize_text(text)[:max_len]):
        ids[i] = CHAR_TO_ID.get(ch, UNK_ID)
    return ids
