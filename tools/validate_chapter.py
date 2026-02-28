#!/usr/bin/env python3
"""
validate_chapter.py

Validate a chapter data.json against schema/chapter.schema.json.

Requires:
  pip install jsonschema

Usage:
  python3 tools/validate_chapter.py books/song-of-songs/02/data.json
  python3 tools/validate_chapter.py --all
"""
import json, pathlib, sys, glob

try:
    import jsonschema
except ImportError:
    print("Missing dependency: jsonschema. Install with: pip install jsonschema")
    raise SystemExit(2)

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schema" / "chapter.schema.json"

def load_schema():
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))

def validate_file(fp, schema):
    data = json.loads(pathlib.Path(fp).read_text(encoding="utf-8"))
    jsonschema.validate(instance=data, schema=schema)
    return True

def main(argv):
    schema = load_schema()
    if len(argv) >= 2 and argv[1] == "--all":
        files = glob.glob(str(ROOT / "books" / "*" / "*" / "data.json"))
        ok = 0
        for f in sorted(files):
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

    fp = argv[1]
    validate_file(fp, schema)
    print("OK:", fp)
    return 0

if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
