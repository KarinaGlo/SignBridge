#!/usr/bin/env bash
# scripts/xmf_sync_drive.sh — TAHAP 1 (SOURCE): salin folder Drive "WL-BISINDO" ke data/raw/wlbisindo_drive/
#
# Cara 1 (disarankan, bisa dicicil & melanjutkan otomatis): rclone
#   1) Pasang rclone (https://rclone.org/install/) lalu: rclone config  -> buat remote bernama "gdrive"
#   2) bash scripts/xmf_sync_drive.sh
# Cara 2: Google Drive for Desktop -> klik kanan folder WL-BISINDO -> "Available offline",
#   lalu buat symlink:  ln -s "/path/ke/GoogleDrive/Shared with me/WL-BISINDO" data/raw/wlbisindo_drive
# Cara 3: unduh manual zip dari web Drive lalu ekstrak ke data/raw/wlbisindo_drive/{video,citra,alfabet}
set -euo pipefail
FOLDER_ID="${XMF_DRIVE_FOLDER_ID:-1dkZl3TRpJEj3wGjzrYUrVWQ2Z6yq29pN}"
DEST="${1:-data/raw/wlbisindo_drive}"
REMOTE="${XMF_RCLONE_REMOTE:-gdrive}"
command -v rclone >/dev/null || { echo "rclone belum terpasang — lihat komentar di atas skrip ini"; exit 1; }
mkdir -p "$DEST"
# --drive-root-folder-id menunjuk langsung folder yang dibagikan; copy bersifat inkremental (aman diulang)
rclone copy "${REMOTE}:" "$DEST" --drive-root-folder-id "$FOLDER_ID" \
  --transfers 16 --checkers 32 --fast-list --progress
echo "Selesai. Jalankan ulang kapan saja saat upload citra bertambah (hanya file baru yang diunduh)."
find "$DEST" -maxdepth 1 -mindepth 1 -type d -exec sh -c 'echo "  $(basename "$1"): $(find "$1" -type f | wc -l) file"' _ {} \;
