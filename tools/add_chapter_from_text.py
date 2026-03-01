#!/usr/bin/env python3
"""
add_chapter_from_text.py
Bulk-ingest a chapter from a plain-text file into Spec v1.4 structure.

Input file format:
- BOOK_SLUG=<slug>
- BOOK_NAME=<name>
- CHAPTER=<number>
- Then verses as:  1 <TAB or space> Hebrew text

Usage:
  python3 tools/add_chapter_from_text.py input.txt
"""
import re, pathlib, sys, datetime
from utils import save_json, write_data_js, pad_chapter, BOOKS_DIR, SPEC_VERSION

def parse_lines(lines):
    meta = {}
    verses = []
    for ln in lines:
        ln = ln.rstrip("\n")
        if not ln.strip():
            continue
        if "=" in ln and ln.split("=", 1)[0] in ("BOOK_SLUG", "BOOK_NAME", "CHAPTER"):
            k, v = ln.split("=", 1)
            meta[k] = v.strip()
            continue
        m = re.match(r"^(\d+)\s+(.*)$", ln)
        if m:
            verses.append((int(m.group(1)), m.group(2).strip()))
    return meta, verses

def main():
    p = pathlib.Path(sys.argv[1]).resolve()
    lines = p.read_text(encoding="utf-8").splitlines()
    meta, verses = parse_lines(lines)
    slug = meta["BOOK_SLUG"]
    name = meta["BOOK_NAME"]
    chap = int(meta["CHAPTER"])
    chdir = BOOKS_DIR / slug / pad_chapter(chap)
    chdir.mkdir(parents=True, exist_ok=True)
    data = {
        "spec_version": SPEC_VERSION,
        "tagset": {"name": "ETCBC-like", "version": "1.0"},
        "title": f"{name} {chap}",
        "book": name,
        "book_slug": slug,
        "chapter": chap,
        "ref_system": "MT",
        "verses": [
            {"ref": f"{chap}:{v}", "he": t, "en": "", "tr": "", "tokens": [], "semantic_summary": []}
            for v, t in verses
        ],
        "lexicon": [],
        "grammar": [],
        "exercises": [],
        "annotations": [],
        "generated_at": str(datetime.date.today()),
    }
    out = chdir / "data.json"
    save_json(out, data)
    write_data_js(out)
    print("Wrote", out)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 tools/add_chapter_from_text.py input.txt")
        raise SystemExit(2)
    main()
