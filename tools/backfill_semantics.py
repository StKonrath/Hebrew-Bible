#!/usr/bin/env python3
"""
backfill_semantics.py

Backfills required semantic fields to satisfy Spec v1.4 validation:
- verse.semantic_summary: [] if missing (or derived from token.semantic tags)
- token.semantic: [] if missing

Usage:
  python3 tools/backfill_semantics.py books/song-of-songs/01/data.json
  python3 tools/backfill_semantics.py --all
"""
import sys, pathlib
from utils import load_json, save_json, all_chapter_jsons

def derive_semantic_summary(verse):
    tags = []
    for t in (verse.get("tokens") or []):
        for s in (t.get("semantic") or []):
            if s and s not in tags:
                tags.append(s)
    return tags

def patch_file(fp):
    data = load_json(fp)
    changed = False
    for v in (data.get("verses") or []):
        v.setdefault("tokens", [])
        for t in v["tokens"]:
            if "semantic" not in t or t["semantic"] is None:
                t["semantic"] = []
                changed = True
        if "semantic_summary" not in v or v["semantic_summary"] is None:
            v["semantic_summary"] = derive_semantic_summary(v)
            changed = True
    if changed:
        save_json(fp, data)
    return changed

def main(argv):
    if len(argv) >= 2 and argv[1] == "--all":
        n = sum(1 for f in all_chapter_jsons() if patch_file(f))
        print(f"OK: patched {n} files")
        return 0
    if len(argv) < 2:
        print("Usage: python3 tools/backfill_semantics.py <path/to/data.json> | --all")
        return 2
    fp = pathlib.Path(argv[1]).resolve()
    if not fp.exists():
        print("Not found:", fp)
        return 2
    changed = patch_file(fp)
    print("OK:", fp, "(changed)" if changed else "(no changes)")
    return 0

if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
