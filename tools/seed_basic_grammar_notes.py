#!/usr/bin/env python3
"""seed_basic_grammar_notes.py

Generate a lightweight, consistent starter set of grammar notes from morphology.
This is a baseline (not a full grammar engine) intended to prevent empty Grammar panels.

Heuristics:
- Verbs: list up to N notable verb tokens (surface, lemma, morph)
- Construct chains: detect tokens with state containing 'cstr' or morph containing 'cstr'
- Pronominal suffixes: detect token.features.suffix
- Cohortative/Jussive/Imperative: detect morph string containing 'imp' / 'juss' / 'coh' (best-effort)

Usage:
  python3 tools/seed_basic_grammar_notes.py books/song-of-songs/02/data.json
  python3 tools/seed_basic_grammar_notes.py --all

Notes:
- Does not overwrite existing non-empty grammar by default unless --force.
"""
import argparse, json, pathlib, glob, re

ROOT = pathlib.Path(__file__).resolve().parents[1]

def load(p: pathlib.Path):
    return json.loads(p.read_text(encoding='utf-8'))

def save(p: pathlib.Path, obj):
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding='utf-8')

def tok_has_construct(t):
    st=str((t.get('features') or {}).get('state','')).lower()
    m=str(t.get('morph','')).lower()
    return ('cstr' in st) or ('cstr' in m) or ('construct' in st)

def tok_suffix(t):
    return (t.get('features') or {}).get('suffix')

def tok_is_verb(t):
    return str(t.get('pos','')).upper()=='VERB' or str(t.get('pos','')).lower()=='verb'

def tok_mood_hint(t):
    m=str(t.get('morph','')).lower()
    for k,label in [('imp','imperative'), ('juss','jussive'), ('coh','cohortative')]:
        if k in m:
            return label
    return ''

def build_notes(data):
    verses=data.get('verses') or []
    verbs=[]
    constructs=[]
    suffixes=[]
    moods=[]
    for v in verses:
        for t in v.get('tokens',[]) or []:
            if tok_is_verb(t):
                verbs.append(t)
                mh=tok_mood_hint(t)
                if mh:
                    moods.append((mh,t))
            if tok_has_construct(t):
                constructs.append(t)
            suf=tok_suffix(t)
            if suf:
                suffixes.append((suf,t))

    notes=[]

    if verbs:
        items=[]
        for t in verbs[:8]:
            items.append(f"{t.get('surface','')} — {t.get('lemma','')} ({t.get('morph','')})")
        body='Notable verb forms (surface — lemma (morph)):\n- ' + '\n- '.join(items)
        notes.append({'id':'verbs', 'title':'Key verb forms (auto)', 'body':body})

    if constructs:
        items=[]
        for t in constructs[:8]:
            items.append(f"{t.get('surface','')} — {t.get('lemma','')} ({t.get('morph','')})")
        body='Likely construct/state-marked forms (auto):\n- ' + '\n- '.join(items)
        notes.append({'id':'construct', 'title':'Construct/state hints (auto)', 'body':body})

    if suffixes:
        items=[]
        for suf,t in suffixes[:10]:
            items.append(f"{t.get('surface','')} — suffix {suf} ({t.get('lemma','')})")
        body='Pronominal suffixes detected (auto):\n- ' + '\n- '.join(items)
        notes.append({'id':'suffixes', 'title':'Pronominal suffixes (auto)', 'body':body})

    if moods:
        # unique moods
        uniq={}
        for mh,t in moods:
            uniq.setdefault(mh, [])
            if len(uniq[mh])<6:
                uniq[mh].append(f"{t.get('surface','')} ({t.get('morph','')})")
        parts=[]
        for mh,items in uniq.items():
            parts.append(f"{mh}: " + ', '.join(items))
        body='Mood/aspect hints from morphology tags (auto):\n' + '\n'.join('- '+p for p in parts)
        notes.append({'id':'mood', 'title':'Mood/aspect hints (auto)', 'body':body})

    # always return at least empty list
    return notes

def patch_file(fp: pathlib.Path, force: bool):
    data=load(fp)
    existing=data.get('grammar')
    if existing and isinstance(existing, list) and len(existing)>0 and not force:
        return False
    data['grammar']=build_notes(data)
    save(fp, data)
    return True

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('path', nargs='?', help='Path to chapter data.json')
    ap.add_argument('--all', action='store_true')
    ap.add_argument('--force', action='store_true')
    args=ap.parse_args()

    if args.all:
        files=glob.glob(str(ROOT/'books'/'*'/'*'/'data.json'))
        n=0
        for f in sorted(files):
            if patch_file(pathlib.Path(f), args.force):
                n+=1
        print(f'OK: seeded grammar in {n} files')
        return 0

    if not args.path:
        print('Usage: seed_basic_grammar_notes.py <path/to/data.json> | --all [--force]')
        return 2
    fp=pathlib.Path(args.path).resolve()
    if not fp.exists():
        print('Not found:', fp)
        return 2
    changed=patch_file(fp, args.force)
    print('OK:', fp, '(changed)' if changed else '(skipped; grammar already present)')
    return 0

if __name__=='__main__':
    raise SystemExit(main())
