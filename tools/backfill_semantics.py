#!/usr/bin/env python3
"""
backfill_semantics.py

Backfills required semantic fields to satisfy Spec v1.3 validation:
- verse.semantic_summary: [] if missing (or derived from token.semantic tags)
- token.semantic: [] if missing

Usage:
  python3 tools/backfill_semantics.py books/song-of-songs/01/data.json
  python3 tools/backfill_semantics.py --all
"""
import json, pathlib, sys, glob

ROOT = pathlib.Path(__file__).resolve().parents[1]

def load(p: pathlib.Path):
    return json.loads(p.read_text(encoding="utf-8"))

def save(p: pathlib.Path, obj):
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")

def derive_semantic_summary(verse: dict) -> list:
    tags = []
    for t in (verse.get("tokens") or []):
        for s in (t.get("semantic") or []):
            if s and s not in tags:
                tags.append(s)
    return tags

def patch_file(fp: pathlib.Path) -> bool:
    data = load(fp)
    changed = False

    verses = data.get("verses") or []
    for v in verses:
        v.setdefault("tokens", [])

        for t in v["tokens"]:
            if "semantic" not in t or t["semantic"] is None:
                t["semantic"] = []
                changed = True

        if "semantic_summary" not in v or v["semantic_summary"] is None:
            v["semantic_summary"] = derive_semantic_summary(v)
            changed = True

    if changed:
        save(fp, data)
    return changed

def main(argv):
    if len(argv) >= 2 and argv[1] == "--all":
        files = glob.glob(str(ROOT / "books" / "*" / "*" / "data.json"))
        n = 0
        for f in sorted(files):
            if patch_file(pathlib.Path(f)):
                n += 1
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
