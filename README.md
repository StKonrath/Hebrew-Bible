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
