#!/usr/bin/env python3
"""promote_tokens_to_lexicon.py

Build or enrich top-level `lexicon[]` entries from token data so the Vocabulary panel
is populated for every chapter.

Modes:
- default: if lexicon is empty/missing, build it from tokens
- --fill-missing: if lexicon exists, fill missing gloss/root/pos/notes from tokens + gloss_map
- --force: rebuild lexicon from tokens (do NOT use on chapters with curated lexicon unless desired)

Usage:
  python3 tools/promote_tokens_to_lexicon.py books/song-of-songs/02/data.json
  python3 tools/promote_tokens_to_lexicon.py --all
  python3 tools/promote_tokens_to_lexicon.py --all --fill-missing
"""
import argparse, json, pathlib, glob, collections, re

ROOT = pathlib.Path(__file__).resolve().parents[1]
GLOSS_MAP_PATH = pathlib.Path(__file__).resolve().parent / "gloss_map.json"

def load(p: pathlib.Path):
    return json.loads(p.read_text(encoding='utf-8'))

def save(p: pathlib.Path, obj):
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding='utf-8')

def norm_pos(pos):
    if not pos: return ''
    return str(pos).lower()

def strip_niqqud(s: str) -> str:
    if not s: return ''
    # Hebrew niqqud + cantillation ranges
    return re.sub(r"[\u0591-\u05BD\u05BF-\u05C7]", "", s)


import unicodedata

def normalize_hebrew(s: str) -> str:
    s = (s or "").strip()
    s = unicodedata.normalize("NFC", s)
    # drop cantillation marks
    s = "".join(ch for ch in s if not (0x0591 <= ord(ch) <= 0x05AF))
    # strip leading punctuation and combining marks
    while s and (s[0] in "־–—" or s[0].isspace()):
        s = s[1:]
    while s and unicodedata.category(s[0]) == "Mn":
        s = s[1:]
    return s

def load_gloss_map():
    if GLOSS_MAP_PATH.exists():
        try:
            return load(GLOSS_MAP_PATH)
        except Exception:
            return {}
    return {}

def derive_notes(samples):
    morphs=[(t.get('morph') or '') for t in samples if (t.get('morph') or '').strip()]
    morphs=[m for m in morphs if m]
    if not morphs: return ''
    c=collections.Counter(morphs)
    common=[m for m,_ in c.most_common(2)]
    return 'Common forms: ' + '; '.join(common) if common else ''

def collect_token_index(data):
    idx=collections.defaultdict(list)
    for v in data.get('verses', []) or []:
        for t in v.get('tokens', []) or []:
            lemma=(t.get('lemma') or '').strip()
            if lemma:
                idx[lemma].append(t)
    return idx

def build_lexicon_from_tokens(data, gloss_map):
    idx=collect_token_index(data)
    order=[]
    seen=set()
    for v in data.get('verses', []) or []:
        for t in v.get('tokens', []) or []:
            lemma=(t.get('lemma') or '').strip()
            if lemma and lemma not in seen:
                seen.add(lemma); order.append(lemma)
    entries=[]
    for lemma in order:
        samp=idx[lemma]
        t0=samp[0]
        gloss=(t0.get('gloss') or '').strip()
        if not gloss:
            gloss=(gloss_map.get(strip_niqqud(lemma), '') or gloss_map.get(lemma, '') or gloss_map.get(normalize_hebrew(lemma), '')).strip()
        entries.append({
            "lemma": lemma,
            "root": (t0.get("root") or "—"),
            "pos": norm_pos(t0.get("pos")),
            "gloss": gloss,
            "notes": derive_notes(samp)
        })
    return entries

def fill_missing_fields(existing, token_idx, gloss_map):
    # existing: list of lexicon entries
    by_lemma={e.get('lemma'): e for e in existing if isinstance(e, dict) and e.get('lemma')}
    for lemma,e in by_lemma.items():
        samp=token_idx.get(lemma) or []
        t0=samp[0] if samp else {}
        if not e.get('root'):
            e['root']=t0.get('root') or '—'
        if not e.get('pos'):
            e['pos']=norm_pos(t0.get('pos'))
        if not e.get('gloss'):
            e['gloss']=(t0.get('gloss') or '').strip()
            if not e['gloss']:
                e['gloss']=gloss_map.get(strip_niqqud(lemma), '')
        if 'notes' not in e or e.get('notes') is None or e.get('notes')=='':
            e['notes']=derive_notes(samp)
    # Ensure all entries have notes key
    for e in existing:
        if isinstance(e, dict) and 'notes' not in e:
            e['notes']=''
    return existing

def patch_file(fp: pathlib.Path, force: bool, fill_missing: bool):
    data=load(fp)
    gloss_map=load_gloss_map()
    token_idx=collect_token_index(data)

    existing=data.get('lexicon')
    if force or not existing or (isinstance(existing, list) and len(existing)==0):
        data['lexicon']=build_lexicon_from_tokens(data, gloss_map)
        save(fp, data)
        return True

    if fill_missing and isinstance(existing, list):
        data['lexicon']=fill_missing_fields(existing, token_idx, gloss_map)
        save(fp, data)
        return True

    return False

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('path', nargs='?', help='Path to chapter data.json')
    ap.add_argument('--all', action='store_true', help='Process all chapters')
    ap.add_argument('--force', action='store_true', help='Rebuild lexicon from tokens')
    ap.add_argument('--fill-missing', action='store_true', help='Fill missing gloss/root/pos/notes in existing lexicon')
    args=ap.parse_args()

    if args.all:
        files=glob.glob(str(ROOT/'books'/'*'/'*'/'data.json'))
        n=0
        for f in sorted(files):
            if patch_file(pathlib.Path(f), args.force, args.fill_missing):
                n+=1
        print(f'OK: updated lexicon in {n} files')
        return 0

    if not args.path:
        print('Usage: promote_tokens_to_lexicon.py <path/to/data.json> | --all [--fill-missing] [--force]')
        return 2
    fp=pathlib.Path(args.path).resolve()
    if not fp.exists():
        print('Not found:', fp)
        return 2
    changed=patch_file(fp, args.force, args.fill_missing)
    print('OK:', fp, '(changed)' if changed else '(no changes)')
    return 0

if __name__=='__main__':
    raise SystemExit(main())
