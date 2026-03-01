#!/usr/bin/env python3
"""
utils.py — Shared helpers for Hebrew Bible tooling (v1.4).

Consolidates duplicated logic: JSON I/O, path inference, Hebrew normalization,
glob-based batch processing, and data.js generation.
"""
import json, pathlib, glob, re, unicodedata, datetime

ROOT = pathlib.Path(__file__).resolve().parents[1]
BOOKS_DIR = ROOT / "books"
SPEC_VERSION = "1.4"

# ---------------------------------------------------------------------------
# JSON I/O
# ---------------------------------------------------------------------------

def load_json(p):
    """Load and parse a JSON file."""
    return json.loads(pathlib.Path(p).read_text(encoding="utf-8"))

def save_json(p, obj):
    """Write an object as pretty-printed JSON."""
    pathlib.Path(p).write_text(
        json.dumps(obj, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

# ---------------------------------------------------------------------------
# Path inference
# ---------------------------------------------------------------------------

def infer_book_chapter(fp):
    """
    Extract (book_slug, chapter_num) from a path like .../books/<slug>/<ch>/data.json.
    Returns (None, None) if the path doesn't match.
    """
    parts = pathlib.Path(fp).resolve().parts
    try:
        i = parts.index("books")
        slug = parts[i + 1]
        ch = int(parts[i + 2])
        return slug, ch
    except (ValueError, IndexError):
        return None, None

def title_case_slug(slug):
    """Convert a book slug to display name.  Handles multi-word titles."""
    special = {
        "song-of-songs": "Song of Songs",
        "1-samuel": "1 Samuel",
        "2-samuel": "2 Samuel",
        "1-kings": "1 Kings",
        "2-kings": "2 Kings",
        "1-chronicles": "1 Chronicles",
        "2-chronicles": "2 Chronicles",
    }
    if slug in special:
        return special[slug]
    return " ".join(w.capitalize() for w in slug.split("-"))

# ---------------------------------------------------------------------------
# Hebrew normalization
# ---------------------------------------------------------------------------

def normalize_hebrew(s):
    """NFC-normalize, strip cantillation marks and leading combining marks."""
    s = (s or "").strip()
    s = unicodedata.normalize("NFC", s)
    # Remove cantillation marks (U+0591–U+05AF)
    s = "".join(ch for ch in s if not (0x0591 <= ord(ch) <= 0x05AF))
    # Strip leading punctuation (maqaf, dashes) and spaces
    while s and (s[0] in "־–—" or s[0].isspace()):
        s = s[1:]
    # Strip leading combining marks
    while s and unicodedata.category(s[0]) == "Mn":
        s = s[1:]
    return s

def strip_niqqud(s):
    """Remove all Hebrew vowel points and cantillation marks."""
    if not s:
        return ""
    return re.sub(r"[\u0591-\u05BD\u05BF-\u05C7]", "", s)

# ---------------------------------------------------------------------------
# Batch helpers
# ---------------------------------------------------------------------------

def all_chapter_jsons():
    """Return sorted list of Path objects for every books/*/*/data.json."""
    return sorted(
        pathlib.Path(p) for p in glob.glob(str(BOOKS_DIR / "*" / "*" / "data.json"))
    )

def pad_chapter(n):
    """Zero-pad a chapter number: 2-digit for <100, 3-digit otherwise."""
    return f"{n:02d}" if n < 100 else f"{n:03d}"

# ---------------------------------------------------------------------------
# data.js generation
# ---------------------------------------------------------------------------

def write_data_js(json_path):
    """Generate data.js (window.__chapterData wrapper) next to a data.json."""
    p = pathlib.Path(json_path)
    obj = load_json(p)
    out = p.with_name("data.js")
    out.write_text(
        "window.__chapterData = "
        + json.dumps(obj, ensure_ascii=False, indent=2)
        + ";\n",
        encoding="utf-8",
    )
    return out

# ---------------------------------------------------------------------------
# Index helpers
# ---------------------------------------------------------------------------

def load_bible_index():
    return load_json(ROOT / "bible_index.json")

def save_bible_index(idx):
    save_json(ROOT / "bible_index.json", idx)
    (ROOT / "bible_index.js").write_text(
        "window.BIBLE_INDEX = "
        + json.dumps(idx, ensure_ascii=False, indent=2)
        + ";\n",
        encoding="utf-8",
    )
