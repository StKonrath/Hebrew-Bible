#!/usr/bin/env python3
"""
add_chapter_bundle.py

One-command chapter installer for the Hebrew Bible Learning Site.

Given a chapter JSON, this tool will:
  1) Normalize it to Spec v1.4
  2) Create the chapter folder: books/<book_slug>/<NN or NNN>/
  3) Copy the shared chapter template into that folder
  4) Write data.json + data.js
  5) Ensure the book exists in bible_index.json
  6) Backfill semantic fields, lexicon, grammar (best-effort)
  7) Validate chapter against the JSON schema

Requirements: pip install jsonschema

Usage:
  python3 tools/add_chapter_bundle.py --in /path/to/data.json
  python3 tools/add_chapter_bundle.py --book psalms --chapter 140 --in /path/to/data.json
"""
import argparse, pathlib, re, shutil, datetime
import sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from utils import (
    load_json, save_json, write_data_js, pad_chapter,
    load_bible_index, save_bible_index,
    ROOT, BOOKS_DIR, SPEC_VERSION,
)

SCHEMA_PATH = ROOT / "schema" / "chapter.schema.json"
TEMPLATE_PATH = ROOT / "assets" / "chapter.html"

def die(msg, code=2):
    print(msg)
    raise SystemExit(code)

def write_json_dry(p, obj, dry):
    if dry:
        print("DRY: write", p)
        return
    save_json(p, obj)

def ensure_dir(p, dry):
    if dry:
        print("DRY: mkdir -p", p)
        return
    p.mkdir(parents=True, exist_ok=True)

def normalize_top_level(data):
    data["spec_version"] = SPEC_VERSION
    data.setdefault("tagset", {"name": "ETCBC-like", "version": "1.0"})
    data["ref_system"] = data.get("ref_system") or "MT"
    data.setdefault("lexicon", [])
    data.setdefault("grammar", [])
    data.setdefault("exercises", [])
    data.setdefault("annotations", [])
    data["generated_at"] = data.get("generated_at") or str(datetime.date.today())

def normalize_book_fields(data, args):
    book = data.get("book")
    if isinstance(book, dict):
        book_name = book.get("name") or data.get("book_name") or args.book_name
        book_slug = book.get("slug") or data.get("book_slug") or args.book
    else:
        book_name = book or data.get("book_name") or args.book_name
        book_slug = data.get("book_slug") or args.book

    if not book_slug:
        if not book_name:
            die("Cannot determine book/book_slug. Provide --book and/or --book-name.")
        book_slug = re.sub(r"[^a-z0-9]+", "-", book_name.lower()).strip("-")

    if not book_name:
        book_name = args.book_name or book_slug.replace("-", " ").title()

    ch = data.get("chapter") or args.chapter
    if not ch:
        v0 = (data.get("verses") or [{}])[0]
        ref = v0.get("ref", "")
        try:
            ch = int(str(ref).split(":")[0])
        except Exception:
            die("Cannot determine chapter number. Provide --chapter or include chapter in JSON.")
    ch = int(ch)

    data["book"] = book_name
    data["book_slug"] = book_slug
    data["chapter"] = ch
    return book_slug, book_name, ch

def normalize_verses(data):
    verses = data.get("verses") or []
    ch = int(data.get("chapter") or 0)
    out = []
    for i, v in enumerate(verses, start=1):
        ref = v.get("ref")
        if not ref and "n" in v:
            ref = f"{ch}:{int(v['n'])}"
        if not ref:
            ref = f"{ch}:{i}"
        he = v.get("he") or v.get("heb") or v.get("text") or ""
        out.append({
            "ref": str(ref),
            "he": str(he),
            "en": str(v.get("en", "")),
            "tr": str(v.get("tr", "")),
            "tokens": v.get("tokens") or [],
            "semantic_summary": v.get("semantic_summary") or [],
        })
    data["verses"] = out

def find_template(path_opt):
    if path_opt:
        p = pathlib.Path(path_opt)
        if not p.is_absolute():
            p = (ROOT / p).resolve()
        if not p.exists():
            die(f"Template not found: {p}")
        return p
    if TEMPLATE_PATH.exists():
        return TEMPLATE_PATH
    matches = list(ROOT.glob("books/*/*/index.html"))
    if not matches:
        die("No chapter index.html template found in repo.")
    return matches[0]

def update_index(book_slug, book_name, args, dry):
    if args.no_index:
        return
    idx = load_bible_index()
    idx["spec_version"] = SPEC_VERSION
    books = idx.setdefault("books", [])
    existing = next((b for b in books if b.get("slug") == book_slug), None)
    if existing:
        if args.chapters:
            existing["chapters"] = max(int(existing.get("chapters", 0)), int(args.chapters))
    else:
        chapters = int(args.chapters) if args.chapters else 1
        order = int(args.order) if args.order is not None else 999
        testament = args.testament or "OT"
        books.append({"name": book_name, "slug": book_slug, "chapters": chapters, "order": order, "testament": testament})
    idx["books"] = sorted(books, key=lambda x: (x.get("order", 999), x.get("name", "")))
    if dry:
        print("DRY: update bible_index")
    else:
        save_bible_index(idx)

def validate(path_json, args):
    if args.no_validate:
        return
    try:
        import jsonschema
    except ImportError:
        die("Missing dependency: jsonschema. Install with: pip install jsonschema")
    schema = load_json(SCHEMA_PATH)
    data = load_json(path_json)
    jsonschema.validate(instance=data, schema=schema)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", required=True, help="Input chapter JSON file")
    ap.add_argument("--book", default=None, help="Book slug (override)")
    ap.add_argument("--book-name", default=None, help="Book display name (override)")
    ap.add_argument("--chapter", type=int, default=None, help="Chapter number (override)")
    ap.add_argument("--template", default=None, help="Path to chapter index.html template")
    ap.add_argument("--chapters", type=int, default=None, help="If auto-adding book, chapter count")
    ap.add_argument("--order", type=int, default=None)
    ap.add_argument("--testament", default="OT", choices=["OT", "NT"])
    ap.add_argument("--no-index", action="store_true")
    ap.add_argument("--no-validate", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    inp = pathlib.Path(args.inp).resolve()
    if not inp.exists():
        die(f"Input not found: {inp}")

    data = load_json(inp)
    if args.book:
        data["book_slug"] = args.book
    if args.book_name:
        data["book"] = args.book_name
    if args.chapter:
        data["chapter"] = args.chapter

    normalize_top_level(data)
    book_slug, book_name, ch = normalize_book_fields(data, args)
    normalize_verses(data)

    chdir = BOOKS_DIR / book_slug / pad_chapter(ch)
    ensure_dir(chdir, args.dry_run)

    tpl = find_template(args.template)
    dst_index = chdir / "index.html"
    if args.dry_run:
        print("DRY: copy", tpl, "->", dst_index)
    else:
        shutil.copy2(tpl, dst_index)

    out_json = chdir / "data.json"
    write_json_dry(out_json, data, args.dry_run)

    if not args.dry_run:
        write_data_js(out_json)

    update_index(book_slug, book_name, args, args.dry_run)

    if not args.dry_run:
        # Backfill semantic fields before validation
        try:
            from backfill_semantics import patch_file as _patch_sem
            _patch_sem(out_json)
        except Exception:
            pass
        # Promote token data into teaching layers
        try:
            from promote_tokens_to_lexicon import patch_file as _patch_lex
            _patch_lex(out_json, force=False)
        except Exception:
            pass
        try:
            from seed_basic_grammar_notes import patch_file as _patch_gram
            _patch_gram(out_json, force=False)
        except Exception:
            pass
        validate(out_json, args)
        print("OK: installed", out_json)
    else:
        print("DRY: would validate", out_json)

if __name__ == "__main__":
    main()
