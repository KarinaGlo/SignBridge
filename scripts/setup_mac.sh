#!/usr/bin/env bash
# scripts/setup_mac.sh — Siapkan proyek SignBridge-XMF di Mac (mode cicil: citra belum lengkap tidak masalah).
#
#   bash ~/Downloads/setup_mac.sh                  # default: ~/Documents/SignBridge
#   DEST=~/Kuliah/SignBridge bash ~/Downloads/setup_mac.sh
#
# Langkah: alat (Homebrew) -> repo + branch rombak -> .venv Python 3.11 -> folder data (symlink Google Drive bila ada)
#          -> folder rekaman suara relawan -> tes -> ingest awal -> buka di Kiro. Aman dijalankan berulang.
set -euo pipefail
DEST="${DEST:-$HOME/Documents/SignBridge}"
BRANCH="rombak/xmf-crossmodal-fusion"
REPO="https://github.com/KarinaGlo/SignBridge.git"
BUNDLE="${BUNDLE:-$(ls -t "$HOME"/Downloads/signbridge_xmf*.bundle 2>/dev/null | head -1 || true)}"
step() { printf "\n\033[1;35m==> %s\033[0m\n" "$*"; }
warn() { printf "\033[1;33m[!] %s\033[0m\n" "$*"; }

step "1/8 Alat: Homebrew, git, Python 3.11, ffmpeg, rclone"
if ! command -v brew >/dev/null; then
  echo 'Homebrew belum ada. Pasang dulu:'
  echo '  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"'
  exit 1
fi
for f in git python@3.11 ffmpeg rclone; do brew list "$f" >/dev/null 2>&1 || brew install "$f"; done
PY="$(brew --prefix python@3.11)/bin/python3.11"

step "2/8 Repo & branch $BRANCH  ->  $DEST"
mkdir -p "$(dirname "$DEST")"
[ -d "$DEST/.git" ] || git clone "$REPO" "$DEST"
cd "$DEST"
if git ls-remote --exit-code --heads origin "$BRANCH" >/dev/null 2>&1; then
  SRC=origin; echo "Branch ditemukan di GitHub."
elif [ -n "$BUNDLE" ] && [ -f "$BUNDLE" ]; then
  SRC="$BUNDLE"; echo "Memakai bundle: $BUNDLE"
else
  warn "Branch belum ada di GitHub dan file signbridge_xmf.bundle tidak ditemukan di ~/Downloads."; exit 1
fi
git fetch "$SRC" "$BRANCH"
if git show-ref --verify --quiet "refs/heads/$BRANCH"; then
  git checkout "$BRANCH" && git merge --ff-only FETCH_HEAD || warn "Branch lokal sudah berbeda; dibiarkan apa adanya."
else
  git checkout -b "$BRANCH" FETCH_HEAD
fi
if [ "$SRC" != origin ]; then
  git push -u origin "$BRANCH" 2>/dev/null && echo "Branch didorong ke GitHub." \
    || warn "Belum bisa push (butuh akses tulis ke repo). Minta Karina menambahkanmu sebagai collaborator, lalu: git push -u origin $BRANCH"
fi

step "3/8 Virtual environment .venv (Python 3.11) + library"
[ -x .venv/bin/python ] || "$PY" -m venv .venv
# shellcheck disable=SC1091
source .venv/bin/activate
python -m pip install -q --upgrade pip
python -m pip install -q -r requirements-xmf.txt

step "4/8 Folder data sumber  data/raw/wlbisindo_drive"
RAW="data/raw/wlbisindo_drive"
mkdir -p data/raw
if [ -e "$RAW" ]; then
  echo "Sudah ada: $RAW"
else
  GD="$(ls -d "$HOME"/Library/CloudStorage/GoogleDrive-*/{"My Drive","Drive Saya"}/WL-BISINDO 2>/dev/null | head -1 || true)"
  if [ -n "$GD" ]; then
    ln -s "$GD" "$RAW"; echo "Symlink ke Google Drive: $GD"
    echo "Tips: di Finder klik kanan WL-BISINDO -> Akses offline -> Tersedia offline (agar preprocessing cepat)."
  else
    mkdir -p "$RAW"/{video,citra,alfabet}
    warn "Folder Google Drive 'WL-BISINDO' tidak ditemukan. Dibuat folder kosong."
    echo "  Pilihan: (a) Google Drive for Desktop + 'Tambahkan pintasan ke Drive', hapus $RAW lalu jalankan skrip ini lagi;"
    echo "           (b) rclone config (remote 'gdrive') lalu: bash scripts/xmf_sync_drive.sh"
  fi
fi

step "5/8 Folder rekaman suara relawan  data/raw/audio/{gloss,alphabet}/<KONSEP>/"
python - <<'PYEOF'
from pathlib import Path
from signbridge.xmf.config import GLOSSES, LETTERS, speech_scripts_for
for task, classes in (("gloss", GLOSSES), ("alphabet", LETTERS)):
    root = Path("data/raw/audio") / task
    scripts = speech_scripts_for(task)
    for c in classes:
        d = root / c
        d.mkdir(parents=True, exist_ok=True)
        (d / "_UCAPKAN.txt").write_text("Ucapkan salah satu (rekam 1-2 detik, 16 kHz mono WAV/M4A):\n- " + "\n- ".join(scripts[c]) + "\n")
(Path("data/raw/audio") / "README.txt").write_text(
    "Nama file: <namapenutur>_<nomor>.wav  contoh: gloria_1.wav, farrel_3.m4a\n"
    "Satu penutur = satu nama (dipakai untuk split train/val/test per penutur).\n"
    "Target awal: 4 orang x 32 kata x 5 kali. Rekam pakai Voice Memos lalu salin ke folder kata yang sesuai.\n")
print("Folder rekaman siap: data/raw/audio/gloss/<32 kata>, data/raw/audio/alphabet/<A-Z>")
PYEOF

step "6/8 Tes cepat"
python -m pytest -q -p no:cacheprovider tests/test_xmf.py 2>&1 | tail -3 || warn "Ada tes gagal — kirim outputnya ke Claude."

step "7/8 Ingest awal (mode cicil)"
if [ -n "$(find -L "$RAW/video" -name '*.mp4' -print -quit 2>/dev/null)" ]; then
  python -m signbridge.xmf.ingest --drive-root "$RAW"
  echo "Laporan: data/xmf/ingest/ingest_report.json"
else
  warn "Belum ada video di $RAW/video — ingest dilewati. Jalankan lagi setelah data tersedia."
fi

step "8/8 Buka di Kiro"
if command -v kiro >/dev/null; then kiro "$DEST"
elif [ -d /Applications/Kiro.app ]; then open -a Kiro "$DEST"
else warn "Kiro tidak ditemukan di /Applications. Buka manual: File -> Open Folder -> $DEST"; fi

printf "\n\033[1;32mSelesai.\033[0m Folder proyek: %s\n" "$DEST"
echo "Berikutnya (di Terminal Kiro):  source .venv/bin/activate && python -m signbridge.xmf.ingest"
echo "Daftar tugas cicil ada di Kiro: .kiro/specs/xmf-crossmodal-fusion/tasks.md"
