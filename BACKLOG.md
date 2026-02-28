# BACKLOG (Hebrew Bible Learning Site)

This is a living backlog of product + engineering improvements for the long-term “computational Hebrew engine” vision.

## P0 — Fixes / correctness
- [x] **Header navigation 404**: fix book+chapter dropdown generating `.../books/books/...` on GitHub Pages (root cause: wrong relative path when current URL ends in `index.html`).
- [ ] Add a lightweight **schema validator** (Spec v1.2) to catch missing fields (`lemma/root/gloss/features/morph/semantic`) before publishing.
- [ ] Normalize tokenization rules: maqaf splitting, punctuation stripping, consistent handling of sof pasuq and paseq.
- [ ] Make TTS robust: fallback voice selection, error states, iOS/Safari quirks, verse-level rate/pitch persistence.

## P1 — Corpus scalability
- [ ] **Universal chapter renderer**: replace per-chapter `index.html` duplication with one `chapter.html?book=<slug>&ch=<NN>` router (optional, but reduces maintenance).
- [ ] **Auto-index update**: one command to add book+chapters (scaffold folders + update `bible_index.json` + regenerate `bible_index.js`).
- [ ] Bulk ingestion “one-shot” pipeline: `add_chapter_from_text.py` + `enrich_chapter.py` + `validate.py` + `pack_zip.py`.
- [ ] Add a `manifest.json` per book to declare chapter count, order, optional metadata (themes, authorship, dating, genre).

## P2 — Linguistics quality
- [ ] Lock a full **feature schema** (ETCBC-like v1.0 already started) with enumerated values and documented constraints.
- [ ] Improve morphology engine:
  - disambiguate common homographs via context (e.g., participle vs noun)
  - consistently encode pronominal suffixes and preposition+suffix compounds
  - add “state” and “gender” with higher accuracy
- [ ] Add lemma normalization rules: strip clitics; unify pointing variants; handle defective/plene spellings.
- [ ] Expand gloss dictionary + lexicon generator:
  - closed-class inventory (prep/particles)
  - frequent content lemmas for each book
  - consistent gloss style guide
- [ ] Optional import/mapping from external datasets (ETCBC, Westminster) into Spec v1.2 `features`.

## P3 — UX / Learning features
- [ ] Toggle to highlight **semantic tags** (LOVE/FLORA/FAUNA/etc.) inline.
- [ ] Morph filters: “show only verbs”, “show only construct nouns”, “show only imperatives”.
- [ ] Vocabulary trainer mode: spaced repetition export (Anki) per chapter/book.
- [ ] Interlinear improvements: align token-to-gloss spacing; show prefixes/suffixes as mini-tokens.
- [ ] Search:
  - Hebrew search (exact/normalized)
  - lemma search (across chapters)
  - semantic tag search

## P4 — Commentary / admin workflow
- [ ] Admin annotations UI:
  - add/edit verse notes (theological context, literary notes)
  - add token notes (disambiguation, etymology)
  - store notes in `annotations[]` with author + timestamp
- [ ] Review mode: “diff” between morphology versions for a chapter (v1.2 vs v1.3).
- [ ] Publishing pipeline: draft vs published chapters; build step to create a static release.

## P5 — Quality + collaboration
- [ ] Contributor guidelines: tagset rules, gloss style, transliteration system.
- [ ] Automated tests on GitHub Actions: schema validation + link checker.
- [ ] Generate docs site: spec docs, tagset docs, onboarding.

---
## Notes on the navigation bug (root cause)
When a chapter is opened as `.../books/<slug>/<NN>/index.html` (GitHub Pages), the old nav code computed the base path by counting path segments, but treated `index.html` as a directory level. It then navigated to `../..../books/<slug>/<NN>/`, producing `.../books/books/...`.

**Fix**: derive the site base from the substring before `/books/` and always build URLs as:
`<base>/books/<slug>/<NN>/`.
