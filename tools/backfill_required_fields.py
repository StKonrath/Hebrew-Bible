#!/usr/bin/env python3
"""
backfill_required_fields.py

Ensures all chapter data.json files meet Spec v1.4 top-level required fields.

It will add (if missing):
- spec_version, tagset, ref_system, generated_at
- book, book_slug, chapter: inferred from folder path
- lexicon, grammar, exercises, annotations: []

Usage:
  python3 tools/backfill_required_fields.py books/song-of-songs/03/data.json
  python3 tools/backfill_required_fields.py --all
"""
import sys, pathlib, datetime
from utils import (
    load_json, save_json, infer_book_chapter, title_case_slug,
    all_chapter_jsons, SPEC_VERSION,
)

def patch(fp):
    data = load_json(fp)
    changed = False

    slug, ch_num = infer_book_chapter(fp)

    defaults = {
        "spec_version": SPEC_VERSION,
        "tagset": {"name": "ETCBC-like", "version": "1.0"},
        "ref_system": "MT",
        "generated_at": str(datetime.date.today()),
    }
    for k, v in defaults.items():
        if data.get(k) is None:
            data[k] = v
            changed = True

    if slug and data.get("book_slug") is None:
        data["book_slug"] = slug
        changed = True
    if ch_num and data.get("chapter") is None:
        data["chapter"] = ch_num
        changed = True
    if data.get("book") is None:
        if isinstance(data.get("book"), dict) and data["book"].get("name"):
            data["book"] = data["book"]["name"]
        elif slug:
            data["book"] = title_case_slug(slug)
        changed = True

    for k in ("lexicon", "grammar", "exercises", "annotations"):
        if data.get(k) is None:
            data[k] = []
            changed = True

    if data.get("verses") is None:
        data["verses"] = []
        changed = True

    if changed:
        save_json(fp, data)
    return changed

def main(argv):
    if len(argv) >= 2 and argv[1] == "--all":
        n = sum(1 for f in all_chapter_jsons() if patch(f))
        print(f"OK: patched {n} files")
        return 0

    if len(argv) < 2:
        print("Usage: python3 tools/backfill_required_fields.py <path/to/data.json> | --all")
        return 2
    fp = pathlib.Path(argv[1]).resolve()
    if not fp.exists():
        print("Not found:", fp)
        return 2
    changed = patch(fp)
    print("OK:", fp, "(changed)" if changed else "(no changes)")
    return 0

if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
