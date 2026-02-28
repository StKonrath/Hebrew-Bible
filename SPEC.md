# Data Spec — Hebrew Bible Learning Site

This repository renders Hebrew Bible texts from chapter-level JSON files.

**Principle:** JSON = data only. Renderer = presentation only.  
Titles, breadcrumbs, SEO `<title>`, and verse range display are derived by the renderer.

---

## Spec Versioning

Every chapter `data.json` includes:

```json
{
  "spec_version": "1.3"
}
```

- **Minor** increments (e.g. 1.3 → 1.4) may add optional fields and MUST remain backward compatible.
- **Major** increments (e.g. 1.x → 2.0) may introduce breaking changes.

Keep versioning **inside the JSON** so filenames never need renaming.

---

## Canonical Chapter File Layout

Each chapter folder contains:

```
books/<book_slug>/<NN>/
  data.json
  data.js          (file:// friendly wrapper)
  index.html       (renderer; identical across chapters in current architecture)
```

`data.js` must define:

```js
window.__chapterData = <same JSON as data.json>;
```

---

## Renderer-driven Title & Navigation (Automation)

The renderer derives the canonical chapter title as:

```
<book> - Chapter <chapter>
```

Optional subtitle can be provided via:

- `subtitle` (preferred)
- or `book_subtitle`, `book_hebrew`, `book_he` (accepted aliases)

Verse range is computed from `verses[].ref` and shown automatically.

Breadcrumbs and SEO `<title>` are computed automatically:
- Document title: `<book> - Chapter <n> | Hebrew Bible`
- Breadcrumbs: `Home › <book> › Chapter <n>`

**Do not embed formatting logic in JSON** (e.g., do not put verse ranges into titles).

---

## Spec v1.3 — Chapter JSON Schema (Human Readable)

Top-level fields:

- `spec_version` (string, required) — currently `"1.3"`
- `tagset` (object, required) — e.g. `{ "name": "ETCBC-like", "version": "1.0" }`
- `book` (string, required) — display name (English)
- `book_slug` (string, required) — URL/FS slug (kebab-case)
- `chapter` (integer, required)
- `ref_system` (string, required) — `"MT"`
- `subtitle` (string, optional) — e.g. Hebrew book name
- `verses` (array, required)
- `lexicon` (array, required)
- `grammar` (array, required)
- `exercises` (array, required)
- `annotations` (array, required)
- `generated_at` (string, required) — ISO date recommended

### Verse object
Each item of `verses[]`:

- `ref` (string, required) — `"2:17"`
- `he` (string, required) — pointed Hebrew
- `en` (string, required) — English translation
- `tr` (string, required) — transliteration
- `tokens` (array, required)
- `semantic_summary` (array of strings, required)

### Token object
Each item of `tokens[]`:

- `id` (string, required) — `<book_slug>.<CC>.<VV>.t###` (CC and VV are zero-padded to **2 digits**, but **3 digits** when >=100)
- `surface` (string, required) — pointed token
- `lemma` (string, required)
- `root` (string, required) — `"—"` if not applicable
- `pos` (string, required) — e.g. `NOUN`, `VERB`, `PREP`, `PARTICLE`, ...
- `features` (object, required) — tagset-aligned morphology features
- `morph` (string, required) — derived display string
- `gloss` (string, required)
- `semantic` (array of strings, required)

---

## Controlled Semantic Tags (starter set)

FLORA, FAUNA, LOVE, MOTION, SPEECH, OATH, TIME, PLACE, WEATHER, FOOD, BODY, PERCEPTION,
PRAISE, DAMAGE, AGRICULTURE, MUSIC, SYMBOL

You may extend the vocabulary, but do not change meanings of existing tags.

---

## Deprecations

- `title` is **deprecated** (renderer generates canonical titles).
- If `title` exists in older chapters, the renderer SHOULD ignore it.

---

## Validation

This repo includes a JSON Schema validator:

- `schema/chapter.schema.json`

Use it to validate every `data.json` before publishing.

