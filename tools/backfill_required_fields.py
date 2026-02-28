#!/usr/bin/env python3
"""
backfill_required_fields.py

Ensures all chapter `data.json` files meet Spec v1.3 *top-level* required fields.
This is meant to upgrade older chapter files generated before Spec v1.3 was locked.

It will add (if missing):
- spec_version: "1.3"
- tagset: {name:"ETCBC-like", version:"1.0"}
- ref_system: "MT"
- generated_at: YYYY-MM-DD (today)
- book, book_slug, chapter: inferred from folder path books/<slug>/<NNN>/
- lexicon, grammar, exercises, annotations: []

It does NOT change verse text or token morphology (beyond adding defaults).

Usage:
  python3 tools/backfill_required_fields.py books/song-of-songs/03/data.json
  python3 tools/backfill_required_fields.py --all
"""
import json, pathlib, sys, glob, re, datetime

ROOT = pathlib.Path(__file__).resolve().parents[1]

def load(p: pathlib.Path):
    return json.loads(p.read_text(encoding="utf-8"))

def save(p: pathlib.Path, obj):
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")

def infer_from_path(fp: pathlib.Path):
    # expect .../books/<slug>/<chapter>/data.json
    parts = fp.parts
    try:
        i = parts.index("books")
        slug = parts[i+1]
        ch = parts[i+2]
        ch_num = int(ch)
        return slug, ch_num
    except Exception:
        return None, None

def title_case_slug(slug: str) -> str:
    # Special-case a few
    if slug == "song-of-songs": return "Song of Songs"
    return " ".join([w.capitalize() for w in slug.split("-")])

def patch(fp: pathlib.Path) -> bool:
    data = load(fp)
    changed = False

    slug, ch_num = infer_from_path(fp)
    if data.get("spec_version") is None:
        data["spec_version"] = "1.3"
        changed = True
    if data.get("tagset") is None:
        data["tagset"] = {"name":"ETCBC-like","version":"1.0"}
        changed = True
    if data.get("ref_system") is None:
        data["ref_system"] = "MT"
        changed = True
    if data.get("generated_at") is None:
        data["generated_at"] = str(datetime.date.today())
        changed = True

    if slug and data.get("book_slug") is None:
        data["book_slug"] = slug
        changed = True
    if ch_num and data.get("chapter") is None:
        data["chapter"] = int(ch_num)
        changed = True
    if data.get("book") is None:
        # if legacy book is object
        if isinstance(data.get("book"), dict) and data["book"].get("name"):
            data["book"] = data["book"]["name"]
            changed = True
        elif slug:
            data["book"] = title_case_slug(slug)
            changed = True

    for k in ["lexicon","grammar","exercises","annotations"]:
        if data.get(k) is None:
            data[k] = []
            changed = True

    # Ensure verses exist
    if data.get("verses") is None:
        data["verses"] = []
        changed = True

    if changed:
        save(fp, data)
    return changed

def main(argv):
    if len(argv) >= 2 and argv[1] == "--all":
        files = glob.glob(str(ROOT / "books" / "*" / "*" / "data.json"))
        n = 0
        for f in sorted(files):
            if patch(pathlib.Path(f)):
                n += 1
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
