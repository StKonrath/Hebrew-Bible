#!/usr/bin/env python3
"""
scaffold_book.py
Create a new book folder with a TOC page and chapter folders.

Uses the shared templates at assets/book.html and assets/chapter.html.

Usage:
  python3 tools/scaffold_book.py <book_slug> "<Book Name>" <chapters>
Example:
  python3 tools/scaffold_book.py genesis "Genesis" 50
"""
import argparse, pathlib, shutil, datetime
from utils import save_json, write_data_js, pad_chapter, BOOKS_DIR, ROOT, SPEC_VERSION

ap = argparse.ArgumentParser()
ap.add_argument("slug")
ap.add_argument("name")
ap.add_argument("chapters", type=int)
args = ap.parse_args()

book_dir = BOOKS_DIR / args.slug
book_dir.mkdir(parents=True, exist_ok=True)

# Copy shared book TOC template
toc_path = book_dir / "index.html"
book_template = ROOT / "assets" / "book.html"
if not toc_path.exists():
    if book_template.exists():
        shutil.copy2(book_template, toc_path)
    else:
        raise SystemExit(f"Book template not found at {book_template}")

# Copy shared chapter template to each chapter folder
chapter_template = ROOT / "assets" / "chapter.html"
if not chapter_template.exists():
    raise SystemExit(f"Chapter template not found at {chapter_template}")

for ch in range(1, args.chapters + 1):
    ch_dir = book_dir / pad_chapter(ch)
    ch_dir.mkdir(parents=True, exist_ok=True)

    # Copy shared chapter index.html
    idxp = ch_dir / "index.html"
    if not idxp.exists():
        shutil.copy2(chapter_template, idxp)

    # Create stub data.json
    dj = ch_dir / "data.json"
    if not dj.exists():
        stub = {
            "spec_version": SPEC_VERSION,
            "tagset": {"name": "ETCBC-like", "version": "1.0"},
            "title": f"{args.name} {ch}",
            "book": args.name,
            "book_slug": args.slug,
            "chapter": ch,
            "ref_system": "MT",
            "verses": [],
            "lexicon": [],
            "grammar": [],
            "exercises": [],
            "annotations": [],
            "generated_at": str(datetime.date.today()),
        }
        save_json(dj, stub)

    # Generate data.js
    write_data_js(dj)

print("Scaffolded book:", args.slug, "with", args.chapters, "chapters")
