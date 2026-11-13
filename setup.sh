#!/usr/bin/env bash
# setup.sh — InstalaCa semua dependensi SignBridge BISINDO
# Requirements: 20.1, 20.2, 20.3
# Exit code 0 jika berhasil, non-zero jika ada langkah yang gagal.

set -euo pipefail

echo "=================================================="
echo "  SignBridge BISINDO — Setup"
echo "=================================================="

# ── 1. Verifikasi Python (3.10+) ───────────────────────────────────────────────
echo ""
echo "[1/5] Memeriksa versi Python..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
required_major=3
required_minor=10
major=$(echo "$python_version" | cut -d. -f1)
minor=$(echo "$python_version" | cut -d. -f2)

if [ "$major" -lt "$required_major" ] || ([ "$major" -eq "$required_major" ] && [ "$minor" -lt "$required_minor" ]); then
    echo "ERROR: Diperlukan Python >= 3.10, ditemukan $python_version"
    exit 1
fi
echo "  Python $python_version — OK"

# ── 2. Buat virtual environment (opsional, lewati jika sudah aktif) ────────────
echo ""
echo "[2/5] Menyiapkan virtual environment..."
if [ -z "${VIRTUAL_ENV:-}" ] && [ -z "${CONDA_PREFIX:-}" ]; then
    if [ ! -d ".venv" ]; then
        python3 -m venv .venv
        echo "  Virtual environment dibuat di .venv/"
    else
        echo "  Virtual environment sudah ada di .venv/"
    fi
    # shellcheck disable=SC1091
    source .venv/bin/activate 2>/dev/null || source .venv/Scripts/activate 2>/dev/null || true
    echo "  Virtual environment diaktifkan."
else
    echo "  Virtual environment atau Conda sudah aktif — dilewati."
fi

# ── 3. Instal dependensi Python ────────────────────────────────────────────────
echo ""
echo "[3/5] Menginstal dependensi Python dari requirements.txt..."
pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet
echo "  Dependensi Python berhasil diinstal."

# ── 4. Instal dependensi JavaScript (opsional, lewati jika node tidak ada) ────
echo ""
echo "[4/5] Menginstal dependensi JavaScript..."
if command -v npm &> /dev/null; then
    npm install --prefix . --silent
    echo "  Dependensi JavaScript berhasil diinstal."
else
    echo "  PERINGATAN: npm tidak ditemukan. Lewati instalasi JavaScript."
    echo "             Instal Node.js >= 18 untuk fitur inferensi browser."
fi

# ── 5. Verifikasi struktur direktori ──────────────────────────────────────────
echo ""
echo "[5/5] Memverifikasi struktur direktori proyek..."
required_dirs=("data" "configs" "src" "tests" "scripts" "web")
for dir in "${required_dirs[@]}"; do
    if [ ! -d "$dir" ]; then
        mkdir -p "$dir"
        echo "  Direktori '$dir/' dibuat."
    else
        echo "  Direktori '$dir/' — OK"
    fi
done

required_configs=(
    "configs/train_bisindo.yaml"
    "configs/train_wlasl.yaml"
    "configs/eval_bisindo.yaml"
)
for cfg in "${required_configs[@]}"; do
    if [ ! -f "$cfg" ]; then
        echo "  PERINGATAN: File konfigurasi '$cfg' tidak ditemukan!"
    else
        echo "  Konfigurasi '$cfg' — OK"
    fi
done

echo ""
echo "=================================================="
echo "  Setup complete. Run \`python smoke_test.py\` to verify."
echo "=================================================="
exit 0
