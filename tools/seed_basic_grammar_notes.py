#!/usr/bin/env python3
"""seed_basic_grammar_notes.py

Generate a lightweight starter set of grammar notes from morphology.
Prevents empty Grammar panels.

Usage:
  python3 tools/seed_basic_grammar_notes.py books/song-of-songs/02/data.json
  python3 tools/seed_basic_grammar_notes.py --all
"""
import argparse, pathlib
from utils import load_json, save_json, all_chapter_jsons

def tok_has_construct(t):
    st = str((t.get("features") or {}).get("state", "")).lower()
    m = str(t.get("morph", "")).lower()
    return "cstr" in st or "cstr" in m or "construct" in st

def tok_suffix(t):
    return (t.get("features") or {}).get("suffix")

def tok_is_verb(t):
    return str(t.get("pos", "")).upper() == "VERB"

def tok_mood_hint(t):
    m = str(t.get("morph", "")).lower()
    for k, label in [("imp", "imperative"), ("juss", "jussive"), ("coh", "cohortative")]:
        if k in m:
            return label
    return ""

def build_notes(data):
    verbs, constructs, suffixes, moods = [], [], [], []
    for v in (data.get("verses") or []):
        for t in (v.get("tokens") or []):
            if tok_is_verb(t):
                verbs.append(t)
                mh = tok_mood_hint(t)
                if mh:
                    moods.append((mh, t))
            if tok_has_construct(t):
                constructs.append(t)
            suf = tok_suffix(t)
            if suf:
                suffixes.append((suf, t))

    notes = []
    if verbs:
        items = [f"{t.get('surface','')} \u2014 {t.get('lemma','')} ({t.get('morph','')})" for t in verbs[:8]]
        notes.append({"id": "verbs", "title": "Key verb forms (auto)", "body": "Notable verb forms (surface \u2014 lemma (morph)):\n- " + "\n- ".join(items)})
    if constructs:
        items = [f"{t.get('surface','')} \u2014 {t.get('lemma','')} ({t.get('morph','')})" for t in constructs[:8]]
        notes.append({"id": "construct", "title": "Construct/state hints (auto)", "body": "Likely construct/state-marked forms (auto):\n- " + "\n- ".join(items)})
    if suffixes:
        items = [f"{t.get('surface','')} \u2014 suffix {suf} ({t.get('lemma','')})" for suf, t in suffixes[:10]]
        notes.append({"id": "suffixes", "title": "Pronominal suffixes (auto)", "body": "Pronominal suffixes detected (auto):\n- " + "\n- ".join(items)})
    if moods:
        uniq = {}
        for mh, t in moods:
            uniq.setdefault(mh, [])
            if len(uniq[mh]) < 6:
                uniq[mh].append(f"{t.get('surface','')} ({t.get('morph','')})")
        parts = [f"{mh}: " + ", ".join(items) for mh, items in uniq.items()]
        notes.append({"id": "mood", "title": "Mood/aspect hints (auto)", "body": "Mood/aspect hints from morphology tags (auto):\n" + "\n".join("- " + p for p in parts)})
    return notes

def patch_file(fp, force=False):
    data = load_json(fp)
    existing = data.get("grammar")
    if existing and isinstance(existing, list) and len(existing) > 0 and not force:
        return False
    data["grammar"] = build_notes(data)
    save_json(fp, data)
    return True

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("path", nargs="?")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    if args.all:
        n = sum(1 for f in all_chapter_jsons() if patch_file(f, args.force))
        print(f"OK: seeded grammar in {n} files")
        return 0
    if not args.path:
        print("Usage: seed_basic_grammar_notes.py <path/to/data.json> | --all [--force]")
        return 2
    fp = pathlib.Path(args.path).resolve()
    if not fp.exists():
        print("Not found:", fp)
        return 2
    changed = patch_file(fp, args.force)
    print("OK:", fp, "(changed)" if changed else "(skipped; grammar already present)")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
