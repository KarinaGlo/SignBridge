import pandas as pd
import json

df = pd.read_csv('data/manifest_wl_bisindo.csv')
train_map = df[['label', 'gloss']].drop_duplicates().sort_values('label').set_index('label')['gloss'].to_dict()

with open('web/model/labels.json') as f:
    web_labels = json.load(f)

# Semantic relations:
# Let's inspect semantic relations between training labels and web labels:
# e.g.:
# - AIR (Water) vs HALO (Hello) -> DIFFERENT CONCEPT
# - BELAJAR (Study) vs TERIMA_KASIH (Thank you) -> INDEX MISMATCH (BELAJAR is at web index 14)
# - MAAF (Sorry) vs GURU (Teacher) -> INDEX MISMATCH (MAAF is at web index 2)
# - SAYA (I/Me) vs SUDAH (Already) -> INDEX MISMATCH (SAYA is at web index 4)
# - TERIMA_KASIH vs BELUM -> INDEX MISMATCH (TERIMA_KASIH is at web index 1)
# - APA (What) vs TIDAK (No) -> INDEX MISMATCH (APA is at web index 24)
# - SIAPA (Who) vs ADA (There is) -> INDEX MISMATCH (SIAPA is at web index 25)
# - KAPAN (When) vs BELAJAR -> INDEX MISMATCH (KAPAN is at web index 27)
# - DIMANA (Where) vs PAHAM -> INDEX MISMATCH (DIMANA is at web index 26)
# - BAGAIMANA (How) vs BACA -> INDEX MISMATCH (BAGAIMANA is at web index 28)
# - TEMAN (Friend) vs SIAPA -> INDEX MISMATCH (TEMAN is at web index 7)
# What about semantic relations between words that don't share exact string?
# e.g. RUMAH (House/Home) vs SEKOLAH (School) -> SEMANTICALLY RELATED — NEEDS HUMAN VALIDATION (Location concept)
# e.g. MENGAPA (Why) vs TANYA (Ask/Question) -> SEMANTICALLY RELATED — NEEDS HUMAN VALIDATION (Question concept)
# e.g. DENGAR (Hear) vs TULI (Deaf) vs PAHAM (Understand)

print("Index | Training Label | Checkpoint Label | ONNX Output Index | Frontend Label | Match Status")
for i in range(32):
    t_lbl = train_map[i]
    w_lbl = web_labels[i]
    
    # Classify
    if t_lbl == w_lbl:
        status = "EXACT MATCH"
    elif t_lbl in web_labels:
        web_idx = web_labels.index(t_lbl)
        status = f"INDEX MISMATCH (Exists at Web Index {web_idx})"
    elif t_lbl == "MENGAPA" and w_lbl == "TANYA":
        status = "SEMANTICALLY RELATED — NEEDS HUMAN VALIDATION (Interrogative)"
    elif t_lbl == "RUMAH" and w_lbl == "KAPAN":
        status = "DIFFERENT CONCEPT"
    elif t_lbl in ["PAGI", "SIANG", "SORE", "MALAM"] and w_lbl in ["BAGAIMANA", "BAIK", "BENAR", "SALAH"]:
        status = "DIFFERENT CONCEPT"
    elif t_lbl in ["MERAH", "KUNING", "HIJAU", "HITAM"]:
        status = "DIFFERENT CONCEPT (Color vs Classroom Action/Object)"
    else:
        status = "DIFFERENT CONCEPT"
        
    print(f"{i:2d} | {t_lbl:15s} | {t_lbl:15s} | {i:2d} | {w_lbl:15s} | {status}")

