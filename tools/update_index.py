#!/usr/bin/env python3
"""
update_index.py
Update bible_index.json and bible_index.js (file:// friendly).

Usage:
  python3 tools/update_index.py <book_slug> "<Book Name>" <chapters> [--order N] [--testament OT]
Example:
  python3 tools/update_index.py song-of-songs "Song of Songs" 8 --order 22 --testament OT
"""
import argparse, json, pathlib

ap = argparse.ArgumentParser()
ap.add_argument("slug")
ap.add_argument("name")
ap.add_argument("chapters", type=int)
ap.add_argument("--order", type=int, default=999)
ap.add_argument("--testament", default="OT")
args = ap.parse_args()

root = pathlib.Path(__file__).resolve().parents[1]
idx_path = root / "bible_index.json"
idx = json.loads(idx_path.read_text(encoding="utf-8"))

idx.setdefault("spec_version", "1.2")
books = idx.setdefault("books", [])

found = None
for b in books:
    if b.get("slug") == args.slug:
        found = b
        break
if not found:
    found = {"name": args.name, "slug": args.slug, "chapters": args.chapters, "order": args.order, "testament": args.testament}
    books.append(found)
else:
    found.update({"name": args.name, "chapters": args.chapters, "order": found.get("order", args.order), "testament": found.get("testament", args.testament)})

# sort by order then name
books.sort(key=lambda x: (x.get("order", 999), x.get("name","")))

idx_path.write_text(json.dumps(idx, ensure_ascii=False, indent=2), encoding="utf-8")
(root / "bible_index.js").write_text("window.BIBLE_INDEX = " + json.dumps(idx, ensure_ascii=False, indent=2) + ";\n", encoding="utf-8")
print("Updated", idx_path, "and bible_index.js")
