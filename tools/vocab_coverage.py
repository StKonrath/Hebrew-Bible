#!/usr/bin/env python3
"""
vocab_coverage.py

Reports vocabulary (lexicon) gloss coverage per chapter and optionally token-gloss coverage.

Gloss coverage = percentage of lexicon entries that have a non-empty `gloss`.

Usage:
  python3 tools/vocab_coverage.py --all
  python3 tools/vocab_coverage.py books/song-of-songs/02/data.json

Options:
  --all           scan all books/*/*/data.json
  --tokens        also report token-gloss coverage (% tokens with non-empty gloss)
  --min PCT       exit with code 2 if any chapter is below this gloss coverage (e.g. --min 95)
"""
import argparse, json, pathlib, glob

ROOT = pathlib.Path(__file__).resolve().parents[1]

def load(fp: pathlib.Path):
    return json.loads(fp.read_text(encoding="utf-8"))

def pct(a: int, b: int) -> float:
    return (100.0 * a / b) if b else 0.0

def lexicon_stats(d: dict):
    lex = d.get("lexicon") or []
    total = len(lex)
    with_gloss = sum(1 for x in lex if (x.get("gloss") or "").strip())
    return with_gloss, total

def token_stats(d: dict):
    total = 0
    with_gloss = 0
    for v in (d.get("verses") or []):
        for t in (v.get("tokens") or []):
            total += 1
            if (t.get("gloss") or "").strip():
                with_gloss += 1
    return with_gloss, total

def infer_slug_ch(fp: pathlib.Path):
    parts = fp.parts
    try:
        i = parts.index("books")
        return parts[i+1], parts[i+2]
    except Exception:
        return "?", "?"

def row(slug, ch, lex_with, lex_total, tok_with=None, tok_total=None):
    base = f"{slug}/{ch}: lexicon {lex_with}/{lex_total} ({pct(lex_with, lex_total):5.1f}%)"
    if tok_with is not None and tok_total is not None:
        base += f" | tokens {tok_with}/{tok_total} ({pct(tok_with, tok_total):5.1f}%)"
    return base

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("path", nargs="?", help="Path to a chapter data.json")
    ap.add_argument("--all", action="store_true", help="Scan all chapters")
    ap.add_argument("--tokens", action="store_true", help="Also report token gloss coverage")
    ap.add_argument("--min", type=float, default=None, help="Fail if any chapter below this lexicon gloss %%")
    args = ap.parse_args()

    if args.all:
        files = [pathlib.Path(p) for p in glob.glob(str(ROOT / "books" / "*" / "*" / "data.json"))]
        files.sort()
    elif args.path:
        files = [pathlib.Path(args.path).resolve()]
    else:
        print("Usage: python3 tools/vocab_coverage.py --all | <path/to/data.json>")
        return 2

    failures = []
    for fp in files:
        d = load(fp)
        slug, ch = infer_slug_ch(fp)
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
