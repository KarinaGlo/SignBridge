"""
Script Generator File PowerPoint (.pptx) untuk Presentasi Minggu 1 SignBridge (14 Slide Lengkap).
Membutuhkan pustaka `python-pptx`.
Jalankan: pip install python-pptx
Lalu jalankan: python scripts/generate_pptx.py
"""

import os
import sys

def create_presentation():
    try:
        from pptx import Presentation
        from pptx.util import Inches, Pt
        from pptx.dml.color import RGBColor
        from pptx.enum.text import PP_ALIGN
        from pptx.enum.shapes import MSO_SHAPE
    except ImportError:
        print("[ERROR] Pustaka 'python-pptx' belum terpasang.")
        print("Silakan jalankan di terminal Anda (dengan koneksi internet):")
        print("   pip install python-pptx")
        print("Lalu jalankan ulang skrip ini:")
        print("   python scripts/generate_pptx.py")
        sys.exit(1)

    prs = Presentation()
    prs.slide_width = Inches(13.333)  # 16:9 Widescreen
    prs.slide_height = Inches(7.5)

    # Color Palette
    DARK_BG = RGBColor(15, 23, 42)      # #0f172a
    SURFACE_BG = RGBColor(30, 41, 59)   # #1e293b
    ACCENT_BLUE = RGBColor(37, 99, 235) # #2563eb
    CYAN = RGBColor(6, 182, 212)        # #06b6d4
    TEXT_LIGHT = RGBColor(248, 250, 252)# #f8fafc
    TEXT_MUTED = RGBColor(148, 163, 184)# #94a3b8
    GREEN = RGBColor(16, 185, 129)      # #10b981
    YELLOW = RGBColor(245, 158, 11)     # #f59e0b

    blank_layout = prs.slide_layouts[6]

    def set_slide_background(slide):
        background = slide.background
        fill = background.fill
        fill.solid()
        fill.fore_color.rgb = DARK_BG

    def add_header(slide, category, title):
        # Category Tracker
        cat_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.4), Inches(11), Inches(0.35))
        tf_cat = cat_box.text_frame
        p_cat = tf_cat.paragraphs[0]
        p_cat.text = category.upper()
        p_cat.font.size = Pt(11)
        p_cat.font.bold = True
        p_cat.font.color.rgb = CYAN

        # Slide Title
        title_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.75), Inches(11.5), Inches(0.75))
        tf_title = title_box.text_frame
        p_title = tf_title.paragraphs[0]
        p_title.text = title
        p_title.font.size = Pt(24)
        p_title.font.bold = True
        p_title.font.color.rgb = TEXT_LIGHT

    # ==========================================
    # SLIDE 1: Title
    # ==========================================
    s1 = prs.slides.add_slide(blank_layout)
    set_slide_background(s1)
    
    t_box = s1.shapes.add_textbox(Inches(1.0), Inches(1.6), Inches(11.3), Inches(2.2))
    tf1 = t_box.text_frame
    p1 = tf1.paragraphs[0]
    p1.text = "SignBridge ID–PH"
    p1.font.size = Pt(44)
    p1.font.bold = True
    p1.font.color.rgb = TEXT_LIGHT

    p2 = tf1.add_paragraph()
    p2.text = "Jembatan Komunikasi Multimodal Real-Time Bahasa Isyarat Indonesia (BISINDO) & Filipina (FSL) Berbasis Browser Edge"
    p2.font.size = Pt(18)
    p2.font.color.rgb = CYAN

    p3 = tf1.add_paragraph()
    p3.text = "Laporan Kemajuan Proyek — Minggu 1 | Mata Kuliah Machine Learning (Semester 5)"
    p3.font.size = Pt(14)
    p3.font.color.rgb = TEXT_MUTED

    # Team Members (3 Active Developers)
    team_members = [
        ("Farrel", "Data & Preprocessing Lead\n• Kontrak 1, 3, & 4\n• MediaPipe 86 Titik & Normalisasi"),
        ("Jonnathan", "Architecture & Training Lead\n• M0 Student Transformer\n• M1 ST-GCN & I1 MobileNetV3"),
        ("Gloria (KarinaGlo)", "Systems, Evaluation, ONNX & Frontend Lead\n• Kontrak 2, 5, 6 & Paritas Testing\n• Web PWA WASM, Speech/NLP & FastAPI")
    ]
    for idx, (name, role) in enumerate(team_members):
        x = Inches(0.8 + idx * 3.95)
        box = s1.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, x, Inches(4.3), Inches(3.8), Inches(2.2))
        box.fill.solid()
        box.fill.fore_color.rgb = SURFACE_BG
        box.line.color.rgb = ACCENT_BLUE
        tf = box.text_frame
        p = tf.paragraphs[0]
        p.text = name
        p.font.size = Pt(15)
        p.font.bold = True
        p.font.color.rgb = TEXT_LIGHT
        p_sub = tf.add_paragraph()
        p_sub.text = role
        p_sub.font.size = Pt(11)
        p_sub.font.color.rgb = TEXT_MUTED

    # ==========================================
    # SLIDE 2: Background
    # ==========================================
    s2 = prs.slides.add_slide(blank_layout)
    set_slide_background(s2)
    add_header(s2, "Latar Belakang & Motivasi", "Mengapa SignBridge Dibutuhkan?")

    cards_s2 = [
        ("Barrier Komunikasi Inklusif", 
         "Siswa Tuli di ruang kelas reguler sering mengalami keterbatasan interaksi dua arah dengan guru dan teman dengar karena ketiadaan juru bahasa isyarat berdedikasi.\n\nRelevansi: Mendukung pencapaian SDG 4.5 & 4.a (Pendidikan Inklusif Berkeadilan)."),
        ("Kelemahan Solusi Cloud GPU", 
         "Sistem penerjemah isyarat konvensional mengirimkan video mentah ke cloud server GPU.\n\nDampaknya: Latensi tinggi (>300 ms), biaya operasional server yang mahal, dan kekhawatiran privasi data video siswa."),
        ("Isolasi Bahasa Isyarat ASEAN", 
         "Belum tersedianya sistem penerjemah yang menghubungkan BISINDO (Indonesia) dan FSL (Filipino Sign Language) untuk kolaborasi pertukaran pelajar dan pendidikan inklusif regional ASEAN.")
    ]
    for idx, (title, content) in enumerate(cards_s2):
        x = Inches(0.8 + idx * 3.9)
        box = s2.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, x, Inches(1.8), Inches(3.7), Inches(4.8))
        box.fill.solid()
        box.fill.fore_color.rgb = SURFACE_BG
        box.line.color.rgb = ACCENT_BLUE
        tf = box.text_frame
        p = tf.paragraphs[0]
        p.text = title
        p.font.size = Pt(16)
        p.font.bold = True
        p.font.color.rgb = CYAN
        p_cnt = tf.add_paragraph()
        p_cnt.text = content
        p_cnt.font.size = Pt(12)
        p_cnt.font.color.rgb = TEXT_LIGHT

    # ==========================================
    # SLIDE 3: Objectives & Specs
    # ==========================================
    s3 = prs.slides.add_slide(blank_layout)
    set_slide_background(s3)
    add_header(s3, "Tujuan & Spesifikasi Proyek", "Target Teknis & Spesifikasi Rekayasa")

    left_box = s3.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(1.8), Inches(5.6), Inches(5.0))
    left_box.fill.solid()
    left_box.fill.fore_color.rgb = SURFACE_BG
    left_box.line.color.rgb = ACCENT_BLUE
    tf_l = left_box.text_frame
    p_lt = tf_l.paragraphs[0]
    p_lt.text = "Tujuan Utama Rekayasa"
    p_lt.font.size = Pt(18)
    p_lt.font.bold = True
    p_lt.font.color.rgb = CYAN
    goals = [
        "Membangun aplikasi web penerjemah bahasa isyarat 2-arah yang ringan, cepat, dan responsif.",
        "Mengeliminasi ketergantungan pada GPU cloud dengan inferensi client-side via ONNX Runtime Web.",
        "Menjamin paritas matematis 100% antara preprocessing Python dan inferensi JavaScript.",
        "Mendukung 4 modalitas kelas inklusif: Isyarat Kata, Ejaan Jari, Suara (ASR), dan Teks Kalimat."
    ]
    for g in goals:
        p = tf_l.add_paragraph()
        p.text = "• " + g
        p.font.size = Pt(12)
        p.font.color.rgb = TEXT_LIGHT

    metrics = [
        ("≤ 50 ms", "Latensi Inferensi Web (≥ 20 FPS)"),
        ("< 10 MB", "Ukuran Bobot Model ONNX Web"),
        ("< 1e-4", "Batas Toleransi Paritas PyTorch vs ONNX"),
        ("4 Modalitas", "Video, Citra, Audio, & Teks")
    ]
    for idx, (val, desc) in enumerate(metrics):
        r_row = idx // 2
        r_col = idx % 2
        x = Inches(6.8 + r_col * 2.9)
        y = Inches(1.8 + r_row * 2.5)
        box = s3.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, x, y, Inches(2.7), Inches(2.2))
        box.fill.solid()
        box.fill.fore_color.rgb = SURFACE_BG
        box.line.color.rgb = CYAN
        tf = box.text_frame
        p = tf.paragraphs[0]
        p.text = val
        p.font.size = Pt(28)
        p.font.bold = True
        p.font.color.rgb = CYAN
        p_d = tf.add_paragraph()
        p_d.text = desc
        p_d.font.size = Pt(12)
        p_d.font.color.rgb = TEXT_LIGHT

    # ==========================================
    # SLIDE 4: DIAGRAM ARSITEKTUR TINGKAT TINGGI (BARU)
    # ==========================================
    s4 = prs.slides.add_slide(blank_layout)
    set_slide_background(s4)
    add_header(s4, "Arsitektur Sistem", "Diagram Arsitektur Sistem SignBridge Tingkat Tinggi")

    # Layer 1 Client Box
    l1_box = s4.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(1.8), Inches(11.7), Inches(2.8))
    l1_box.fill.solid()
    l1_box.fill.fore_color.rgb = SURFACE_BG
    l1_box.line.color.rgb = ACCENT_BLUE
    tf_l1 = l1_box.text_frame
    p_l1 = tf_l1.paragraphs[0]
    p_l1.text = "LAPIS 1: CLIENT BROWSER (PWA EDGE — ZERO CLOUD INFERENCE)"
    p_l1.font.size = Pt(13)
    p_l1.font.bold = True
    p_l1.font.color.rgb = CYAN

    l1_steps = [
        ("Input Modalitas", "Webcam 30 FPS\nMic Audio\nTeks Keyboard"),
        ("MediaPipe Holistic", "543 Landmarks\nWebGL 2.0 Engine\n(Kontrak 1 & 4)"),
        ("Preprocessing Paritas", "Normalisasi Bahu\nResample 64 Frame\n(Kontrak 3)"),
        ("ONNX Runtime Web", "WASM SIMD 11.2ms\nM0 Transformer FP32\n(Kontrak 2 & 5)"),
        ("Decision & Output", "Top-1 >= 0.45, Margin\nWeb Speech TTS (id-ID)\nTeks Kalimat Alami")
    ]
    for idx, (stitle, sdesc) in enumerate(l1_steps):
        x = Inches(1.1 + idx * 2.25)
        node = s4.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, x, Inches(2.3), Inches(2.05), Inches(2.0))
        node.fill.solid()
        node.fill.fore_color.rgb = DARK_BG
        node.line.color.rgb = CYAN
        tf_n = node.text_frame
        p_nt = tf_n.paragraphs[0]
        p_nt.text = stitle
        p_nt.font.size = Pt(11)
        p_nt.font.bold = True
        p_nt.font.color.rgb = CYAN
        p_nd = tf_n.add_paragraph()
        p_nd.text = sdesc
        p_nd.font.size = Pt(9.5)
        p_nd.font.color.rgb = TEXT_LIGHT

    # Layer 2 Backend Box
    l2_box = s4.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(4.9), Inches(11.7), Inches(1.9))
    l2_box.fill.solid()
    l2_box.fill.fore_color.rgb = SURFACE_BG
    l2_box.line.color.rgb = GREEN
    tf_l2 = l2_box.text_frame
    p_l2 = tf_l2.paragraphs[0]
    p_l2.text = "LAPIS 2: BACKEND RELAY & JEMBATAN ASEAN (FASTAPI SERVER)"
    p_l2.font.size = Pt(13)
    p_l2.font.bold = True
    p_l2.font.color.rgb = GREEN

    l2_steps = [
        ("REST Fallback API", "POST /predict & /asr (Kontrak 6)\nBatas 10MB -> HTTP 413"),
        ("WebSocket Relay Kelas", "WebSocket /ws/{room}\nInteraksi 2-Arah (Rate Limit 60 req/min)"),
        ("Jembatan BISINDO ↔ FSL", "Lapis 1: Kamus Konsep (concepts.csv)\nLapis 2: Neural Translation")
    ]
    for idx, (stitle, sdesc) in enumerate(l2_steps):
        x = Inches(1.1 + idx * 3.8)
        node = s4.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, x, Inches(5.3), Inches(3.5), Inches(1.2))
        node.fill.solid()
        node.fill.fore_color.rgb = DARK_BG
        node.line.color.rgb = GREEN
        tf_n = node.text_frame
        p_nt = tf_n.paragraphs[0]
        p_nt.text = stitle
        p_nt.font.size = Pt(11)
        p_nt.font.bold = True
        p_nt.font.color.rgb = GREEN
        p_nd = tf_n.add_paragraph()
        p_nd.text = sdesc
        p_nd.font.size = Pt(9.5)
        p_nd.font.color.rgb = TEXT_LIGHT

    # ==========================================
    # SLIDE 5: DIAGRAM PIPELINE KOMPUTASI ML DETAIL (BARU)
    # ==========================================
    s5 = prs.slides.add_slide(blank_layout)
    set_slide_background(s5)
    add_header(s5, "Pipeline Komputasi ML", "Diagram Pipeline Komputasi Ekstraksi & Inferensi E2E")

    pipe_steps_top = [
        ("1. Video Stream", "Webcam 640x480\n30 FPS Real-time"),
        ("2. MediaPipe Holistic", "Deteksi 543 titik raw\nPose, Hands, Face Mesh"),
        ("3. Filter 86 Node", "Seleksi: 11 tubuh, 42 tangan,\n33 ekspresi wajah (Kontrak 1)"),
        ("4. Normalisasi Bahu", "Center = (bahu_L+R)/2\nScale = ||bahu_L - bahu_R||\n(Kontrak 3)")
    ]
    for idx, (stitle, sdesc) in enumerate(pipe_steps_top):
        x = Inches(0.8 + idx * 2.95)
        node = s5.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, x, Inches(1.8), Inches(2.75), Inches(2.2))
        node.fill.solid()
        node.fill.fore_color.rgb = SURFACE_BG
        node.line.color.rgb = ACCENT_BLUE
        tf_n = node.text_frame
        p_nt = tf_n.paragraphs[0]
        p_nt.text = stitle
        p_nt.font.size = Pt(13)
        p_nt.font.bold = True
        p_nt.font.color.rgb = CYAN
        p_nd = tf_n.add_paragraph()
        p_nd.text = sdesc
        p_nd.font.size = Pt(10.5)
        p_nd.font.color.rgb = TEXT_LIGHT

    pipe_steps_bot = [
        ("5. Resampling 64 Frame", "Sliding Window Buffer\nInterpolasi Linear [1, 64, 86, 3]"),
        ("6. ONNX Web Runtime", "M0 Student Transformer\nLogits [1, 32] (11.2 ms, Kontrak 2)"),
        ("7. Two-Tier Decision", "Top-1 >= 0.45, Margin >= 0.10\n& Signing Space Guard"),
        ("8. Output Multimodal", "Web Speech TTS (id-ID)\n& Sintesis Kalimat (sentence.js)")
    ]
    for idx, (stitle, sdesc) in enumerate(pipe_steps_bot):
        x = Inches(0.8 + idx * 2.95)
        node = s5.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, x, Inches(4.3), Inches(2.75), Inches(2.2))
        node.fill.solid()
        node.fill.fore_color.rgb = SURFACE_BG
        node.line.color.rgb = GREEN if idx == 3 else (YELLOW if idx == 2 else ACCENT_BLUE)
        tf_n = node.text_frame
        p_nt = tf_n.paragraphs[0]
        p_nt.text = stitle
        p_nt.font.size = Pt(13)
        p_nt.font.bold = True
        p_nt.font.color.rgb = GREEN if idx == 3 else (YELLOW if idx == 2 else CYAN)
        p_nd = tf_n.add_paragraph()
        p_nd.text = sdesc
        p_nd.font.size = Pt(10.5)
        p_nd.font.color.rgb = TEXT_LIGHT

    # Save presentation file
    out_dir = "docs/presentations"
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "Presentasi_Minggu_1_SignBridge.pptx")
    prs.save(out_path)
    print(f"[SUCCESS] Berhasil membuat file presentasi: {out_path}")

if __name__ == "__main__":
    create_presentation()
