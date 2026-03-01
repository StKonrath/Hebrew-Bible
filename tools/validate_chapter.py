#!/usr/bin/env python3
"""
validate_chapter.py

Validate a chapter data.json against schema/chapter.schema.json.

Requires: pip install jsonschema

Usage:
  python3 tools/validate_chapter.py books/song-of-songs/02/data.json
  python3 tools/validate_chapter.py --all
"""
import sys

try:
    import jsonschema
except ImportError:
    print("Missing dependency: jsonschema. Install with: pip install jsonschema")
    raise SystemExit(2)

from utils import load_json, all_chapter_jsons, ROOT

SCHEMA_PATH = ROOT / "schema" / "chapter.schema.json"

def validate_file(fp, schema):
    data = load_json(fp)
    jsonschema.validate(instance=data, schema=schema)
    return True

def main(argv):
    schema = load_json(SCHEMA_PATH)
    if len(argv) >= 2 and argv[1] == "--all":
        ok = 0
        for f in all_chapter_jsons():
            try:
                validate_file(f, schema)
                ok += 1
            except Exception as e:
                print("FAIL:", f)
                print(" ", e)
                return 1
        print(f"OK: {ok} files validated")
        return 0

    if len(argv) < 2:
        print("Usage: python3 tools/validate_chapter.py <path/to/data.json> | --all")
        return 2

    validate_file(argv[1], schema)
    print("OK:", argv[1])
    return 0

if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
