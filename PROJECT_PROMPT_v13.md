# Copy/paste prompt for new chats (Hebrew Bible Site)

Use this in a new chat to generate a new chapter `data.json` in the
project standard.

------------------------------------------------------------------------

## System / Project context

You are working inside the *Hebrew Bible Learning Site* project.

------------------------------------------------------------------------

# Hard requirements (Spec v1.3)

-   Output **Spec v1.3 JSON only** (no prose in between).
-   Top-level must include:
    -   `spec_version: "1.3"`
    -   `tagset: { "name": "ETCBC-like", "version": "1.0" }`
    -   `ref_system: "MT"`
    -   `generated_at` (ISO date string, e.g. `"2026-03-01"`)
    -   `book`
    -   `book_slug`
    -   `chapter`
    -   `title`
    -   `verses[]`
    -   `lexicon[]`
    -   `grammar[]`
    -   `exercises[]`
    -   `annotations[]` (empty unless requested)

------------------------------------------------------------------------

# Verse structure (Spec v1.3)

Each verse must contain:

{ "ref": "1:1", "he": "...", "en": "...", "tr": "...", "tokens": \[\],
"semantic_summary": \[\] }

### Notes

-   `ref` must be string format `"chapter:verse"` (e.g. `"1:1"`).
-   Do NOT use `"verse": 1` (that was Spec v1.2).
-   Preserve Hebrew pointing.
-   Preserve maqaf splitting in tokenization.

------------------------------------------------------------------------

# Token structure (ETCBC-like v1.0)

Every token must include:

{ "id": "psalms.01.01.t001", "surface": "אַשְׁרֵי", "lemma": "אַשְׁרֵי",
"root": "אשר", "pos": "interj", "features": {}, "morph": "INTJ",
"gloss": "blessed", "semantic": \[\] }

### Requirements

-   `id` format: `<book_slug>.<chapter(2d)>.<verse(2d)>.t###`
-   `features` is authoritative (ETCBC-style categories).
-   `morph` is derived display string.
-   If a root does not apply (particles, conjunctions, prepositions),
    set: `"root": "—"`

------------------------------------------------------------------------

# Lexicon

Provide a concise but useful `lexicon[]`, chapter-specific only.

Each entry must include:

{ "lemma": "...", "root": "...", "pos": "...", "gloss": "..." }

------------------------------------------------------------------------

# Grammar Notes

Provide **3--8 grammar\[\] notes**, only for forms appearing in the
chapter.

Each note:

{ "topic": "...", "example": "...", "note": "..." }

------------------------------------------------------------------------

# Exercises

Provide **3--6 exercises\[\]** with answers.

Each exercise:

{ "q": "...", "a": "..." }

------------------------------------------------------------------------

# Semantic tagging layer

-   Add token-level `semantic: []` tags.
-   Add verse-level `semantic_summary`.

Controlled tags:

FLORA, FAUNA, LOVE, MOTION, SPEECH, OATH, TIME, PLACE, WEATHER, FOOD,
BODY, PERCEPTION, PRAISE, DAMAGE, AGRICULTURE, MUSIC, SYMBOL

Only use tags that actually apply.

------------------------------------------------------------------------

# Output format

Your output must contain exactly:

1)  `data.json` (Spec v1.3 JSON only)
2)  A `data.js` wrapper line:

window.\_\_chapterData = `<the same JSON>`{=html};

No explanatory prose between them.

------------------------------------------------------------------------

# Output packaging

-   Provide a ZIP containing:
    books/`<book_slug>`{=html}/`<NN>`{=html}/data.json
    books/`<book_slug>`{=html}/`<NN>`{=html}/data.js
-   If adding a new book, also include updated:
    -   `bible_index.json`
    -   `bible_index.js`

------------------------------------------------------------------------

Now generate:

\[PASTE BOOK/CHAPTER AND HEBREW TEXT HERE\]
