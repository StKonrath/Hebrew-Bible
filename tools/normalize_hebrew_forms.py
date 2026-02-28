#!/usr/bin/env python3
"""
normalize_hebrew_forms.py

Normalizes Hebrew strings in token.lemma and (optionally) lexicon lemmas by:
- NFC normalization
- removing cantillation marks (0591-05AF)
- stripping leading Hebrew combining marks (e.g., dagesh/vowel points) that can appear due to buggy prefix stripping

Usage:
  python3 tools/normalize_hebrew_forms.py --all
  python3 tools/normalize_hebrew_forms.py books/song-of-songs/02/data.json
"""
import argparse, json, pathlib, glob, unicodedata

ROOT = pathlib.Path(__file__).resolve().parents[1]

def normalize_hebrew(s: str) -> str:
    s = (s or "").strip()
    s = unicodedata.normalize("NFC", s)
    s = "".join(ch for ch in s if not (0x0591 <= ord(ch) <= 0x05AF))
    # strip leading punctuation + combining marks
    while s and (s[0] in "־–—" or s[0].isspace()):
        s = s[1:]
    while s and unicodedata.category(s[0]) == "Mn":
        s = s[1:]
    return s

def patch_file(fp: pathlib.Path) -> bool:
    data = json.loads(fp.read_text(encoding="utf-8"))
    changed = False

    for v in data.get("verses", []) or []:
        for t in v.get("tokens", []) or []:
            lem = t.get("lemma")
            if isinstance(lem, str):
                n = normalize_hebrew(lem)
                if n and n != lem:
                    t["lemma"] = n
                    changed = True
            surf = t.get("surface")
            if isinstance(surf, str):
                n = normalize_hebrew(surf)
                if n and n != surf:
                    t["surface"] = n
                    changed = True

    for entry in data.get("lexicon", []) or []:
        lem = entry.get("lemma")
        if isinstance(lem, str):
            n = normalize_hebrew(lem)
            if n and n != lem:
                entry["lemma"] = n
                changed = True

    if changed:
        fp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return changed

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("path", nargs="?", help="Path to data.json")
    ap.add_argument("--all", action="store_true")
    args = ap.parse_args()

    if args.all:
        files = glob.glob(str(ROOT / "books" / "*" / "*" / "data.json"))
        n=0
        for f in sorted(files):
            if patch_file(pathlib.Path(f)):
                n+=1
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
