#!/usr/bin/env python3
"""
add_chapter_bundle.py

One-command chapter installer for the Hebrew Bible Learning Site.

Given a chapter JSON (from ChatGPT or elsewhere), this tool will:
  1) Normalize it to Spec v1.3 (best-effort)
  2) Create the chapter folder: books/<book_slug>/<NN or NNN>/
  3) Copy a chapter renderer index.html template into that folder
  4) Write data.json
  5) Generate data.js (file:// friendly wrapper)
  6) Ensure the book exists in bible_index.json (optional auto-add)
  7) Regenerate bible_index.js
  8) Validate chapter against schema/chapter.schema.json

Requirements:
  pip install jsonschema

Usage:
  python3 tools/add_chapter_bundle.py --in /path/to/data.json
  python3 tools/add_chapter_bundle.py --book psalms --chapter 140 --in /path/to/data.json

Options:
  --template <path>    Use this index.html as chapter renderer template
  --book-name <name>   If auto-adding a book, use this name (default: title-cased slug)
  --chapters <n>       If auto-adding a book, set chapter count (default: 1)
  --order <n>          If auto-adding a book, set order (default: 999)
  --testament OT|NT    If auto-adding a book, set testament (default: OT)
  --no-index           Do not update bible_index.json/js
  --no-validate        Skip schema validation (not recommended)
  --dry-run            Print actions without writing files

Notes:
- The renderer builds titles/breadcrumbs/SEO automatically; do not embed formatting logic in JSON.
"""
import argparse, json, pathlib, re, shutil, datetime
import sys
sys.path.insert(0, str((pathlib.Path(__file__).resolve().parent)))

ROOT = pathlib.Path(__file__).resolve().parents[1]
BOOKS_DIR = ROOT / "books"
SCHEMA_PATH = ROOT / "schema" / "chapter.schema.json"
INDEX_JSON = ROOT / "bible_index.json"
INDEX_JS = ROOT / "bible_index.js"

def die(msg: str, code: int = 2):
    print(msg)
    raise SystemExit(code)

def load_json(p: pathlib.Path):
    return json.loads(p.read_text(encoding="utf-8"))

def write_json(p: pathlib.Path, obj, dry: bool):
    if dry:
        print("DRY: write", p)
        return
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")

def ensure_dir(p: pathlib.Path, dry: bool):
    if dry:
        print("DRY: mkdir -p", p)
        return
    p.mkdir(parents=True, exist_ok=True)

def pad_num(n: int) -> str:
    return f"{n:02d}" if n < 100 else f"{n:03d}"

def normalize_top_level(data: dict):
    data["spec_version"] = "1.3"
    data.setdefault("tagset", {"name": "ETCBC-like", "version": "1.0"})
    data["ref_system"] = data.get("ref_system") or "MT"
    data.setdefault("lexicon", [])
    data.setdefault("grammar", [])
    data.setdefault("exercises", [])
    data.setdefault("annotations", [])
    data["generated_at"] = data.get("generated_at") or str(datetime.date.today())

def normalize_book_fields(data: dict, args):
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

def normalize_verses(data: dict):
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
            "semantic_summary": v.get("semantic_summary") or []
        })
    data["verses"] = out

def make_data_js(data: dict, out_path: pathlib.Path, dry: bool):
    if dry:
        print("DRY: write", out_path)
        return
    out_path.write_text("window.__chapterData = " + json.dumps(data, ensure_ascii=False, indent=2) + ";
", encoding="utf-8")

def find_template(path_opt: str):
    if path_opt:
        p = pathlib.Path(path_opt)
        if not p.is_absolute():
            p = (ROOT / p).resolve()
        if not p.exists():
            die(f"Template not found: {p}")
        return p
    pref = ROOT / "books" / "song-of-songs" / "02" / "index.html"
    if pref.exists():
        return pref
    matches = list(ROOT.glob("books/*/*/index.html"))
    if not matches:
        die("No chapter index.html template found in repo.")
    return matches[0]

def write_index_js(idx: dict, dry: bool):
    if dry:
        print("DRY: write", INDEX_JS)
        return
    INDEX_JS.write_text("window.BIBLE_INDEX = " + json.dumps(idx, ensure_ascii=False, indent=2) + ";
", encoding="utf-8")

def update_index(book_slug: str, book_name: str, args, dry: bool):
    if args.no_index:
        return
    if not INDEX_JSON.exists():
        die("Missing bible_index.json")

    idx = load_json(INDEX_JSON)
    books = idx.get("books", [])
    existing = next((b for b in books if b.get("slug") == book_slug), None)
    if existing:
        if args.chapters:
            existing["chapters"] = max(int(existing.get("chapters", 0)), int(args.chapters))
        write_json(INDEX_JSON, idx, dry)
        write_index_js(idx, dry)
        return

    chapters = int(args.chapters) if args.chapters else 1
    order = int(args.order) if args.order is not None else 999
    testament = args.testament or "OT"

    books.append({"name": book_name, "slug": book_slug, "chapters": chapters, "order": order, "testament": testament})
    idx["books"] = sorted(books, key=lambda x: (x.get("order", 999), x.get("name", "")))
    write_json(INDEX_JSON, idx, dry)
    write_index_js(idx, dry)

def validate(path_json: pathlib.Path, args):
    if args.no_validate:
        return
    try:
        import jsonschema
    except Exception:
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
    ap.add_argument("--order", type=int, default=None, help="If auto-adding book, ordering number")
    ap.add_argument("--testament", default="OT", choices=["OT", "NT"], help="If auto-adding book, testament")
    ap.add_argument("--no-index", action="store_true", help="Do not update bible_index.json/js")
    ap.add_argument("--no-validate", action="store_true", help="Skip schema validation")
    ap.add_argument("--dry-run", action="store_true", help="Print actions without writing")
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

    chdir = BOOKS_DIR / book_slug / pad_num(ch)
    ensure_dir(chdir, args.dry_run)

    tpl = find_template(args.template)
    dst_index = chdir / "index.html"
    if args.dry_run:
        print("DRY: copy", tpl, "->", dst_index)
    else:
        shutil.copy2(tpl, dst_index)

    out_json = chdir / "data.json"
    out_js = chdir / "data.js"
    write_json(out_json, data, args.dry_run)
    make_data_js(data, out_js, args.dry_run)

    update_index(book_slug, book_name, args, args.dry_run)

    if not args.dry_run:

    # Backfill required semantic fields (Spec v1.3) before validation
    try:
        from backfill_semantics import patch_file as _patch_sem
        _patch_sem(out_json)
    except Exception:
        # If the helper isn't available, continue; validation may still fail if semantic fields are missing.
        pass

    # Promote token data into teaching layers (Vocabulary + Grammar) before validation
    try:
        from promote_tokens_to_lexicon import patch_file as _patch_lex
        _patch_lex(out_json, force=False)  # only if lexicon empty
    except Exception:
        pass
    try:
        from seed_basic_grammar_notes import patch_file as _patch_gram
        _patch_gram(out_json, force=False)  # only if grammar empty
    except Exception:
        pass
        validate(out_json, args)
        print("OK: installed", out_json)
    else:
        print("DRY: would validate", out_json)

if __name__ == "__main__":
    main()
