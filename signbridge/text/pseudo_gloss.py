"""
pseudo_gloss.py — Linguistic rules for Indonesian <-> BISINDO Pseudo-Gloss conversion
and B0 Rule-Based Sentence Constructor.

Follows Modul 03 Langkah 12 (Bab 4.12 p. 19) & Bab 7.4 (sentence.js p. 39):
  1. sentence_to_pseudo_gloss(sentence):
     - Strips function words (ini, itu, yang, di [unless 'di mana'], ke, dari, adalah, untuk, pada)
     - Expands possessive clitics (-mu -> KAMU, -ku -> SAYA) & strips common prefixes/suffixes
     - Moves time expressions (PAGI, SIANG, SORE, MALAM, KEMARIN, BESOK, SEKARANG) to the FRONT
     - Moves question words (APA, SIAPA, KAPAN, DI MANA, MENGAPA, BAGAIMANA, BERAPA) to the BACK
     - Examples (Bab 4.12 p. 19):
         "Saya sudah makan nasi pagi ini."  -> "PAGI SAYA SUDAH MAKAN NASI"
         "Apakah kamu belajar di rumah?"    -> "KAMU BELAJAR RUMAH APA"
         "Di mana rumahmu?"                 -> "RUMAH KAMU DI MANA"

  2. gloss_to_sentence_rules(gloss_seq) [B0 baseline, identical to web/js/sentence.js]:
     - Deduplicates consecutive identical glosses
     - Capitalizes first word
     - Adds comma after leading time marker (Pagi, Siang, Sore, Malam, Kemarin, Besok)
     - Ends with '?' if a question word is present, otherwise '.'
     - Examples (Bab 7.4 p. 39):
         "Pagi Saya Belajar"  -> "Pagi, saya belajar."
         "Teman Datang Kapan" -> "Teman datang kapan?"
"""

from __future__ import annotations

import re
from typing import List, Sequence

TIME_WORDS = {"PAGI", "SIANG", "SORE", "MALAM", "KEMARIN", "BESOK", "SEKARANG", "TADI", "HARI_INI"}
QUESTION_WORDS = {"APA", "SIAPA", "KAPAN", "DI MANA", "DIMANA", "MENGAPA", "KENAPA", "BAGAIMANA", "BERAPA"}
FUNCTION_STOPWORDS = {
    "INI",
    "ITU",
    "YANG",
    "DI",
    "KE",
    "DARI",
    "ADALAH",
    "IALAH",
    "DENGAN",
    "UNTUK",
    "PADA",
    "DAN",
    "ATAU",
    "DALAM",
    "PARA",
    "SANG",
    "SI",
}

AFFIX_ROOT_MAP = {
    "MEMAKAN": "MAKAN",
    "MEMINUM": "MINUM",
    "MEMBACA": "BACA",
    "MENULIS": "TULIS",
    "MELIHAT": "LIHAT",
    "MENDENGAR": "DENGAR",
    "BERJALAN": "JALAN",
    "BERBICARA": "BICARA",
    "BERTANYA": "TANYA",
    "MENJAWAB": "JAWAB",
    "BERMAIN": "MAIN",
    "BEKERJA": "KERJA",
    "TERIMA_KASIH": "TERIMA KASIH",
}


def _strip_affixes_and_clitics(word: str) -> List[str]:
    """
    Normalize a single uppercase Indonesian token into 1 or 2 BISINDO root gloss tokens.
    """
    if word in ("APAKAH", "APA"):
        return ["APA"]
    if word in ("KENAPA", "MENGAPA"):
        return ["MENGAPA"]
    if word == "DIMANA":
        return ["DI MANA"]

    if word in AFFIX_ROOT_MAP:
        return [AFFIX_ROOT_MAP[word]]

    # Possessive clitics: RUMAHMU -> RUMAH KAMU, BUKUKU -> BUKU SAYA
    if len(word) > 4 and word.endswith("MU") and word not in ("KAMU", "ILMU", "TAMU", "TEMU"):
        base = word[:-2]
        return [_strip_affixes_and_clitics(base)[0], "KAMU"]
    if len(word) > 4 and word.endswith("KU") and word not in ("BUKU", "AKU", "SUKU", "PAKU", "KAKU"):
        base = word[:-2]
        return [_strip_affixes_and_clitics(base)[0], "SAYA"]
    if len(word) > 5 and word.endswith("NYA") and word not in ("TANYA", "BERTANYA", "PUNYA", "HANYA"):
        base = word[:-3]
        return [_strip_affixes_and_clitics(base)[0]]

    return [word]


def sentence_to_pseudo_gloss(sentence: str) -> str:
    """
    Transform a standard Indonesian sentence into BISINDO pseudo-gloss order:
      [TIME] + [CORE CONTENT GLOSSES] + [QUESTION]
    """
    if not sentence or not sentence.strip():
        return ""

    # Preserve multi-word question 'di mana' before punctuation stripping
    cleaned = re.sub(r"\bdi\s+mana\b", "DI_MANA", sentence, flags=re.IGNORECASE)
    cleaned = re.sub(r"\bterima\s+kasih\b", "TERIMA_KASIH", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"[^\w\s]", " ", cleaned)
    raw_tokens = [t.upper() for t in cleaned.split() if t.strip()]

    time_tokens: List[str] = []
    question_tokens: List[str] = []
    content_tokens: List[str] = []

    for tok in raw_tokens:
        if tok == "DI_MANA":
            question_tokens.append("DI MANA")
            continue
        if tok == "TERIMA_KASIH":
            content_tokens.append("TERIMA KASIH")
            continue

        expanded = _strip_affixes_and_clitics(tok)
        for sub in expanded:
            if sub in FUNCTION_STOPWORDS:
                continue
            if sub in TIME_WORDS:
                time_tokens.append(sub.replace("_", " "))
            elif sub in QUESTION_WORDS:
                question_tokens.append(sub)
            else:
                content_tokens.append(sub)

    ordered = time_tokens + content_tokens + question_tokens
    # Deduplicate consecutive identical tokens
    deduped: List[str] = []
    for tok in ordered:
        if not deduped or deduped[-1] != tok:
            deduped.append(tok)

    return " ".join(deduped)


def gloss_to_sentence_rules(gloss_input: str | Sequence[str], lang: str = "id") -> str:
    """
    B0 Rule-Based Sentence Constructor (mirrors `web/js/sentence.js` Bab 7.4):
      - Deduplicate consecutive identical glosses
      - Capitalize first word, lowercase subsequent words
      - Add comma after leading time word (Pagi, Siang, Sore, Malam, Kemarin, Besok)
      - End with '?' if sequence contains a question word (Apa, Siapa, Kapan, Di mana,
        Mengapa, Bagaimana, Berapa), else '.'
    """
    if isinstance(gloss_input, str):
        # Preserve two-word glosses 'di mana' and 'terima kasih'
        norm_str = re.sub(r"\bdi\s+mana\b", "di_mana", gloss_input.strip(), flags=re.IGNORECASE)
        norm_str = re.sub(r"\bterima\s+kasih\b", "terima_kasih", norm_str, flags=re.IGNORECASE)
        raw_list = [w.replace("_", " ") for w in norm_str.split() if w.strip()]
    else:
        raw_list = [str(w).strip().replace("_", " ") for w in gloss_input if str(w).strip()]

    if not raw_list:
        return ""

    # Deduplicate consecutive identical glosses (case-insensitive)
    tokens: List[str] = []
    for w in raw_list:
        if not tokens or tokens[-1].lower() != w.lower():
            tokens.append(w.lower())

    if lang.lower() in ("fil", "tl", "ph"):
        fil_map = {
            "halo": "kumusta",
            "terima kasih": "salamat",
            "maaf": "paumanhin",
            "tolong": "pakiusap",
            "saya": "ako ay",
            "kamu": "ikaw ay",
            "guru": "sa guro",
            "teman": "kaibigan",
            "mau": "gustong",
            "sudah": "tapos nang",
            "belum": "hindi pa",
            "bisa": "kaya",
            "tidak": "hindi",
            "ada": "mayroon",
            "belajar": "mag-aral",
            "paham": "nakakaintindi",
            "tanya": "magtanong",
            "baca": "magbasa",
            "tulis": "magsulat",
            "jawab": "sumagot",
            "buku": "ng libro",
            "tugas": "ng takdang-aralin",
            "kelas": "sa klase",
            "sekolah": "sa paaralan",
            "apa": "ano",
            "siapa": "sino",
            "di mana": "saan",
            "dimana": "saan",
            "kapan": "kailan",
            "bagaimana": "paano",
            "baik": "mabuti",
            "benar": "tama",
            "salah": "mali",
        }
        tokens = [fil_map.get(t, t) for t in tokens]

    time_set = {"pagi", "siang", "sore", "malam", "kemarin", "besok", "sekarang"}
    question_set = {"apa", "siapa", "kapan", "di mana", "dimana", "mengapa", "kenapa", "bagaimana", "berapa"}

    has_question = any(t in question_set for t in tokens)
    first_word = tokens[0].capitalize()
    rest_words = tokens[1:]

    if tokens[0] in time_set and rest_words:
        body = f"{first_word}, " + " ".join(rest_words)
    else:
        body = " ".join([first_word] + rest_words)

    punct = "?" if has_question else "."
    return f"{body}{punct}"
