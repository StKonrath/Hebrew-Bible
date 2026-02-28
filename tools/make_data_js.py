#!/usr/bin/env python3
"""
make_data_js.py
Generate data.js (file:// friendly) from a chapter data.json.

Usage:
  python3 tools/make_data_js.py books/song-of-songs/01/data.json
"""
import json, sys, pathlib

p = pathlib.Path(sys.argv[1]).resolve()
obj = json.loads(p.read_text(encoding="utf-8"))
out = p.with_name("data.js")
out.write_text("window.__chapterData = " + json.dumps(obj, ensure_ascii=False, indent=2) + ";\n", encoding="utf-8")
print("Wrote", out)
