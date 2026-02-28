#!/usr/bin/env python3
"""normalize_grammar_items.py

Normalize grammar note objects to a consistent shape used by the UI:
{id, title, body}

Converts common legacy shapes such as:
{topic, example, note} -> {id: slug(topic), title: topic, body: note + example}

Usage:
  python3 tools/normalize_grammar_items.py books/psalms/139/data.json
  python3 tools/normalize_grammar_items.py --all
"""
import argparse, json, pathlib, glob, re

ROOT = pathlib.Path(__file__).resolve().parents[1]

def load(p): return json.loads(pathlib.Path(p).read_text(encoding='utf-8'))
def save(p,obj): pathlib.Path(p).write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding='utf-8')

def slug(s):
    s=(s or '').strip().lower()
    s=re.sub(r'[^a-z0-9]+','-', s)
    return s.strip('-') or 'note'

def normalize_item(it, i):
    if not isinstance(it, dict):
        return {"id": f"note-{i:02d}", "title":"Note", "body": str(it)}
    if "title" in it and "body" in it and "id" in it:
        return it
    if "topic" in it:
        title=it.get("topic") or "Grammar note"
        example=it.get("example")
        note=it.get("note") or ""
        body=note
        if example:
            body=(body + "\n\nExample: " + example).strip()
        return {"id": slug(title), "title": title, "body": body}
    # fallback
    title=it.get("title") or it.get("id") or f"Note {i}"
    body=it.get("body") or it.get("note") or ""
    return {"id": it.get("id") or slug(title), "title": title, "body": body}

def patch_file(fp):
    data=load(fp)
    g=data.get("grammar") or []
    new=[normalize_item(it, i+1) for i,it in enumerate(g)]
    data["grammar"]=new
    save(fp, data)
    return True

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('path', nargs='?')
    ap.add_argument('--all', action='store_true')
    args=ap.parse_args()
    if args.all:
        files=glob.glob(str(ROOT/'books'/'*'/'*'/'data.json'))
        for f in sorted(files):
            patch_file(f)
        print('OK: normalized grammar items in all chapters')
        return 0
    if not args.path:
        print('Usage: normalize_grammar_items.py <path/to/data.json> | --all')
        return 2
    fp=pathlib.Path(args.path).resolve()
    if not fp.exists():
        print('Not found:', fp); return 2
    patch_file(str(fp))
    print('OK:', fp)
    return 0

if __name__=='__main__':
    raise SystemExit(main())
