# Hebrew Bible Learning Site (Static, Morph-ready)

This is a static multi-page site for Biblical Hebrew with:
- Original Hebrew
- Translation + transliteration
- Token-level morphology (Spec v1.2, ETCBC-like)
- Interlinear view + token info
- Browser TTS with speed slider

## Quick start
Open `index.html` directly (file://) or host the folder on any static web server.

## Add a new book (recommended workflow)
1) Scaffold folders + templates:
   - `python3 tools/scaffold_book.py <book_slug> "<Book Name>" <chapters>`
2) Register the book in the global index:
   - `python3 tools/update_index.py <book_slug> "<Book Name>" <chapters> --order 10 --testament OT`

## Add a new chapter
1) Put `data.json` into:
   - `books/<book_slug>/<NN>/data.json`
2) Generate `data.js` (file-friendly):
   - `python3 tools/make_data_js.py books/<book_slug>/<NN>/data.json`

## Authoring new chapters with ChatGPT
Use `PROJECT_PROMPT.md` as the copy/paste prompt for a new chat. It enforces:
- Spec v1.2 JSON
- token IDs
- ETCBC-like feature keys
- gloss + lemma normalization


## Validation
This repo includes a JSON Schema for chapter files: `schema/chapter.schema.json`.

Validate (requires `jsonschema`):

```bash
pip install jsonschema
python3 tools/validate_chapter.py --all
```


---

## 🔎 JSON Validation (Spec v1.3)

This project uses a formal JSON Schema to ensure every chapter file follows **Spec v1.3**.

Schema location:

    schema/chapter.schema.json

### Install validator dependency

    pip install jsonschema

### Validate a single chapter

    python3 tools/validate_chapter.py books/song-of-songs/02/data.json

### Validate all chapters in the repository

    python3 tools/validate_chapter.py --all

If validation fails, the script prints the file and the schema error.

---

### Why Validation Matters

- Prevents structural drift between chapters
- Enforces token ID format
- Ensures morphology fields exist
- Guarantees semantic tagging structure
- Protects renderer automation (title, breadcrumbs, SEO)

Always validate before committing new chapters.


---

## 🧰 Tools (Scripts)

All automation helpers live in `tools/`. They keep manual work minimal and enforce Spec consistency.

### ⭐ Recommended: `tools/add_chapter_bundle.py`
**One-command chapter installer.** Use this whenever you have a new chapter `data.json` (from ChatGPT or any pipeline) and want it fully integrated.

It will:
- normalize the JSON to Spec v1.3 (best-effort)
- create `books/<book_slug>/<NN or NNN>/`
- copy a chapter `index.html` renderer template into the folder
- write `data.json`
- generate `data.js`
- update `bible_index.json` / `bible_index.js` (optional)
- validate against `schema/chapter.schema.json`

Example:
```bash
pip install jsonschema
python3 tools/add_chapter_bundle.py --in /path/to/data.json
```

Override book/chapter if needed:
```bash
python3 tools/add_chapter_bundle.py --book psalms --chapter 140 --in /path/to/data.json
```

### `tools/validate_chapter.py`
Validate chapter JSON against the schema.

- Validate one:
```bash
python3 tools/validate_chapter.py books/song-of-songs/02/data.json
```
- Validate all:
```bash
python3 tools/validate_chapter.py --all
```

### `tools/make_data_js.py`
Generate `data.js` from `data.json` (file:// friendly wrapper).
```bash
python3 tools/make_data_js.py books/song-of-songs/02/data.json
```

### `tools/update_index.py`
Add/update a book entry in `bible_index.json` and regenerate `bible_index.js`.
```bash
python3 tools/update_index.py psalms "Psalms" 150 --order 19 --testament OT
```

### `tools/scaffold_book.py`
Create a book TOC page (`books/<slug>/index.html`) and (optionally) chapter folders.
```bash
python3 tools/scaffold_book.py psalms "Psalms" 150
```

### `tools/add_chapter_from_text.py`
Create a minimal chapter scaffold from a plain text verse list (Hebrew only). Produces starter `data.json` + `data.js`.
```bash
python3 tools/add_chapter_from_text.py input.txt
```

### `tools/normalize_legacy_chapter.py`
Convert legacy/ad-hoc chapter JSON into Spec-compatible structure (best-effort). Useful when importing external formats.
```bash
python3 tools/normalize_legacy_chapter.py legacy.json --out books/psalms/139/data.json
```

---


### `tools/backfill_semantics.py`
Backfill required semantic fields for Spec v1.3 so older chapters pass validation (adds `semantic_summary: []` to verses and `semantic: []` to tokens when missing).
```bash
python3 tools/backfill_semantics.py books/song-of-songs/01/data.json
python3 tools/backfill_semantics.py --all
```

### `tools/backfill_required_fields.py`
Upgrade older chapter JSONs to meet Spec v1.3 top-level required fields (spec_version, tagset, ref_system, generated_at, etc.).
```bash
python3 tools/backfill_required_fields.py --all
```

### `tools/promote_tokens_to_lexicon.py`
Auto-build `lexicon[]` from tokens so Vocabulary panel is populated.
```bash
python3 tools/promote_tokens_to_lexicon.py --all
```

### `tools/seed_basic_grammar_notes.py`
Generate baseline `grammar[]` notes from morphology so Grammar panel is not empty.
```bash
python3 tools/seed_basic_grammar_notes.py --all
```


### `tools/vocab_coverage.py`
Report vocabulary (lexicon) gloss coverage per chapter (and optionally token gloss coverage).
```bash
python3 tools/vocab_coverage.py --all
python3 tools/vocab_coverage.py --all --tokens
python3 tools/vocab_coverage.py --all --min 95
```
