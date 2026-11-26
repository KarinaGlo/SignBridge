"""
scripts/xmf_build_architecture_page.py — Bangun halaman arsitektur & pipeline SignBridge-XMF (HTML + logo tools)
lalu render PNG-nya untuk laporan/slide:

    python scripts/xmf_build_architecture_page.py --icons /tmp/icons.json
    -> docs/architecture/xmf_architecture.html
    -> docs/architecture/xmf_pipeline.png, xmf_model.png   (butuh google-chrome / chromium untuk render)

Logo diambil dari paket npm `simple-icons` (CC0): node -e "..." menulis icons.json (lihat README di docs).
"""

from __future__ import annotations

import argparse
import html
import json
import shutil
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DARK_LOGOS = {"numpy", "github", "json"}


def logo(icons: dict, key: str, x: float, y: float, s: float = 30) -> str:
    i = icons[key]
    fill = "#111" if key in DARK_LOGOS else f"#{i['hex']}"
    k = (s - 10) / 24
    return (f'<g transform="translate({x},{y})"><title>{html.escape(i["title"])}</title>'
            f'<rect width="{s}" height="{s}" rx="7" fill="#fff" stroke="#06222e" stroke-opacity=".18"/>'
            f'<path transform="translate(5,5) scale({k:.4f})" fill="{fill}" d="{i["path"]}"/></g>')


STAGES = [
    ("1", "Source", ["googledrive", "rclone"], ["Drive WL-BISINDO:", "video 1.600 mp4", "citra 16 frame/klip", "alfabet A–Z"]),
    ("2", "Ingestion", ["python", "ffmpeg"], ["gabung per kunci", "signer·label·sample", "label dari nama file", "bank audio + teks"]),
    ("3", "Preprocessing", ["mediapipe", "opencv", "numpy"], ["1 proses, 1 .npz/sampel", "pose 64×86×3", "citra 16×112² (crop)", "audio 2,5 dtk · teks 64"]),
    ("4", "Modeling", ["pytorch"], ["SignBridge-XMF", "4 encoder → Cross-", "Modal Transformer", "+ gated weighting"]),
    ("5", "Training", ["pytorch", "googlecolab", "yaml"], ["AdamW + cosine", "sampling subset", "modalitas, augmentasi", "early stop F1 (V+I)"]),
    ("6", "Evaluation", ["python", "numpy"], ["protokol SD & SI", "metrik utama V+I", "ablation 8 subset", "confusion matrix"]),
    ("7", "Export", ["onnx"], ["ONNX opset 17", "mel & normalisasi", "di dalam graf", "paritas < 1e-3"]),
    ("8", "Deployment", ["webassembly", "googlechrome", "fastapi", "docker"], ["ORT Web (WASM)", "MediaPipe JS di", "browser · PWA", "FastAPI + Docker"]),
]


def pipeline_svg(icons: dict) -> str:
    W, H, x0, dx, y = 1240, 330, 78, 155, 96
    parts = [f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="Pipeline SignBridge-XMF dari source hingga deployment, 8 tahap" '
             f'font-family="Inter, sans-serif" style="width:100%;height:auto;min-width:880px">',
             '<defs><marker id="ar" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto">'
             '<path d="M0,0L10,5L0,10z" fill="currentColor"/></marker></defs>',
             f'<line x1="{x0}" y1="{y}" x2="{x0 + dx * 7}" y2="{y}" stroke="currentColor" stroke-width="8" stroke-linecap="round"/>',
             f'<line x1="{x0 + dx * 2}" y1="{y}" x2="{x0 + dx * 3}" y2="{y}" stroke="#ff2e7e" stroke-width="8"/>']
    for i, (num, name, logos, lines) in enumerate(STAGES):
        cx = x0 + dx * i
        hot = i == 2
        parts.append(f'<circle cx="{cx}" cy="{y}" r="22" fill="{"#ff2e7e" if hot else "var(--bg)"}" stroke="currentColor" stroke-width="4"/>')
        parts.append(f'<text x="{cx}" y="{y + 6}" text-anchor="middle" font-size="17" font-weight="700" '
                     f'fill="{"#fff" if hot else "currentColor"}">{num}</text>')
        parts.append(f'<text x="{cx}" y="{y - 40}" text-anchor="middle" font-size="16" font-weight="700" '
                     f'font-family="Space Grotesk, sans-serif" fill="currentColor">{name}</text>')
        n = len(logos)
        for j, k in enumerate(logos):
            parts.append(logo(icons, k, cx - (n * 34 - 4) / 2 + j * 34, y + 36))
        for j, t in enumerate(lines):
            parts.append(f'<text x="{cx}" y="{y + 90 + j * 18}" text-anchor="middle" font-size="12.5" '
                         f'fill="currentColor" opacity="{1 if j == 0 else .78}">{html.escape(t)}</text>')
    yb = 290
    parts.append(f'<path d="M{x0 + dx * 7},{yb - 10} L{x0 + dx * 7},{yb} L{x0},{yb} L{x0},{yb - 10}" fill="none" '
                 f'stroke="currentColor" stroke-dasharray="5 5" opacity=".55" marker-end="url(#ar)"/>')
    parts.append(f'<text x="{(x0 + x0 + dx * 7) / 2}" y="{yb + 22}" text-anchor="middle" font-size="12.5" opacity=".8" fill="currentColor">'
                 'mode cicil: upload Drive bertambah → jalankan ulang (hanya sampel baru yang diproses)</text>')
    parts.append("</svg>")
    return "".join(parts)


def model_svg(icons: dict) -> str:
    W, H = 1240, 560
    lanes = [
        ("VIDEO", "pose [64, 86, 3]", "MediaPipe Holistic, 86 titik", "Part-aware embed + kecepatan", "Transformer temporal ×2", "16 token", "mediapipe"),
        ("CITRA", "frames [16, 3, 112, 112]", "16 frame klip yang sama, crop badan", "MobileNetV3-Small (ImageNet)", "per frame + Transformer ×1", "16 token", "opencv"),
        ("AUDIO", "gelombang [40000]", "ucapan konsep, 16 kHz, 2,5 dtk", "log-mel 64 (STFT di graf)", "Conv1d ×2 + Transformer ×1", "31 token", "ffmpeg"),
        ("TEKS", "id karakter [64]", "kata/kalimat konsep", "Embedding karakter + posisi", "Transformer ×1 (mask pad)", "64 token", "json"),
    ]
    p = [f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="Arsitektur SignBridge-XMF: empat encoder, fusion cross-modal attention, gated weighting" '
         f'font-family="Inter, sans-serif" style="width:100%;height:auto;min-width:880px">',
         '<defs><marker id="am" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto">'
         '<path d="M0,0L10,5L0,10z" fill="currentColor"/></marker></defs>']
    ys = [40, 160, 280, 400]
    for (name, shape, src, e1, e2, tok, lg), y in zip(lanes, ys):
        p.append(logo(icons, lg, 16, y + 18, 34))
        p.append(f'<text x="62" y="{y + 32}" font-size="15" font-weight="700" font-family="Space Grotesk, sans-serif" fill="currentColor">{name}</text>')
        p.append(f'<text x="62" y="{y + 51}" font-size="12.5" fill="currentColor">{html.escape(shape)}</text>')
        p.append(f'<text x="62" y="{y + 69}" font-size="12" fill="currentColor" opacity=".75">{html.escape(src)}</text>')
        p.append(f'<rect x="300" y="{y + 10}" width="250" height="68" rx="8" fill="var(--panel)" stroke="currentColor" stroke-opacity=".45"/>')
        p.append(f'<text x="425" y="{y + 38}" text-anchor="middle" font-size="13" font-weight="600" fill="currentColor">{html.escape(e1)}</text>')
        p.append(f'<text x="425" y="{y + 58}" text-anchor="middle" font-size="12.5" fill="currentColor" opacity=".8">{html.escape(e2)}</text>')
        p.append(f'<line x1="262" y1="{y + 44}" x2="296" y2="{y + 44}" stroke="currentColor" marker-end="url(#am)"/>')
        for k in range(6):
            p.append(f'<rect x="{574 + k * 13}" y="{y + 32}" width="10" height="24" rx="2" fill="currentColor" opacity="{.35 + .1 * k:.2f}"/>')
        p.append(f'<text x="613" y="{y + 74}" text-anchor="middle" font-size="12" fill="currentColor" opacity=".8">{tok}</text>')
        p.append(f'<line x1="554" y1="{y + 44}" x2="570" y2="{y + 44}" stroke="currentColor"/>')
        p.append(f'<path d="M656,{y + 44} C690,{y + 44} 690,{270} 718,{270}" fill="none" stroke="currentColor" stroke-opacity=".6" marker-end="url(#am)"/>')
    # fusion block
    p.append('<rect x="722" y="96" width="220" height="350" rx="12" fill="#ff2e7e"/>')
    for i, t in enumerate(["[CLS] + 127 token", "+ embedding tipe", "modalitas", "", "Cross-Modal", "Attention Fusion", "Transformer ×2", "", "token modalitas yang", "hilang di-mask"]):
        big = 4 <= i <= 6
        p.append(f'<text x="832" y="{150 + i * 26}" text-anchor="middle" font-size="{17 if big else 13}" '
                 f'font-weight="{700 if big else 500}" fill="#fff" font-family="{"Space Grotesk" if big else "Inter"}, sans-serif">{t}</text>')
    # gate + heads
    p.append('<line x1="942" y1="270" x2="982" y2="270" stroke="currentColor" marker-end="url(#am)"/>')
    p.append('<rect x="986" y="200" width="236" height="140" rx="10" fill="var(--panel)" stroke="currentColor" stroke-opacity=".45"/>')
    for i, t in enumerate(["Gated modality weighting", "u_m = rata-rata token modalitas m", "α = softmax(vᵀ tanh(W u_m))", "z = Σ α_m u_m ;  h = LN(CLS + z)"]):
        p.append(f'<text x="1104" y="{230 + i * 26}" text-anchor="middle" font-size="{14 if i == 0 else 12.5}" '
                 f'font-weight="{700 if i == 0 else 400}" fill="currentColor">{t}</text>')
    p.append('<line x1="1104" y1="340" x2="1104" y2="384" stroke="currentColor" marker-end="url(#am)"/>')
    p.append('<rect x="986" y="388" width="236" height="58" rx="10" fill="currentColor"/>')
    p.append('<text x="1104" y="413" text-anchor="middle" font-size="14" font-weight="700" fill="var(--bg)">logits: 32 gloss / 26 huruf</text>')
    p.append('<text x="1104" y="433" text-anchor="middle" font-size="12.5" fill="var(--bg)">+ bobot α per modalitas</text>')
    p.append('<line x1="1104" y1="200" x2="1104" y2="146" stroke="currentColor" marker-end="url(#am)"/>')
    p.append('<rect x="986" y="70" width="236" height="74" rx="10" fill="none" stroke="currentColor" stroke-dasharray="5 4"/>')
    for i, t in enumerate(["Head prototipe BERSAMA", "ke-4 u_m → ruang konsep yang", "sama (verifikasi lintas-modal)"]):
        p.append(f'<text x="1104" y="{94 + i * 19}" text-anchor="middle" font-size="{13.5 if i == 0 else 12}" font-weight="{700 if i == 0 else 400}" fill="currentColor">{t}</text>')
    p.append(logo(icons, "pytorch", 1188, 520, 30))
    p.append(logo(icons, "onnx", 1152, 520, 30))
    p.append('<text x="1144" y="540" text-anchor="end" font-size="12.5" fill="currentColor" opacity=".8">'
             'Loss = CE(fusion) + 0,5 · CE(prototipe per modalitas) · 2,1 juta parameter · ONNX 9,3 MB</text>')
    p.append("</svg>")
    return "".join(p)


PAGE = """<!DOCTYPE html>
<html lang="id"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>SignBridge-XMF Arsitektur</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;700&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
/* VOICE work: technical architecture brief for a lecturer and a 4-person team
   IDEA a transit line map: 8 stations from Drive to browser, one route
   PICTURE the pipeline route with tool logos, then the fusion model drawn as lanes merging into one block
   COLOUR ice ground, ink, hot pink for the unified preprocessing + fusion (what changed)
   TYPE Space Grotesk + Inter
   LAYOUT title + verdict + figures across the top, route full width, model full width, before/after table, commands */
:root{color-scheme:light dark;--bg:light-dark(#dff1f7,#06222e);--ink:light-dark(#06222e,#e4f3f8);--panel:light-dark(#ffffff,#0c3242);--rule:light-dark(#06222e2e,#e4f3f833);--hot:#ff2e7e}
:root[data-theme=light]{color-scheme:light}:root[data-theme=dark]{color-scheme:dark}
*{box-sizing:border-box;min-width:0}
body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.55 Inter,system-ui,sans-serif;overflow-x:clip}
.band{padding:clamp(24px,4vw,56px) max(5vw,16px)}
.wrap{max-width:1240px;margin:0 auto}
h1,h2{font-family:"Space Grotesk",sans-serif;letter-spacing:-.02em;line-height:1.05;margin:0 0 12px;text-wrap:balance}
h1{font-size:clamp(32px,4.4vw,50px)}h2{font-size:clamp(24px,2.6vw,32px);margin-top:8px}
.lead{font-size:17px;max-width:70ch;margin:0 0 20px}
.figs{display:grid;grid-template-columns:repeat(auto-fit,minmax(9.5em,1fr));gap:12px;margin:18px 0 8px}
.figs div{border-top:2px solid var(--ink);padding-top:8px}.figs b{display:block;font:700 clamp(22px,2.4vw,30px)/1.1 "Space Grotesk",sans-serif;white-space:nowrap}
.figs span{font-size:13.5px}
figure{margin:0}.scroll{overflow-x:auto}figcaption{font-size:14px;margin-top:8px;max-width:80ch}
.panel{background:var(--panel);border:1px solid var(--rule);border-radius:12px;padding:clamp(12px,2vw,24px)}
table{border-collapse:collapse;width:100%;font-size:15px}th,td{text-align:left;padding:10px 12px;border-bottom:1px solid var(--rule);vertical-align:top}
th{font-family:"Space Grotesk",sans-serif;font-size:15px}td:first-child{font-weight:600;width:18%}
.new{color:var(--hot);font-weight:600}
.two{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:28px}
pre{background:var(--panel);border:1px solid var(--rule);border-radius:10px;padding:14px;font-size:13.5px;line-height:1.5;overflow-x:auto;margin:0}
code{font-family:ui-monospace,Menlo,monospace;overflow-wrap:anywhere}
.copy{font:600 14px Inter,sans-serif;min-height:44px;padding:0 16px;border-radius:8px;border:1px solid var(--ink);background:transparent;color:var(--ink);cursor:pointer;margin-bottom:8px}
.copy:focus-visible{outline:3px solid var(--hot);outline-offset:2px}
.note{font-size:14px;opacity:.85}
@media(max-width:760px){.two{grid-template-columns:minmax(0,1fr)}}
@media(max-width:600px){table{font-size:13px}.stack thead{display:none}.stack tr{display:grid;padding-block:10px;border-bottom:1px solid var(--rule)}.stack td{border:0;padding:3px 0;width:auto}.stack td::before{content:attr(data-l);display:block;font-size:13px;opacity:.7;font-weight:600}}
</style></head><body>
<header class="band"><div class="wrap">
<h1>SignBridge-XMF: satu model fusion, empat modalitas dari sampel yang sama</h1>
<p class="lead">Video (keypoint) dan citra kini diambil dari klip WL-BISINDO yang sama, diproses bersama menjadi satu rekaman per sampel bersama pasangan audio dan teks dari konsep yang sama, lalu masuk ke <b>satu</b> Cross-Modal Attention Fusion Transformer. Model yang sama berjalan di browser lewat ONNX Runtime Web.</p>
<div class="figs">
<div><b>32 + 26</b><span>kelas: gloss WL-BISINDO + huruf A–Z</span></div>
<div><b>1.600 × 16</b><span>klip video × frame citra berpasangan</span></div>
<div><b>2,1 juta</b><span>parameter model gloss</span></div>
<div><b>9,3 MB</b><span>ONNX fp32 (6,3 MB int8)</span></div>
<div><b>≈150 ms</b><span>inferensi WASM 1 thread (uji Node)</span></div>
</div></div></header>

<section class="band" style="padding-top:0"><div class="wrap">
<h2>Pipeline delapan tahap, dari Drive sampai browser</h2>
<figure class="panel"><div class="scroll">__PIPE__</div>
<figcaption>Tahap 3 (merah muda) adalah perubahan utama: satu proses menghasilkan satu berkas <code>.npz</code> per sampel berisi pose, citra, audio, teks, dan mask modalitas. Label selalu dibaca dari nama file <code>signer·label·sample</code>.</figcaption></figure>
</div></section>

<section class="band" style="padding-top:0"><div class="wrap">
<h2>Arsitektur model: empat jalur bertemu di satu blok attention</h2>
<figure class="panel"><div class="scroll">__MODEL__</div>
<figcaption>Setiap token dapat meng-attend token modalitas lain (cross-modal attention). Bobot α dipelajari per sampel dan otomatis nol untuk modalitas yang tidak ada, jadi model yang sama melayani mode kamera saja (video+citra), mode ucapan, dan mode ketikan.</figcaption></figure>
</div></section>

<section class="band" style="padding-top:0"><div class="wrap">
<h2>Yang berubah dari presentasi pertama</h2>
<div class="panel"><table class="stack"><thead><tr><th>Aspek</th><th>Sebelumnya</th><th>Sekarang (branch rombak/xmf-crossmodal-fusion)</th></tr></thead><tbody>
<tr><td data-l="Aspek">Sumber per modalitas</td><td data-l="Sebelumnya">Video, citra, audio, teks dari sumber berbeda</td><td data-l="Sekarang" class="new">Video &amp; citra dari klip yang sama; audio &amp; teks dipasangkan per konsep</td></tr>
<tr><td data-l="Aspek">Preprocessing</td><td data-l="Sebelumnya">Skrip terpisah per modalitas</td><td data-l="Sekarang" class="new">Satu <code>preprocess.py</code>, satu rekaman 4-modalitas per sampel</td></tr>
<tr><td data-l="Aspek">Model</td><td data-l="Sebelumnya">Model terpisah per modalitas (M0, fingerspell, ASR)</td><td data-l="Sekarang" class="new">Satu model XMF untuk gloss; arsitektur yang sama untuk alfabet</td></tr>
<tr><td data-l="Aspek">Label citra</td><td data-l="Sebelumnya">Nama folder Drive (32 folder bernama salah)</td><td data-l="Sekarang">Dari nama file <code>labelN</code> → daftar resmi WL-BISINDO</td></tr>
<tr><td data-l="Aspek">Preprocessing di browser</td><td data-l="Sebelumnya">Normalisasi citra &amp; log-mel ditulis ulang di JS</td><td data-l="Sekarang">Di dalam graf ONNX; paritas JS–Python diuji</td></tr>
<tr><td data-l="Aspek">Alfabet di web</td><td data-l="Sebelumnya">Aturan geometri dengan keyakinan tetap 0,93</td><td data-l="Sekarang">XMF alfabet: crop tangan + landmark dari foto yang sama</td></tr>
<tr><td data-l="Aspek">web/js/app.js</td><td data-l="Sebelumnya">Syntax error (blok merge ganda), web tidak jalan</td><td data-l="Sekarang">Diperbaiki; lolos <code>node --check</code> dan 42 tes JS</td></tr>
</tbody></table></div>
</div></section>

<section class="band" style="padding-top:0"><div class="wrap two">
<div><h2>Cara melaporkan hasil</h2>
<p><b>Metrik utama = V+I (kamera saja)</b>, karena itu kondisi nyata pengguna Tuli di depan webcam. Laporkan dua protokol: <b>SD</b> (signer-dependent, sebanding dengan M0 99,1 %) dan <b>SI</b> (penanda 4 tidak pernah dilihat saat training), yang lebih jujur memprediksi uji langsung di browser.</p>
<p>Subset yang memuat audio atau teks dipasangkan di tingkat konsep, sehingga akurasinya tidak boleh diklaim sebagai pengenalan isyarat. Subset itu menunjukkan arah Dengar→Tuli: ucapan guru atau ketikan dipetakan ke konsep yang sama, lalu isyarat rujukan ditampilkan.</p>
<p class="note">Angka di halaman ini (parameter, ukuran, latensi) diukur dari uji asap. Akurasi asli baru ada setelah training di data WL-BISINDO lengkap.</p></div>
<div><h2>Perintah per tahap</h2>
<button class="copy" id="copy" type="button">Salin perintah</button>
<pre id="cmds"><code>bash scripts/xmf_sync_drive.sh                       # 1 source
python -m signbridge.xmf.ingest                      # 2 ingestion
python -m signbridge.xmf.audio_bank --task gloss     #   bank audio+teks
python -m signbridge.xmf.preprocess --task gloss --workers 4   # 3
python -m signbridge.xmf.train --config configs/xmf_gloss.yaml --protocol sd   # 4-6
python -m signbridge.xmf.train --config configs/xmf_gloss.yaml --protocol si
python -m signbridge.xmf.train --config configs/xmf_gloss.yaml --protocol final
python -m signbridge.xmf.export --ckpt outputs/xmf/XMF_gloss_final/best.pt     # 7
uvicorn server.app:app --port 7860                   # 8 deployment</code></pre></div>
</div></section>
<script>{const b=document.getElementById('copy');b.addEventListener('click',async()=>{try{await navigator.clipboard.writeText(document.getElementById('cmds').innerText);b.textContent='Tersalin'}catch(e){b.textContent='Salin manual'}setTimeout(()=>{b.textContent='Salin perintah'},1800)})}</script>
</body></html>
"""


def render_png(html_path: Path, out_png: Path, selector_index: int, width: int = 1400) -> bool:
    chrome = shutil.which("google-chrome") or shutil.which("chromium") or shutil.which("chromium-browser")
    if not chrome:
        return False
    src = html_path.read_text(encoding="utf-8")
    figs = src.split('<div class="scroll">')
    svg = figs[selector_index + 1].split("</div>")[0]
    page = ("<!DOCTYPE html><html><head><meta charset='utf-8'><link href='https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;700&family=Inter:wght@400;500;600;700&display=swap' rel='stylesheet'>"
            "<style>:root{--bg:#dff1f7;--panel:#fff}body{margin:0;padding:28px;background:#fff;color:#06222e;font-family:Inter,sans-serif}</style></head>"
            f"<body>{svg}</body></html>")
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td) / "f.html"
        tmp.write_text(page, encoding="utf-8")
        h = 470 if selector_index == 0 else 700
        subprocess.run([chrome, "--headless=new", "--disable-gpu", "--no-sandbox", "--hide-scrollbars",
                        f"--force-device-scale-factor=2", f"--window-size={width},{h}",
                        f"--screenshot={out_png}", tmp.as_uri()], check=True, capture_output=True, timeout=120)
    return True


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--icons", type=Path, required=True, help="icons.json dari paket npm simple-icons")
    ap.add_argument("--out", type=Path, default=ROOT / "docs/architecture")
    a = ap.parse_args()
    icons = json.loads(a.icons.read_text())
    a.out.mkdir(parents=True, exist_ok=True)
    page = PAGE.replace("__PIPE__", pipeline_svg(icons)).replace("__MODEL__", model_svg(icons))
    hp = a.out / "xmf_architecture.html"
    hp.write_text(page, encoding="utf-8")
    print("HTML ->", hp)
    for i, name in enumerate(["xmf_pipeline.png", "xmf_model.png"]):
        if render_png(hp, a.out / name, i):
            print("PNG  ->", a.out / name)


if __name__ == "__main__":
    main()
