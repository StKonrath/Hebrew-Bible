#!/usr/bin/env python3
"""
scaffold_book.py
Create a new book folder with a TOC page and chapter folders.

Usage:
  python3 tools/scaffold_book.py <book_slug> "<Book Name>" <chapters>
Example:
  python3 tools/scaffold_book.py genesis "Genesis" 50
"""
import argparse, pathlib, shutil, json

ap = argparse.ArgumentParser()
ap.add_argument("slug")
ap.add_argument("name")
ap.add_argument("chapters", type=int)
args = ap.parse_args()

root = pathlib.Path(__file__).resolve().parents[1]
books_dir = root / "books"
book_dir = books_dir / args.slug
book_dir.mkdir(parents=True, exist_ok=True)

# copy an existing book index template if present, else create minimal
toc_path = book_dir / "index.html"
if not toc_path.exists():
    toc_html = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <title>{args.name} — Contents</title>
  <link rel="stylesheet" href="../../assets/styles.css" />
</head>
<body>
  <header class="topbar">
    <div class="brand"><a href="../../index.html">Hebrew Bible</a></div>
    <div class="muted">{args.name}</div>
  </header>

  <main class="container">
    <h1>{args.name}</h1>
    <p class="muted">Choose a chapter.</p>
    <div id="toc"></div>
  </main>

  <script src="../../bible_index.js"></script>
  <script src="../../assets/app.js"></script>
  <script>
    (async function(){{
      const idx = await loadIndex();
      window.renderBookTOC(idx, "{args.slug}");
    }})();
  </script>
</body>
</html>"""
    toc_path.write_text(toc_html, encoding="utf-8")

# create chapter folders with chapter index template
chapter_template = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <title>{{BOOK}} {{CH}} — Hebrew Bible</title>
  <link rel="stylesheet" href="../../../assets/styles.css" />
</head>
<body>
  <header class="topbar">
    <div class="brand"><a href="../../../index.html">Hebrew Bible</a></div>
    <div class="nav">
      <a class="btn" href="../index.html">Book TOC</a>
      <span class="spacer"></span>
      <label class="small muted">Book</label>
      <select id="bookSelect"></select>
      <label class="small muted">Chapter</label>
      <select id="chapterSelect"></select>
      <a class="btn" id="prevBtn" href="#">Prev</a>
      <a class="btn" id="nextBtn" href="#">Next</a>
    </div>
  </header>

  <main class="container">
    <h1 id="chapterTitle">{{BOOK}} {{CH}}</h1>
    <div class="grid">
      <section>
        <div class="controls">
          <input id="search" placeholder="Search (Hebrew / English / translation)..." />
          <label><input type="checkbox" id="toggleInterlinear" checked /> Interlinear</label>
          <label><input type="checkbox" id="toggleTranslit" checked /> Transliteration</label>
          <label><input type="checkbox" id="toggleEnglish" checked /> English</label>
        </div>
        <div class="controls">
          <label class="small muted">TTS Speed</label>
          <input type="range" id="ttsRate" min="0.6" max="1.4" step="0.05" value="1.0" />
          <span class="small muted" id="ttsRateVal">1.0×</span>
        </div>
        <div id="verses"></div>
      </section>

      <aside>
        <details open>
          <summary>How to add chapters</summary>
          <div class="muted small">
            <ol>
              <li>Create /books/{{SLUG}}/{{NN}}/ (e.g. 02)</li>
              <li>Put <code>index.html</code> (copy from another chapter)</li>
              <li>Drop <code>data.json</code> (Spec v1.2)</li>
              <li>Run <code>python3 tools/make_data_js.py books/{{SLUG}}/{{NN}}/data.json</code></li>
              <li>Update <code>bible_index.json</code> via <code>python3 tools/update_index.py ...</code></li>
            </ol>
          </div>
        </details>

        <details open>
          <summary>Token info</summary>
          <div id="tokenInfo"></div>
        </details>

        <details>
          <summary>Grammar notes</summary>
          <div id="grammar"></div>
        </details>

        <details>
          <summary>Vocabulary</summary>
          <div id="lexicon"></div>
        </details>

        <details>
          <summary>Exercises</summary>
          <div id="exercises"></div>
        </details>
      </aside>
    </div>
  </main>

  <script src="./data.js"></script>
  <script src="../../../bible_index.js"></script>
  <script src="../../../assets/app.js"></script>
  <script>renderAll();</script>
</body>
</html>
"""

for ch in range(1, args.chapters+1):
    ch_dir = book_dir / f"{ch:02d}"
    ch_dir.mkdir(parents=True, exist_ok=True)
    idxp = ch_dir / "index.html"
    if not idxp.exists():
        html = chapter_template.replace("{{BOOK}}", args.name).replace("{{CH}}", str(ch)).replace("{{SLUG}}", args.slug).replace("{{NN}}", f"{ch:02d}")
        idxp.write_text(html, encoding="utf-8")
    # create stub data.json if missing
    dj = ch_dir / "data.json"
    if not dj.exists():
        stub = {
            "spec_version":"1.2",
            "tagset":{"name":"ETCBC-like","version":"1.0","notes":"features object follows ETCBC-style categories; 'morph' derived for display."},
            "title": f"{args.name} {ch}",
            "book": args.name,
            "book_slug": args.slug,
            "chapter": ch,
            "ref_system":"MT",
            "verses": [],
            "lexicon": [],
            "grammar": [],
            "exercises": [],
            "annotations": [],
            "generated_at": ""
        }
        dj.write_text(json.dumps(stub, ensure_ascii=False, indent=2), encoding="utf-8")
    # data.js
    from json import loads, dumps
    obj = loads(dj.read_text(encoding="utf-8"))
    (ch_dir / "data.js").write_text("window.__chapterData = " + dumps(obj, ensure_ascii=False, indent=2) + ";\n", encoding="utf-8")

print("Scaffolded book:", args.slug, "with", args.chapters, "chapters")
