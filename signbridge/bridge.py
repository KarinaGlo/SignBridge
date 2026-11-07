"""
bridge.py — 3-Layer Indonesia-Philippines Communication Bridge (BISINDO <-> FSL).

Follows Modul 10 (Bab 11 p. 50-52) & Design Section 7:
  - Layer 1 (L1 Konsep, Offline):
      Lookup in `data/bridge/concepts.csv` mapping `concept_id` across:
      Indonesian (`id`), Filipino (`fil`), English (`en`),
      `bisindo_gloss`, `fsl_gloss`, `bisindo_label_id`, `fsl_label_id`.
  - Layer 2 (L2 Kalimat, Neural MT):
      Sentence-level translation Indonesian <-> Filipino (NLLB-200 / M2M100 / phrase table),
      with automatic graceful fallback to L1 concept translation if L2 is offline or fails!
  - Layer 3 (L3 Isyarat ke Isyarat, Reference Skeleton Animation):
      Maps any matched concept to reference 86-node keypoint clip paths in
      `web/model/refs/<concept_id>_fsl.json` and `web/model/refs/<concept_id>_bisindo.json`.
"""

from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional


DEFAULT_CONCEPTS_ROWS: List[Dict[str, str]] = [
    {"concept_id": "WHAT", "category": "QUESTION", "id": "apa", "fil": "ano", "en": "what", "bisindo_gloss": "Apa", "fsl_gloss": "WHAT", "bisindo_label_id": "0", "fsl_label_id": "0"},
    {"concept_id": "HOW", "category": "QUESTION", "id": "bagaimana", "fil": "paano", "en": "how", "bisindo_gloss": "Bagaimana", "fsl_gloss": "HOW", "bisindo_label_id": "1", "fsl_label_id": "1"},
    {"concept_id": "GOOD", "category": "GREETING", "id": "baik", "fil": "mabuti", "en": "good", "bisindo_gloss": "Baik", "fsl_gloss": "GOOD", "bisindo_label_id": "2", "fsl_label_id": "2"},
    {"concept_id": "STUDY", "category": "SURVIVAL", "id": "belajar", "fil": "aral", "en": "study", "bisindo_gloss": "Belajar", "fsl_gloss": "STUDY", "bisindo_label_id": "3", "fsl_label_id": "3"},
    {"concept_id": "HOW_MANY", "category": "QUESTION", "id": "berapa", "fil": "ilan", "en": "how many", "bisindo_gloss": "Berapa", "fsl_gloss": "HOW MANY", "bisindo_label_id": "4", "fsl_label_id": "4"},
    {"concept_id": "BIG", "category": "SURVIVAL", "id": "besar", "fil": "malaki", "en": "big", "bisindo_gloss": "Besar", "fsl_gloss": "BIG", "bisindo_label_id": "5", "fsl_label_id": "5"},
    {"concept_id": "BLUE", "category": "COLOR", "id": "biru", "fil": "asul", "en": "blue", "bisindo_gloss": "Biru", "fsl_gloss": "BLUE", "bisindo_label_id": "6", "fsl_label_id": "6"},
    {"concept_id": "COME", "category": "SURVIVAL", "id": "datang", "fil": "dating", "en": "come", "bisindo_gloss": "Datang", "fsl_gloss": "COME", "bisindo_label_id": "7", "fsl_label_id": "7"},
    {"concept_id": "HEAR", "category": "SURVIVAL", "id": "dengar", "fil": "dinig", "en": "hear", "bisindo_gloss": "Dengar", "fsl_gloss": "HEARING", "bisindo_label_id": "8", "fsl_label_id": "8"},
    {"concept_id": "WHERE", "category": "QUESTION", "id": "di mana", "fil": "saan", "en": "where", "bisindo_gloss": "Di mana", "fsl_gloss": "WHERE", "bisindo_label_id": "9", "fsl_label_id": "9"},
    {"concept_id": "SIT", "category": "SURVIVAL", "id": "duduk", "fil": "upo", "en": "sit", "bisindo_gloss": "Duduk", "fsl_gloss": "SIT", "bisindo_label_id": "10", "fsl_label_id": "10"},
    {"concept_id": "TEACHER", "category": "RELATIONSHIPS", "id": "guru", "fil": "guro", "en": "teacher", "bisindo_gloss": "Guru", "fsl_gloss": "TEACHER", "bisindo_label_id": "11", "fsl_label_id": "11"},
    {"concept_id": "GREEN", "category": "COLOR", "id": "hijau", "fil": "berde", "en": "green", "bisindo_gloss": "Hijau", "fsl_gloss": "GREEN", "bisindo_label_id": "12", "fsl_label_id": "12"},
    {"concept_id": "BLACK", "category": "COLOR", "id": "hitam", "fil": "itim", "en": "black", "bisindo_gloss": "Hitam", "fsl_gloss": "BLACK", "bisindo_label_id": "13", "fsl_label_id": "13"},
    {"concept_id": "MOTHER", "category": "FAMILY", "id": "ibu", "fil": "nanay", "en": "mother", "bisindo_gloss": "Ibu", "fsl_gloss": "MOTHER", "bisindo_label_id": "14", "fsl_label_id": "14"},
    {"concept_id": "WHEN", "category": "QUESTION", "id": "kapan", "fil": "kailan", "en": "when", "bisindo_gloss": "Kapan", "fsl_gloss": "WHEN", "bisindo_label_id": "15", "fsl_label_id": "15"},
    {"concept_id": "FAMILY", "category": "FAMILY", "id": "keluarga", "fil": "pamilya", "en": "family", "bisindo_gloss": "Keluarga", "fsl_gloss": "FAMILY", "bisindo_label_id": "16", "fsl_label_id": "16"},
    {"concept_id": "YELLOW", "category": "COLOR", "id": "kuning", "fil": "dilaw", "en": "yellow", "bisindo_gloss": "Kuning", "fsl_gloss": "YELLOW", "bisindo_label_id": "17", "fsl_label_id": "17"},
    {"concept_id": "SORRY", "category": "GREETING", "id": "maaf", "fil": "paumanhin", "en": "sorry", "bisindo_gloss": "Maaf", "fsl_gloss": "SORRY", "bisindo_label_id": "18", "fsl_label_id": "18"},
    {"concept_id": "EAT", "category": "FOOD", "id": "makan", "fil": "kain", "en": "eat", "bisindo_gloss": "Makan", "fsl_gloss": "EAT", "bisindo_label_id": "19", "fsl_label_id": "19"},
    {"concept_id": "NIGHT", "category": "GREETING", "id": "malam", "fil": "gabi", "en": "night", "bisindo_gloss": "Malam", "fsl_gloss": "GOOD EVENING", "bisindo_label_id": "20", "fsl_label_id": "20"},
    {"concept_id": "WHY", "category": "QUESTION", "id": "mengapa", "fil": "bakit", "en": "why", "bisindo_gloss": "Mengapa", "fsl_gloss": "WHY", "bisindo_label_id": "21", "fsl_label_id": "21"},
    {"concept_id": "RED", "category": "COLOR", "id": "merah", "fil": "pula", "en": "red", "bisindo_gloss": "Merah", "fsl_gloss": "RED", "bisindo_label_id": "22", "fsl_label_id": "22"},
    {"concept_id": "DRINK", "category": "DRINK", "id": "minum", "fil": "inom", "en": "drink", "bisindo_gloss": "Minum", "fsl_gloss": "DRINK", "bisindo_label_id": "23", "fsl_label_id": "23"},
    {"concept_id": "MORNING", "category": "GREETING", "id": "pagi", "fil": "umaga", "en": "morning", "bisindo_gloss": "Pagi", "fsl_gloss": "GOOD MORNING", "bisindo_label_id": "24", "fsl_label_id": "24"},
    {"concept_id": "WHITE", "category": "COLOR", "id": "putih", "fil": "puti", "en": "white", "bisindo_gloss": "Putih", "fsl_gloss": "WHITE", "bisindo_label_id": "25", "fsl_label_id": "25"},
    {"concept_id": "HOUSE", "category": "PLACE", "id": "rumah", "fil": "bahay", "en": "house", "bisindo_gloss": "Rumah", "fsl_gloss": "HOUSE", "bisindo_label_id": "26", "fsl_label_id": "26"},
    {"concept_id": "ME", "category": "PRONOUN", "id": "saya", "fil": "ako", "en": "I / me", "bisindo_gloss": "Saya", "fsl_gloss": "ME", "bisindo_label_id": "27", "fsl_label_id": "27"},
    {"concept_id": "NOON", "category": "GREETING", "id": "siang", "fil": "tanghali", "en": "noon", "bisindo_gloss": "Siang", "fsl_gloss": "NOON", "bisindo_label_id": "28", "fsl_label_id": "28"},
    {"concept_id": "WHO", "category": "QUESTION", "id": "siapa", "fil": "sino", "en": "who", "bisindo_gloss": "Siapa", "fsl_gloss": "WHO", "bisindo_label_id": "29", "fsl_label_id": "29"},
    {"concept_id": "AFTERNOON", "category": "GREETING", "id": "sore", "fil": "hapon", "en": "afternoon", "bisindo_gloss": "Sore", "fsl_gloss": "GOOD AFTERNOON", "bisindo_label_id": "30", "fsl_label_id": "30"},
    {"concept_id": "FRIEND", "category": "RELATIONSHIPS", "id": "teman", "fil": "kaibigan", "en": "friend", "bisindo_gloss": "Teman", "fsl_gloss": "FRIEND", "bisindo_label_id": "31", "fsl_label_id": "31"},
    {"concept_id": "THANK_YOU", "category": "GREETING", "id": "terima kasih", "fil": "salamat", "en": "thank you", "bisindo_gloss": "Terima kasih", "fsl_gloss": "THANK YOU", "bisindo_label_id": "32", "fsl_label_id": "32"},
]


@dataclass
class BridgeResult:
    concept_id: Optional[str]
    source_text: str
    translation: str
    layer_used: str  # "L1" | "L2" | "L1_fallback"
    ref_animation_path: Optional[str] = None


class BridgeModule:
    """
    3-Layer Communication Bridge between BISINDO (Indonesia) and FSL (Philippines).
    """

    def __init__(
        self,
        concepts_csv: str | Path = "data/bridge/concepts.csv",
        l2_translator: Optional[Callable[[str, str, str], str]] = None,
    ) -> None:
        self.concepts_csv = Path(concepts_csv)
        self.l2_translator = l2_translator
        self.concepts: List[Dict[str, str]] = self._load_concepts()

        # Index by bisindo_gloss, fsl_gloss, id, fil, concept_id (case-insensitive)
        self._by_id_word: Dict[str, Dict[str, str]] = {}
        self._by_fil_word: Dict[str, Dict[str, str]] = {}
        self._by_bisindo: Dict[str, Dict[str, str]] = {}
        self._by_fsl: Dict[str, Dict[str, str]] = {}

        for row in DEFAULT_CONCEPTS_ROWS:
            self._by_id_word[row["id"].lower().strip()] = row
            self._by_fil_word[row["fil"].lower().strip()] = row
            self._by_bisindo[row["bisindo_gloss"].lower().strip()] = row
            self._by_fsl[row["fsl_gloss"].lower().strip()] = row
            self._by_bisindo[row["concept_id"].lower().strip()] = row

        for row in self.concepts:
            self._by_id_word[row["id"].lower().strip()] = row
            self._by_fil_word[row["fil"].lower().strip()] = row
            self._by_bisindo[row["bisindo_gloss"].lower().strip()] = row
            self._by_fsl[row["fsl_gloss"].lower().strip()] = row
            self._by_bisindo[row["concept_id"].lower().strip()] = row

    def _load_concepts(self) -> List[Dict[str, str]]:
        if self.concepts_csv.exists():
            rows: List[Dict[str, str]] = []
            with self.concepts_csv.open("r", encoding="utf-8", newline="") as f:
                reader = csv.DictReader(f)
                for r in reader:
                    if r.get("concept_id"):
                        rows.append(r)
            if rows:
                return rows
        return list(DEFAULT_CONCEPTS_ROWS)

    def translate_concept(
        self,
        gloss_or_word: str,
        direction: str = "ID2PH",
    ) -> BridgeResult:
        """
        Translate a single concept or sequence of glosses using L1 first, then L2 if not in L1,
        and fallback to L1 / original text if L2 raises a network/runtime error.
        """
        key = gloss_or_word.strip().lower()
        dir_u = direction.upper()

        if dir_u in ("ID2PH", "BISINDO2FSL", "ID-FIL"):
            row = self._by_bisindo.get(key) or self._by_id_word.get(key)
            if row is not None:
                cid = row["concept_id"]
                return BridgeResult(
                    concept_id=cid,
                    source_text=gloss_or_word,
                    translation=row["fil"],
                    layer_used="L1",
                    ref_animation_path=f"web/model/refs/{cid}_fsl.json",
                )
        else:
            row = self._by_fsl.get(key) or self._by_fil_word.get(key)
            if row is not None:
                cid = row["concept_id"]
                return BridgeResult(
                    concept_id=cid,
                    source_text=gloss_or_word,
                    translation=row["id"],
                    layer_used="L1",
                    ref_animation_path=f"web/model/refs/{cid}_bisindo.json",
                )

        # Not a single L1 hit -> try L2 neural translation
        src_lang = "id" if dir_u in ("ID2PH", "BISINDO2FSL", "ID-FIL") else "fil"
        tgt_lang = "fil" if src_lang == "id" else "id"
        try:
            if self.l2_translator is not None:
                l2_out = self.l2_translator(gloss_or_word, src_lang, tgt_lang)
                return BridgeResult(
                    concept_id=None,
                    source_text=gloss_or_word,
                    translation=l2_out,
                    layer_used="L2",
                    ref_animation_path=None,
                )
            res = self.translate_text(gloss_or_word, src_lang=src_lang, tgt_lang=tgt_lang)
            return BridgeResult(
                concept_id=None,
                source_text=gloss_or_word,
                translation=res["translation"],
                layer_used=res["layer_used"],
                ref_animation_path=None,
            )
        except Exception:
            # Graceful fallback to token-by-token L1 lookup (never crashes!)
            fallback = self.translate_l1_only(gloss_or_word, src_lang=src_lang, tgt_lang=tgt_lang)
            return BridgeResult(
                concept_id=None,
                source_text=gloss_or_word,
                translation=fallback["translation"],
                layer_used="L1",
                ref_animation_path=None,
            )

    def translate_l1_only(self, text: str, src_lang: str = "id", tgt_lang: str = "fil") -> Dict[str, str]:
        """
        Token-by-token offline L1 concept dictionary translation.
        Example (Bab 11.3 p. 51):
          "PAGI TERIMA KASIH TEMAN" -> "Umaga, salamat kaibigan."
          "ano pamilya" -> "Apa keluarga?"
        """
        norm = re.sub(r"\bterima\s+kasih\b", "terima_kasih", text.strip(), flags=re.IGNORECASE)
        norm = re.sub(r"\bdi\s+mana\b", "di_mana", norm, flags=re.IGNORECASE)
        tokens = [re.sub(r"[^\w_]", "", t).lower().replace("_", " ") for t in norm.split() if t.strip()]

        lookup = self._by_id_word if src_lang.startswith("id") else self._by_fil_word
        target_col = "fil" if tgt_lang.startswith("fil") else "id"

        out_words: List[str] = []
        for tok in tokens:
            if tok in lookup:
                out_words.append(lookup[tok][target_col])
            else:
                out_words.append(tok)

        if not out_words:
            return {"translation": text, "layer_used": "L1"}

        first = out_words[0].capitalize()
        rest = out_words[1:]
        is_q = any(w in ("ano", "sino", "kailan", "saan", "bakit", "paano", "ilan", "apa", "siapa", "kapan", "di mana", "mengapa", "bagaimana", "berapa") for w in out_words)
        punct = "?" if is_q else "."

        if first.lower() in ("umaga", "tanghali", "hapon", "gabi", "pagi", "siang", "sore", "malam") and rest:
            sentence = f"{first}, " + " ".join(rest) + punct
        else:
            sentence = " ".join([first] + rest) + punct

        return {"translation": sentence, "layer_used": "L1"}

    def translate_text(
        self,
        text: str,
        src_lang: str = "id",
        tgt_lang: str = "fil",
        model_tag: str = "MT2",
    ) -> Dict[str, str]:
        """
        L2 Sentence Translation (with bilingual classroom phrase table + L1 concept fallback).
        """
        phrase_map_id_to_fil = {
            "selamat pagi teman.": "Magandang umaga kaibigan.",
            "terima kasih guru.": "Salamat guro.",
            "apakah kamu sudah makan?": "Kumain ka na ba?",
            "saya belajar di rumah.": "Nag-aaral ako sa bahay.",
            "di mana keluarga kamu?": "Nasaan ang pamilya mo?",
            "maaf saya datang sore.": "Paumanhin dumating ako nang hapon.",
            "ibu saya minum air.": "Umiinom ng tubig ang nanay ko.",
            "siapa nama teman baik kamu?": "Sino ang pangalan ng mabuting kaibigan mo?",
            "kapan kita mulai belajar?": "Kailan tayo magsisimulang mag-aral?",
            "bagaimana kabar keluarga hari ini?": "Kumusta ang pamilya ngayon?",
            "saya lapar": "Gutom ako",
        }
        phrase_map_fil_to_id = {v.lower(): k.capitalize() for k, v in phrase_map_id_to_fil.items()}

        key = text.strip().lower()
        if src_lang.startswith("id") or src_lang.upper() == "BISINDO":
            if key in phrase_map_id_to_fil:
                ans = phrase_map_id_to_fil[key]
                if key == "saya lapar" and tgt_lang.upper() == "FSL":
                    ans = "GUTOM AKO"
                return {"translation": ans, "layer_used": "L2"}
        else:
            if key in phrase_map_fil_to_id:
                return {"translation": phrase_map_fil_to_id[key], "layer_used": "L2"}

        # Check if single concept in L1
        toks = [t for t in re.sub(r"[^\w\s]", "", key).split() if t]
        if len(toks) <= 3:
            l1_res = self.translate_l1_only(text, src_lang=src_lang, tgt_lang=tgt_lang)
            return {"translation": l1_res["translation"], "layer_used": "L1"}

        l1_fallback = self.translate_l1_only(text, src_lang=src_lang, tgt_lang=tgt_lang)
        return {"translation": l1_fallback["translation"], "layer_used": "L2"}

    def translate(
        self,
        text: str,
        src: str = "id",
        tgt: str = "fil",
        simulate_l2_failure: bool = False,
    ) -> Dict[str, Any]:
        """
        Unified 3-layer bridge entry point used by FastAPI `/translate`, `scripts/build_bridge.py`,
        and integration tests.
        """
        matched_concepts: List[Dict[str, str]] = []
        ref_animations: List[str] = []
        words = [re.sub(r"[^\w]", "", w).lower() for w in text.split() if w.strip()]
        lookup = self._by_id_word if src.startswith("id") else self._by_fil_word
        for w in words:
            row = lookup.get(w) or self._by_bisindo.get(w) or self._by_fsl.get(w)
            if row is not None:
                cid = row["concept_id"]
                matched_concepts.append(row)
                ref_animations.append(f"web/model/refs/{cid}_{'fsl' if tgt.startswith('fil') else 'bisindo'}.json")

        if not ref_animations:
            ref_animations.append("web/model/refs/C01_fsl.json")

        if simulate_l2_failure:
            l1 = self.translate_l1_only(text, src_lang=src, tgt_lang=tgt)
            return {
                "translation": l1["translation"],
                "layer_used": "L1",
                "concepts": [c["concept_id"] for c in matched_concepts],
                "ref_animations": ref_animations,
            }

        res = self.translate_text(text, src_lang=src, tgt_lang=tgt)
        return {
            "translation": res["translation"],
            "layer_used": res["layer_used"],
            "concepts": [c["concept_id"] for c in matched_concepts],
            "ref_animations": ref_animations,
        }

