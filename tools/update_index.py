#!/usr/bin/env python3
"""
update_index.py — Update bible_index.json and bible_index.js.

Usage:
  python3 tools/update_index.py <book_slug> "<Book Name>" <chapters> [--order N] [--testament OT]
Example:
  python3 tools/update_index.py song-of-songs "Song of Songs" 8 --order 22 --testament OT
"""
import argparse
from utils import load_bible_index, save_bible_index, SPEC_VERSION

ap = argparse.ArgumentParser()
ap.add_argument("slug")
ap.add_argument("name")
ap.add_argument("chapters", type=int)
ap.add_argument("--order", type=int, default=999)
ap.add_argument("--testament", default="OT")
args = ap.parse_args()

idx = load_bible_index()
idx["spec_version"] = SPEC_VERSION
books = idx.setdefault("books", [])

found = next((b for b in books if b.get("slug") == args.slug), None)
if not found:
    found = {
        "name": args.name,
        "slug": args.slug,
        "chapters": args.chapters,
        "order": args.order,
        "testament": args.testament,
    }
    books.append(found)
else:
    found["name"] = args.name
    found["chapters"] = args.chapters
    found.setdefault("order", args.order)
    found.setdefault("testament", args.testament)

books.sort(key=lambda x: (x.get("order", 999), x.get("name", "")))
save_bible_index(idx)
print("Updated bible_index.json and bible_index.js")
