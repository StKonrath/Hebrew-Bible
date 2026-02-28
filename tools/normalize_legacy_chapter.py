#!/usr/bin/env python3
"""normalize_legacy_chapter.py

Convert older/ad-hoc chapter JSON variants into the current Spec v1.2 shape.

Why:
- Some experiments used: {book:{name,slug}, chapter:<n>, verses:[{n:<v>, he,en,tr,...}]}
- The site renderer now tolerates these, but the JSON schema validator expects Spec v1.2.

This tool rewrites a chapter JSON in-place (or to --out) to be schema-valid.

Usage:
  python3 tools/normalize_legacy_chapter.py books/psalms/139/data.json
  python3 tools/normalize_legacy_chapter.py books/psalms/139/data.json --out books/psalms/139/data.v1_2.json
"""

import argparse, json, pathlib, datetime


def slugify(s: str) -> str:
    import re
    s = (s or "").lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return re.sub(r"^-+|-+$", "", s)


def normalize(obj: dict) -> dict:
    out = dict(obj)

    # spec_version
    if "spec_version" not in out:
        if isinstance(out.get("spec"), str):
            out["spec_version"] = out["spec"]
        elif isinstance(out.get("spec"), dict) and out["spec"].get("version"):
            out["spec_version"] = str(out["spec"]["version"])
        else:
            out["spec_version"] = "1.2"

    # book fields
    book = out.get("book")
    if isinstance(book, dict):
        name = book.get("name") or out.get("book_name")
        slug = book.get("slug") or out.get("book_slug")
    else:
        name = out.get("book") or out.get("book_name")
        slug = out.get("book_slug")

    name = name or "Book"
    slug = slug or slugify(name)

    out["book"] = name
    out["book_slug"] = slug

    # title
    ch = out.get("chapter")
    if not out.get("title"):
        out["title"] = f"{name} - Chapter {ch}" if ch is not None else name

    # verses
    verses = out.get("verses") or []
    norm_verses = []
    for i, v in enumerate(verses, start=1):
        if not isinstance(v, dict):
            continue
        vn = v.get("n", i)
        ref = v.get("ref") or f"{ch}:{vn}" if ch is not None else str(vn)
        norm_verses.append({
            "ref": ref,
            "he": v.get("he", ""),
            "en": v.get("en", ""),
            "tr": v.get("tr", ""),
            "tokens": v.get("tokens", []),
            # keep semantic fields if present
            **({"semantic": v.get("semantic")} if "semantic" in v else {}),
            **({"semantic_summary": v.get("semantic_summary")} if "semantic_summary" in v else {}),
        })
    out["verses"] = norm_verses

    # optional containers
    out.setdefault("lexicon", [])
    out.setdefault("grammar", [])
    out.setdefault("exercises", [])
    out.setdefault("annotations", [])

    out.setdefault("generated_at", str(datetime.date.today()))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("path")
    ap.add_argument("--out", default="")
    args = ap.parse_args()

    p = pathlib.Path(args.path)
    obj = json.loads(p.read_text(encoding="utf-8"))
    out = normalize(obj)
    dest = pathlib.Path(args.out) if args.out else p
    dest.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print("Wrote", dest)


if __name__ == "__main__":
    main()
