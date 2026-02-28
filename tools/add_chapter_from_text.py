#!/usr/bin/env python3
"""
add_chapter_from_text.py
Bulk-ingest a chapter from a plain-text file into Spec v1.2 structure.

Input file format (recommended):
- First line: BOOK_SLUG=<slug>
- Second line: BOOK_NAME=<name>
- Third line: CHAPTER=<number>
- Then verses as:
  1 <TAB> Hebrew text
  2 <TAB> Hebrew text
  ...
If TAB is not present, the script tries to split at the first space after the number.

This script:
- creates books/<slug>/<NN>/ if missing
- writes data.json (structure) with Hebrew in verses
- writes data.js
NOTE: morphology/translation/transliteration/semantics are left blank for later fill,
unless you provide pre-filled JSON.

Usage:
  python3 tools/add_chapter_from_text.py input.txt
"""
import re, json, pathlib, sys, datetime

def parse_lines(lines):
    meta = {}
    verses = []
    for ln in lines:
        ln = ln.rstrip("\n")
        if not ln.strip(): 
            continue
        if "=" in ln and ln.split("=",1)[0] in ("BOOK_SLUG","BOOK_NAME","CHAPTER"):
            k,v = ln.split("=",1)
            meta[k]=v.strip()
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
    root = pathlib.Path(__file__).resolve().parents[1]
    chdir = root / "books" / slug / f"{chap:02d}"
    chdir.mkdir(parents=True, exist_ok=True)
    data = {
        "spec_version":"1.2",
        "tagset":{"name":"ETCBC-like","version":"1.0","notes":"features object follows ETCBC-style categories; 'morph' is derived for display."},
        "title":f"{name} {chap}",
        "book":name,
        "book_slug":slug,
        "chapter":chap,
        "ref_system":"MT",
        "verses":[{"ref":f"{chap}:{v}","he":t,"en":"","tr":"","tokens":[]} for v,t in verses],
        "lexicon":[],"grammar":[],"exercises":[],"annotations":[],
        "generated_at":str(datetime.date.today())
    }
    (chdir / "data.json").write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    (chdir / "data.js").write_text("window.__chapterData = " + json.dumps(data, ensure_ascii=False, indent=2) + ";\n", encoding="utf-8")
    print("Wrote", chdir / "data.json")
    print("Wrote", chdir / "data.js")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 tools/add_chapter_from_text.py input.txt")
        raise SystemExit(2)
    main()
