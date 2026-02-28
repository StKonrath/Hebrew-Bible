# Copy/paste prompt for new chats (Hebrew Bible Site)

Use this in a new chat to generate a new chapter `data.json` in the project standard.

---

**System / Project context**

You are working inside the *Hebrew Bible Learning Site* project.

**Hard requirements**
- Output **Spec v1.2** JSON only (no prose in between).
- Tagset: **ETCBC-like v1.0** (`features` is authoritative; `morph` is derived display).
- For every verse: include `he`, `en`, `tr`, and `tokens[]`.
- Every token must include: `id`, `surface`, `lemma`, `root`, `pos`, `features`, `morph`, `gloss`.
- Use token IDs: `<book_slug>.<chapter(2d)>.<verse(2d)>.t###` (e.g. `genesis.01.01.t001`).
- Where a root is not applicable (particles, determiners, conjunctions, prepositions): set `root` to `—`.
- Keep Hebrew pointed; preserve maqaf-splitting in tokenization.
- Provide a concise but useful `lexicon[]` (chapter-specific).
- Provide 3–8 `grammar[]` notes (only forms appearing).
- Provide 3–6 `exercises[]` with answers.
- Keep `annotations[]` empty unless I ask for admin notes.

**Input I will provide**
- Book name, book_slug, chapter number
- Hebrew text (pointed) verse by verse (or continuous; you may split)
- Optional English translation preferences

**Your output must be**
1) `data.json` (Spec v1.2)
2) A `data.js` wrapper line:
   `window.__chapterData = <the same JSON>;`

Now generate: [PASTE BOOK/CHAPTER AND HEBREW TEXT HERE]


## Semantic tagging layer
- Add token-level `semantic: []` tags (controlled vocabulary) and verse-level `semantic_summary`.
- Controlled tags (starter): FLORA, FAUNA, LOVE, MOTION, SPEECH, OATH, TIME, PLACE, WEATHER, FOOD, BODY, PERCEPTION, PRAISE, DAMAGE, AGRICULTURE, MUSIC, SYMBOL.

## Output packaging
- Provide a ZIP containing `books/<book_slug>/<NN>/data.json` and `data.js`.
- If adding a new book, also include updated `bible_index.json` and `bible_index.js`.
