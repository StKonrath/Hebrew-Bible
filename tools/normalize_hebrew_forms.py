#!/usr/bin/env python3
"""
normalize_hebrew_forms.py

Normalizes Hebrew strings in token.lemma, token.surface, and lexicon lemmas by:
- NFC normalization
- removing cantillation marks (0591-05AF)
- stripping leading combining marks

Usage:
  python3 tools/normalize_hebrew_forms.py --all
  python3 tools/normalize_hebrew_forms.py books/song-of-songs/02/data.json
"""
import argparse, pathlib
from utils import load_json, save_json, normalize_hebrew, all_chapter_jsons

def patch_file(fp):
    data = load_json(fp)
    changed = False

    for v in (data.get("verses") or []):
        for t in (v.get("tokens") or []):
            for key in ("lemma", "surface"):
                val = t.get(key)
                if isinstance(val, str):
                    n = normalize_hebrew(val)
                    if n and n != val:
                        t[key] = n
                        changed = True

    for entry in (data.get("lexicon") or []):
        lem = entry.get("lemma")
        if isinstance(lem, str):
            n = normalize_hebrew(lem)
            if n and n != lem:
                entry["lemma"] = n
                changed = True

    if changed:
        save_json(fp, data)
    return changed

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("path", nargs="?", help="Path to data.json")
    ap.add_argument("--all", action="store_true")
    args = ap.parse_args()

    if args.all:
        n = sum(1 for f in all_chapter_jsons() if patch_file(f))
        print(f"OK: normalized {n} files")
        return
    if not args.path:
        raise SystemExit("Usage: normalize_hebrew_forms.py <path/to/data.json> | --all")
    fp = pathlib.Path(args.path).resolve()
    if not fp.exists():
        raise SystemExit(f"Not found: {fp}")
    changed = patch_file(fp)
    print("OK:", fp, "(changed)" if changed else "(no changes)")

if __name__ == "__main__":
    main()
