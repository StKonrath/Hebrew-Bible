#!/usr/bin/env python3
"""
generate_chapter.py — Generate complete Spec v1.4 data.json files from
compact Hebrew + English verse input.

Input format (one or more chapters per file):
  === <chapter_number> ===
  <verse>|<hebrew_text>|<english_translation>
  ...

Metadata header (optional, once at top of file):
  BOOK_SLUG=psalms
  BOOK_NAME=Psalms

Usage:
  python3 tools/generate_chapter.py input.txt [--install] [--book psalms] [--book-name Psalms]
  python3 tools/generate_chapter.py --dir /path/to/text_files/ --install
"""
import argparse
import datetime
import json
import os
import pathlib
import re
import subprocess
import sys
import unicodedata

SCRIPT_DIR = pathlib.Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(SCRIPT_DIR))
from utils import (
    save_json, write_data_js, pad_chapter, strip_niqqud,
    normalize_hebrew, BOOKS_DIR, SPEC_VERSION, load_json,
)

# ── Load gloss map ──
GLOSS_MAP = json.loads((SCRIPT_DIR / "gloss_map.json").read_text("utf-8"))

# ── Hebrew function words (vocalized forms) ──
FUNC_WORDS = {
    "לֹא": {"root": "—", "pos": "neg", "morph": "NEG", "gloss": "not"},
    "אַל": {"root": "—", "pos": "neg", "morph": "NEG", "gloss": "do not"},
    "כִּי": {"root": "—", "pos": "part", "morph": "PART;type=disc", "gloss": "for/because", "features": {"type": "disc"}},
    "אִם": {"root": "—", "pos": "conj", "morph": "CONJ;type=cond", "gloss": "if", "features": {"type": "cond"}},
    "אוֹ": {"root": "—", "pos": "conj", "morph": "CONJ", "gloss": "or"},
    "אֲשֶׁר": {"root": "—", "pos": "rel", "morph": "REL", "gloss": "who/that"},
    "גַּם": {"root": "—", "pos": "adv", "morph": "ADV", "gloss": "also/even"},
    "עַתָּה": {"root": "—", "pos": "adv", "morph": "ADV", "gloss": "now"},
    "הִנֵּה": {"root": "—", "pos": "part", "morph": "PART", "gloss": "behold"},
    "פֶּן": {"root": "—", "pos": "conj", "morph": "CONJ", "gloss": "lest"},
    "לָמָּה": {"root": "—", "pos": "interrog", "morph": "INTERROG", "gloss": "why"},
    "מַה": {"root": "—", "pos": "interrog", "morph": "INTERROG", "gloss": "what"},
    "מִי": {"root": "—", "pos": "interrog", "morph": "INTERROG", "gloss": "who"},
    "אֵיךְ": {"root": "—", "pos": "interrog", "morph": "INTERROG", "gloss": "how"},
    "אֵיפֹה": {"root": "—", "pos": "interrog", "morph": "INTERROG", "gloss": "where"},
    "כֵּן": {"root": "כן", "pos": "adv", "morph": "ADV", "gloss": "so/thus"},
    "שָׁם": {"root": "שם", "pos": "adv", "morph": "ADV", "gloss": "there"},
    "אָז": {"root": "—", "pos": "adv", "morph": "ADV", "gloss": "then"},
    "עוֹד": {"root": "עוד", "pos": "adv", "morph": "ADV", "gloss": "still/yet"},
    "מְאֹד": {"root": "—", "pos": "adv", "morph": "ADV", "gloss": "very/exceedingly"},
    "אֶת": {"root": "—", "pos": "part", "morph": "PART;type=obj", "gloss": "(object marker)", "features": {"type": "obj"}},
    "עַל": {"root": "—", "pos": "prep", "morph": "PREP", "gloss": "upon/over"},
    "אֶל": {"root": "—", "pos": "prep", "morph": "PREP", "gloss": "to/toward"},
    "מִן": {"root": "—", "pos": "prep", "morph": "PREP", "gloss": "from"},
    "עִם": {"root": "—", "pos": "prep", "morph": "PREP", "gloss": "with"},
    "בֵּין": {"root": "—", "pos": "prep", "morph": "PREP", "gloss": "between"},
    "תַּחַת": {"root": "—", "pos": "prep", "morph": "PREP", "gloss": "under"},
    "אַחַר": {"root": "—", "pos": "prep", "morph": "PREP", "gloss": "after"},
    "אַחֲרֵי": {"root": "—", "pos": "prep", "morph": "PREP", "gloss": "after"},
    "לִפְנֵי": {"root": "—", "pos": "prep", "morph": "PREP", "gloss": "before"},
    "עַד": {"root": "—", "pos": "prep", "morph": "PREP", "gloss": "until/to"},
    "נֶגֶד": {"root": "—", "pos": "prep", "morph": "PREP", "gloss": "before/opposite"},
    "סֶלָה": {"root": "—", "pos": "part", "morph": "PART", "gloss": "Selah"},
    "אֲנִי": {"root": "—", "pos": "pron", "morph": "PRON;p=1sg", "gloss": "I", "features": {"person": "1", "number": "sg"}},
    "אָנֹכִי": {"root": "—", "pos": "pron", "morph": "PRON;p=1sg", "gloss": "I", "features": {"person": "1", "number": "sg"}},
    "אַתָּה": {"root": "—", "pos": "pron", "morph": "PRON;p=2ms", "gloss": "you (m.sg.)", "features": {"person": "2", "gender": "m", "number": "sg"}},
    "הוּא": {"root": "—", "pos": "pron", "morph": "PRON;p=3ms", "gloss": "he", "features": {"person": "3", "gender": "m", "number": "sg"}},
    "הִיא": {"root": "—", "pos": "pron", "morph": "PRON;p=3fs", "gloss": "she", "features": {"person": "3", "gender": "f", "number": "sg"}},
    "אֲנַחְנוּ": {"root": "—", "pos": "pron", "morph": "PRON;p=1pl", "gloss": "we", "features": {"person": "1", "number": "pl"}},
    "הֵם": {"root": "—", "pos": "pron", "morph": "PRON;p=3mp", "gloss": "they", "features": {"person": "3", "gender": "m", "number": "pl"}},
    "הֵמָּה": {"root": "—", "pos": "pron", "morph": "PRON;p=3mp", "gloss": "they", "features": {"person": "3", "gender": "m", "number": "pl"}},
    "כֹּל": {"root": "כל", "pos": "noun", "morph": "NOUN", "gloss": "all/every"},
    "כָּל": {"root": "כל", "pos": "noun", "morph": "NOUN", "gloss": "all/every"},
    "יוֹמָם": {"root": "יום", "pos": "adv", "morph": "ADV", "gloss": "by day", "semantic": ["TIME"]},
    "לָיְלָה": {"root": "לילה", "pos": "noun", "morph": "NOUN", "gloss": "night", "semantic": ["TIME"]},
    "לַמְנַצֵּחַ": {"root": "נצח", "pos": "noun", "morph": "NOUN", "gloss": "for the director"},
    "מִזְמוֹר": {"root": "זמר", "pos": "noun", "morph": "NOUN", "gloss": "a psalm"},
    "לְדָוִד": {"root": "—", "pos": "propn", "morph": "PROPN", "gloss": "of David"},
    "שִׁיר": {"root": "שׁיר", "pos": "noun", "morph": "NOUN", "gloss": "a song"},
}

# ── Proper nouns ──
PROPER_NOUNS = {
    "יהוה": {"root": "—", "pos": "propn", "morph": "PROPN;type=deity", "gloss": "YHWH", "features": {"type": "deity"}, "semantic": ["PRAISE", "SYMBOL"]},
    "אלהים": {"root": "אלה", "pos": "propn", "morph": "PROPN;type=deity", "gloss": "God", "features": {"type": "deity"}, "semantic": ["PRAISE"]},
    "ישראל": {"root": "—", "pos": "propn", "morph": "PROPN", "gloss": "Israel"},
    "ציון": {"root": "—", "pos": "propn", "morph": "PROPN", "gloss": "Zion"},
    "ירושלם": {"root": "—", "pos": "propn", "morph": "PROPN", "gloss": "Jerusalem"},
    "דוד": {"root": "—", "pos": "propn", "morph": "PROPN", "gloss": "David"},
    "משה": {"root": "—", "pos": "propn", "morph": "PROPN", "gloss": "Moses"},
    "יעקב": {"root": "—", "pos": "propn", "morph": "PROPN", "gloss": "Jacob"},
    "אברהם": {"root": "—", "pos": "propn", "morph": "PROPN", "gloss": "Abraham"},
    "מצרים": {"root": "—", "pos": "propn", "morph": "PROPN", "gloss": "Egypt"},
    "בבל": {"root": "—", "pos": "propn", "morph": "PROPN", "gloss": "Babylon"},
    "לבנון": {"root": "—", "pos": "propn", "morph": "PROPN", "gloss": "Lebanon"},
}

# ── Common Hebrew roots → gloss (consonantal) ──
ROOT_GLOSSES = {
    "הלך": "walk/go", "אמר": "say", "נתן": "give", "עשה": "do/make",
    "בוא": "come", "ראה": "see", "ידע": "know", "שמע": "hear",
    "דבר": "speak", "קרא": "call/read", "שוב": "return", "ישב": "sit/dwell",
    "עלה": "go up", "ירד": "go down", "יצא": "go out", "שלח": "send",
    "לקח": "take", "שים": "put/set", "עמד": "stand", "קום": "rise/stand",
    "מות": "die", "חיה": "live", "אכל": "eat", "שתה": "drink",
    "כתב": "write", "ספר": "count/tell", "שיר": "sing", "זמר": "sing praises",
    "הלל": "praise", "ידה": "give thanks", "ברך": "bless", "קדש": "be holy",
    "טהר": "be pure", "חטא": "sin", "שפט": "judge", "צדק": "be righteous",
    "רשע": "be wicked", "ישע": "save", "גאל": "redeem", "פדה": "ransom",
    "נצל": "deliver", "עזר": "help", "בטח": "trust", "חסה": "take refuge",
    "שמר": "keep/guard", "נצר": "watch/preserve", "סתר": "hide",
    "גלה": "reveal", "פתח": "open", "סגר": "close/shut", "בנה": "build",
    "נפל": "fall", "רום": "be high/exalted", "שפל": "be low/humble",
    "מלך": "reign/be king", "משל": "rule", "עבד": "serve", "יכל": "be able",
    "חפץ": "delight", "אהב": "love", "שנא": "hate", "ירא": "fear",
    "בכה": "weep", "שמח": "rejoice", "גיל": "be glad", "רנן": "shout for joy",
    "צעק": "cry out", "קרב": "come near", "רחק": "be far", "חנן": "be gracious",
    "רחם": "have mercy", "סלח": "forgive", "נשא": "lift/carry/forgive",
    "שבר": "break", "רפא": "heal", "חלה": "be sick", "נחם": "comfort",
    "זכר": "remember", "שכח": "forget", "למד": "learn/teach", "בין": "understand",
    "חכם": "be wise", "חשב": "think/reckon", "יעץ": "counsel/advise",
    "ברא": "create", "יצר": "form", "כון": "establish", "יסד": "found",
    "מלא": "fill", "שלם": "be complete/at peace", "תמם": "be complete",
    "חדש": "be new/renew", "ישן": "be old/sleep", "חזק": "be strong",
    "גבר": "be mighty", "כבד": "be heavy/honored", "אור": "give light",
    "חשך": "be dark", "נגד": "tell/declare", "ספר": "recount/tell",
    "הגה": "meditate/mutter", "שיח": "meditate/muse", "צוה": "command",
    "נאם": "declare/oracle", "ענה": "answer/sing", "שאל": "ask",
    "דרש": "seek/inquire", "בקש": "seek", "מצא": "find",
    "שלך": "cast/throw", "נטה": "stretch out", "פרש": "spread out",
    "כסה": "cover", "לבש": "clothe/put on", "חגר": "gird",
    "רכב": "ride", "רוץ": "run", "מהר": "hurry", "נוס": "flee",
    "רדף": "pursue", "לחם": "fight", "נכה": "strike", "הרג": "kill",
    "שחת": "destroy", "כרת": "cut off", "אבד": "perish/destroy",
    "שבה": "take captive", "פלט": "escape/deliver", "מלט": "escape",
    "ירש": "inherit/possess", "חלק": "divide", "נחל": "inherit",
    "זרע": "sow", "קצר": "reap/harvest", "נטע": "plant",
    "רעה": "shepherd/tend", "נהל": "lead", "נחה": "guide/lead",
    "סבב": "surround", "כתר": "surround", "צור": "besiege",
    "שכן": "dwell", "גור": "sojourn", "נוח": "rest",
    "ישע": "save/deliver", "עזב": "abandon/forsake", "נטש": "forsake",
    "חנה": "encamp", "צבא": "serve/wage war",
    "שבע": "swear", "נדר": "vow", "כפר": "atone",
    "זבח": "sacrifice", "קטר": "burn incense",
    "שקר": "deal falsely", "כזב": "lie/be false", "מרד": "rebel",
    "נאף": "commit adultery", "גנב": "steal",
    "טוב": "be good", "רע": "be evil/bad", "ישר": "be upright/straight",
    "נכון": "be established", "נאמן": "be faithful",
    "חסד": "show kindness", "אמן": "be firm/faithful",
    "גדל": "be great", "קטן": "be small", "רב": "be many/great",
    "מעט": "be few/little",
    "שב": "return", "פנה": "turn",
    "נגע": "touch/strike", "נגף": "strike/plague",
    "שפך": "pour out", "מוג": "melt", "נמס": "melt",
    "סלע": "rock", "צור": "rock/cliff",
    "ארץ": "land/earth", "שמים": "heavens/sky",
}

# ── Semantic tag rules (root → likely tags) ──
SEMANTIC_RULES = {
    "הלל": ["PRAISE"], "ידה": ["PRAISE"], "ברך": ["PRAISE"],
    "זמר": ["PRAISE"], "שיר": ["PRAISE"], "רנן": ["PRAISE"],
    "גיל": ["PRAISE"], "שמח": ["PRAISE"],
    "מלך": ["AUTHORITY"], "משל": ["AUTHORITY"], "שפט": ["AUTHORITY"],
    "צוה": ["AUTHORITY"], "גבר": ["AUTHORITY"],
    "חטא": ["DAMAGE"], "רשע": ["DAMAGE"], "שחת": ["DAMAGE"],
    "אבד": ["DAMAGE"], "הרג": ["DAMAGE"], "נכה": ["DAMAGE"],
    "שבר": ["DAMAGE"], "כרת": ["DAMAGE"],
    "ישע": ["SALVATION"], "גאל": ["SALVATION"], "פדה": ["SALVATION"],
    "נצל": ["SALVATION"], "עזר": ["SALVATION"], "פלט": ["SALVATION"],
    "מלט": ["SALVATION"],
    "חסד": ["KINDNESS"], "רחם": ["KINDNESS"], "חנן": ["KINDNESS"],
    "סלח": ["KINDNESS"],
    "ירא": ["FEAR"], "פחד": ["FEAR"], "חרד": ["FEAR"],
    "בטח": ["TRUST"], "חסה": ["TRUST"], "קוה": ["TRUST"],
    "הלך": ["MOTION"], "בוא": ["MOTION"], "ירד": ["MOTION"],
    "עלה": ["MOTION"], "יצא": ["MOTION"], "רוץ": ["MOTION"],
    "נוס": ["MOTION"], "רדף": ["MOTION"], "קום": ["MOTION"],
    "עמד": ["MOTION"], "ישב": ["MOTION"],
    "דבר": ["SPEECH"], "אמר": ["SPEECH"], "קרא": ["SPEECH"],
    "ענה": ["SPEECH"], "שאל": ["SPEECH"], "נאם": ["SPEECH"],
    "נגד": ["SPEECH"],
    "ידע": ["COGNITION"], "בין": ["COGNITION"], "חכם": ["COGNITION"],
    "חשב": ["COGNITION"], "זכר": ["COGNITION"], "שכח": ["COGNITION"],
    "הגה": ["COGNITION"], "למד": ["COGNITION"],
    "ברא": ["CREATION"], "יצר": ["CREATION"], "כון": ["CREATION"],
    "יסד": ["CREATION"], "בנה": ["CREATION"],
    "מים": ["NATURE"], "ים": ["NATURE"], "נהר": ["NATURE"],
    "הר": ["NATURE"], "שמש": ["NATURE"], "ירח": ["NATURE"],
    "רוח": ["WEATHER", "NATURE"], "גשם": ["WEATHER"],
    "עץ": ["FLORA"], "פרי": ["FLORA"], "עשב": ["FLORA"],
}


def _strip(s):
    """Strip niqqud for lookup."""
    return re.sub(r"[\u0591-\u05C7]", "", s)


def _strip_cantillation(s):
    """Remove cantillation marks only (keep vowels)."""
    return re.sub(r"[\u0591-\u05AF]", "", unicodedata.normalize("NFC", s))


# ── Hebrew prefix patterns (ordered by length, longest first) ──
PREFIX_TABLE = [
    ("וּבְ", "conj+prep", "and in"),
    ("וּכְ", "conj+prep", "and like"),
    ("וּלְ", "conj+prep", "and to"),
    ("וּמִ", "conj+prep", "and from"),
    ("וְהַ", "conj+art", "and the"),
    ("וְבַ", "conj+prep+art", "and in the"),
    ("וְלַ", "conj+prep+art", "and to the"),
    ("וּבַ", "conj+prep+art", "and in the"),
    ("וּלַ", "conj+prep+art", "and to the"),
    ("בַּ", "prep+art", "in the"),
    ("לַ", "prep+art", "to the"),
    ("מֵהַ", "prep+art", "from the"),
    ("כַּ", "prep+art", "like the"),
    ("הַ", "art", "the"),
    ("וְ", "conj", "and"),
    ("וּ", "conj", "and"),
    ("וָ", "conj", "and"),
    ("בְּ", "prep", "in"),
    ("בִּ", "prep", "in"),
    ("כְּ", "prep", "like/as"),
    ("כִּ", "prep", "like/as"),
    ("לְ", "prep", "to/for"),
    ("לִ", "prep", "to/for"),
    ("מִ", "prep", "from"),
    ("מֵ", "prep", "from"),
    ("שֶׁ", "rel", "that"),
]


def lookup_root(consonantal):
    """Look up a consonantal form in our databases.  Returns (root, gloss) or None."""
    # Try proper nouns first
    if consonantal in PROPER_NOUNS:
        return PROPER_NOUNS[consonantal]
    # Try gloss map
    if consonantal in GLOSS_MAP:
        return {"root": consonantal, "gloss": GLOSS_MAP[consonantal]}
    # Try root glosses
    if consonantal in ROOT_GLOSSES:
        return {"root": consonantal, "gloss": ROOT_GLOSSES[consonantal]}
    return None


def analyze_token(surface):
    """Analyze a Hebrew token.  Returns dict with root, pos, morph, gloss, features, semantic."""
    result = {
        "root": "?",
        "pos": "noun",
        "morph": "NOUN",
        "gloss": "",
        "features": {},
        "semantic": [],
    }

    clean = _strip_cantillation(surface)

    # 1. Check vocalized function words
    if clean in FUNC_WORDS:
        entry = FUNC_WORDS[clean]
        return {
            "root": entry.get("root", "—"),
            "pos": entry["pos"],
            "morph": entry["morph"],
            "gloss": entry["gloss"],
            "features": entry.get("features", {}),
            "semantic": entry.get("semantic", []),
        }

    consonantal = _strip(surface)

    # 2. Check proper nouns (consonantal)
    if consonantal in PROPER_NOUNS:
        entry = PROPER_NOUNS[consonantal]
        return {
            "root": entry.get("root", "—"),
            "pos": entry["pos"],
            "morph": entry["morph"],
            "gloss": entry["gloss"],
            "features": entry.get("features", {}),
            "semantic": entry.get("semantic", []),
        }

    # 3. Direct consonantal lookup
    info = lookup_root(consonantal)
    if info and info.get("gloss"):
        root = info.get("root", consonantal)
        result["root"] = root
        result["gloss"] = info["gloss"]
        result["semantic"] = SEMANTIC_RULES.get(root, [])
        return result

    # 4. Try stripping prefixes
    for prefix_voweled, ptype, pgloss in PREFIX_TABLE:
        if clean.startswith(prefix_voweled) and len(clean) > len(prefix_voweled) + 1:
            remainder = clean[len(prefix_voweled):]
            remainder_cons = _strip(remainder)
            info = lookup_root(remainder_cons)
            if info and info.get("gloss"):
                root = info.get("root", remainder_cons)
                result["root"] = root
                result["gloss"] = f"{pgloss} {info['gloss']}"
                result["semantic"] = SEMANTIC_RULES.get(root, [])
                return result

    # 5. Try consonantal prefix stripping
    cons_prefixes = [
        ("ו", "and"), ("ב", "in"), ("כ", "like"), ("ל", "to/for"),
        ("מ", "from"), ("ה", "the"), ("ש", "that"),
    ]
    for cp, cg in cons_prefixes:
        if consonantal.startswith(cp) and len(consonantal) > 2:
            rest = consonantal[1:]
            info = lookup_root(rest)
            if info and info.get("gloss"):
                root = info.get("root", rest)
                result["root"] = root
                result["gloss"] = f"{cg} {info['gloss']}"
                result["semantic"] = SEMANTIC_RULES.get(root, [])
                return result

    # 6. Try removing common suffixes and look up
    for suffix in ["ים", "ות", "י", "ך", "ו", "ם", "ן", "נו", "הם", "הן"]:
        if consonantal.endswith(suffix) and len(consonantal) > len(suffix) + 1:
            stem = consonantal[:-len(suffix)]
            info = lookup_root(stem)
            if info and info.get("gloss"):
                root = info.get("root", stem)
                result["root"] = root
                result["gloss"] = info["gloss"]
                result["semantic"] = SEMANTIC_RULES.get(root, [])
                return result

    # 7. Fallback: look up in gloss map (consonantal)
    if consonantal in GLOSS_MAP:
        result["root"] = consonantal
        result["gloss"] = GLOSS_MAP[consonantal]
        return result

    # 8. Unknown
    return result


def tokenize_verse(hebrew_text):
    """Split Hebrew verse into tokens, handling maqaf."""
    text = _strip_cantillation(hebrew_text.strip())
    # Split on spaces
    raw_tokens = text.split()
    tokens = []
    for rt in raw_tokens:
        if not rt:
            continue
        # Split on maqaf (U+05BE ־) — keep each part as a separate token
        parts = rt.split("־")
        tokens.extend(p for p in parts if p)
    return tokens


def generate_transliteration(hebrew_text):
    """Generate a basic transliteration placeholder."""
    # This is a simplified placeholder — full transliteration is complex
    return ""


def build_chapter_data(book_slug, book_name, chapter, verses):
    """
    Build a complete Spec v1.4 data.json from verse data.

    verses: list of (verse_num, hebrew_text, english_text)
    """
    verse_objects = []
    all_lemmas = {}  # lemma → token info for lexicon

    for vnum, he_text, en_text in verses:
        ref = f"{chapter}:{vnum}"
        surface_tokens = tokenize_verse(he_text)
        token_objects = []
        verse_semantics = set()

        for tidx, surface in enumerate(surface_tokens, start=1):
            token_id = f"{book_slug}.{pad_chapter(chapter)}.{vnum:02d}.t{tidx:03d}"
            analysis = analyze_token(surface)

            tok = {
                "id": token_id,
                "surface": surface,
                "lemma": surface,
                "root": analysis["root"],
                "pos": analysis["pos"],
                "features": analysis.get("features", {}),
                "morph": analysis["morph"],
                "gloss": analysis["gloss"],
                "semantic": analysis.get("semantic", []),
            }
            token_objects.append(tok)
            verse_semantics.update(analysis.get("semantic", []))

            # Collect for lexicon
            lemma_key = _strip(surface)
            if lemma_key not in all_lemmas and analysis["gloss"]:
                all_lemmas[lemma_key] = {
                    "lemma": surface,
                    "root": analysis["root"],
                    "pos": analysis["pos"],
                    "gloss": analysis["gloss"],
                }

        verse_obj = {
            "ref": ref,
            "he": _strip_cantillation(he_text.strip()),
            "en": en_text.strip(),
            "tr": generate_transliteration(he_text),
            "tokens": token_objects,
            "semantic_summary": sorted(verse_semantics),
        }
        verse_objects.append(verse_obj)

    # Build lexicon from collected lemmas (deduplicate, limit to content words)
    lexicon = []
    seen_roots = set()
    for info in all_lemmas.values():
        root = info["root"]
        if root in ("—", "?", "") or root in seen_roots:
            continue
        seen_roots.add(root)
        lexicon.append({
            "lemma": info["lemma"],
            "root": root,
            "pos": info["pos"],
            "gloss": info["gloss"],
        })

    data = {
        "spec_version": SPEC_VERSION,
        "tagset": {"name": "ETCBC-like", "version": "1.0"},
        "ref_system": "MT",
        "generated_at": str(datetime.date.today()),
        "book": book_name,
        "book_slug": book_slug,
        "chapter": chapter,
        "title": f"{book_name} {chapter}",
        "verses": verse_objects,
        "lexicon": lexicon,
        "grammar": [],
        "exercises": [],
        "annotations": [],
    }
    return data


def parse_input_file(filepath):
    """
    Parse input file.  Returns list of (chapter_num, [(verse, hebrew, english)]).
    """
    lines = pathlib.Path(filepath).read_text("utf-8").splitlines()
    meta = {}
    chapters = []
    current_chapter = None
    current_verses = []

    for line in lines:
        line = line.rstrip()
        if not line.strip():
            continue

        # Metadata header
        if "=" in line and line.split("=", 1)[0] in ("BOOK_SLUG", "BOOK_NAME"):
            k, v = line.split("=", 1)
            meta[k.strip()] = v.strip()
            continue

        # Chapter marker
        m = re.match(r"^===\s*(\d+)\s*===$", line.strip())
        if m:
            if current_chapter is not None and current_verses:
                chapters.append((current_chapter, current_verses))
            current_chapter = int(m.group(1))
            current_verses = []
            continue

        # Verse line: <num>|<hebrew>|<english>
        m = re.match(r"^(\d+)\|(.+?)\|(.*)$", line)
        if m:
            vnum = int(m.group(1))
            he = m.group(2).strip()
            en = m.group(3).strip()
            current_verses.append((vnum, he, en))
            continue

    # Don't forget the last chapter
    if current_chapter is not None and current_verses:
        chapters.append((current_chapter, current_verses))

    return meta, chapters


def main():
    parser = argparse.ArgumentParser(description="Generate chapter data.json from Hebrew+English text")
    parser.add_argument("input", nargs="?", help="Input text file")
    parser.add_argument("--dir", help="Process all .txt files in a directory")
    parser.add_argument("--book", default="psalms", help="Book slug (default: psalms)")
    parser.add_argument("--book-name", default="Psalms", help="Book display name")
    parser.add_argument("--install", action="store_true", help="Run add_chapter_bundle.py after generating")
    parser.add_argument("--dry-run", action="store_true", help="Print stats without writing files")
    args = parser.parse_args()

    input_files = []
    if args.dir:
        d = pathlib.Path(args.dir)
        input_files = sorted(d.glob("*.txt"))
    elif args.input:
        input_files = [pathlib.Path(args.input)]
    else:
        parser.error("Provide an input file or --dir")

    total_chapters = 0
    for fpath in input_files:
        meta, chapters = parse_input_file(fpath)
        book_slug = meta.get("BOOK_SLUG", args.book)
        book_name = meta.get("BOOK_NAME", args.book_name)

        for ch_num, verses in chapters:
            data = build_chapter_data(book_slug, book_name, ch_num, verses)

            if args.dry_run:
                total_tokens = sum(len(v["tokens"]) for v in data["verses"])
                unknown = sum(1 for v in data["verses"] for t in v["tokens"] if t["root"] == "?")
                print(f"  {book_name} {ch_num}: {len(verses)} verses, {total_tokens} tokens, {unknown} unknown roots")
                total_chapters += 1
                continue

            # Write to temp file and optionally install
            tmp = pathlib.Path(f"/tmp/{book_slug}_{ch_num:03d}.json")
            save_json(tmp, data)

            if args.install:
                result = subprocess.run(
                    ["python3", str(SCRIPT_DIR / "add_chapter_bundle.py"), "--in", str(tmp)],
                    capture_output=True, text=True,
                )
                if result.returncode == 0:
                    print(f"OK: {book_name} {ch_num} ({len(verses)} verses)")
                else:
                    print(f"FAIL: {book_name} {ch_num}: {result.stderr.strip()}")
            else:
                # Write directly
                ch_dir = BOOKS_DIR / book_slug / pad_chapter(ch_num)
                ch_dir.mkdir(parents=True, exist_ok=True)
                out = ch_dir / "data.json"
                save_json(out, data)
                write_data_js(out)
                # Copy template
                tmpl = ROOT / "assets" / "chapter.html"
                if tmpl.exists():
                    import shutil
                    shutil.copy2(str(tmpl), str(ch_dir / "index.html"))
                print(f"OK: {out}")

            total_chapters += 1

    print(f"\nDone: {total_chapters} chapters processed.")


if __name__ == "__main__":
    main()
