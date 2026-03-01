#!/usr/bin/env python3
"""normalize_grammar_items.py

Normalize grammar note objects to a consistent shape: {id, title, body}.
Converts legacy {topic, example, note} format.

Usage:
  python3 tools/normalize_grammar_items.py books/psalms/139/data.json
  python3 tools/normalize_grammar_items.py --all
"""
import argparse, pathlib, re
from utils import load_json, save_json, all_chapter_jsons

def slug(s):
    s = (s or "").strip().lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-") or "note"

def normalize_item(it, i):
    if not isinstance(it, dict):
        return {"id": f"note-{i:02d}", "title": "Note", "body": str(it)}
    if "title" in it and "body" in it and "id" in it:
        return it
    if "topic" in it:
        title = it.get("topic") or "Grammar note"
        example = it.get("example")
        note = it.get("note") or ""
        body = note
        if example:
            body = (body + "\n\nExample: " + example).strip()
        return {"id": slug(title), "title": title, "body": body}
    title = it.get("title") or it.get("id") or f"Note {i}"
    body = it.get("body") or it.get("note") or ""
    return {"id": it.get("id") or slug(title), "title": title, "body": body}

def patch_file(fp):
    data = load_json(fp)
    g = data.get("grammar") or []
    data["grammar"] = [normalize_item(it, i + 1) for i, it in enumerate(g)]
    save_json(fp, data)
    return True

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("path", nargs="?")
    ap.add_argument("--all", action="store_true")
    args = ap.parse_args()
    if args.all:
        for f in all_chapter_jsons():
            patch_file(f)
        print("OK: normalized grammar items in all chapters")
        return 0
    if not args.path:
        print("Usage: normalize_grammar_items.py <path/to/data.json> | --all")
        return 2
    fp = pathlib.Path(args.path).resolve()
    if not fp.exists():
        print("Not found:", fp)
        return 2
    patch_file(fp)
    print("OK:", fp)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
