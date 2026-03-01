#!/usr/bin/env python3
"""
vocab_coverage.py

Reports vocabulary (lexicon) gloss coverage per chapter and optionally token-gloss coverage.

Usage:
  python3 tools/vocab_coverage.py --all
  python3 tools/vocab_coverage.py books/song-of-songs/02/data.json

Options:
  --all           scan all books/*/*/data.json
  --tokens        also report token-gloss coverage
  --min PCT       exit with code 2 if any chapter is below this lexicon gloss %
"""
import argparse, pathlib
from utils import load_json, infer_book_chapter, all_chapter_jsons

def pct(a, b):
    return (100.0 * a / b) if b else 0.0

def lexicon_stats(d):
    lex = d.get("lexicon") or []
    total = len(lex)
    with_gloss = sum(1 for x in lex if (x.get("gloss") or "").strip())
    return with_gloss, total

def token_stats(d):
    total = with_gloss = 0
    for v in (d.get("verses") or []):
        for t in (v.get("tokens") or []):
            total += 1
            if (t.get("gloss") or "").strip():
                with_gloss += 1
    return with_gloss, total

def row(slug, ch, lw, lt, tw=None, tt=None):
    base = f"{slug}/{ch}: lexicon {lw}/{lt} ({pct(lw, lt):5.1f}%)"
    if tw is not None and tt is not None:
        base += f" | tokens {tw}/{tt} ({pct(tw, tt):5.1f}%)"
    return base

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("path", nargs="?", help="Path to a chapter data.json")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--tokens", action="store_true")
    ap.add_argument("--min", type=float, default=None)
    args = ap.parse_args()

    if args.all:
        files = all_chapter_jsons()
    elif args.path:
        files = [pathlib.Path(args.path).resolve()]
    else:
        print("Usage: python3 tools/vocab_coverage.py --all | <path/to/data.json>")
        return 2

    failures = []
    for fp in files:
        d = load_json(fp)
        slug, ch = infer_book_chapter(fp)
        slug = slug or "?"
        ch = ch or "?"
        lw, lt = lexicon_stats(d)
        if args.tokens:
            tw, tt = token_stats(d)
            print(row(slug, ch, lw, lt, tw, tt))
        else:
            print(row(slug, ch, lw, lt))

        p = pct(lw, lt)
        if args.min is not None and p < args.min:
            failures.append((slug, ch, p))

    if failures:
        print("\nFAIL: Chapters below minimum lexicon coverage:")
        for slug, ch, p in failures:
            print(f"  - {slug}/{ch}: {p:.1f}% < {args.min:.1f}%")
        return 2
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
