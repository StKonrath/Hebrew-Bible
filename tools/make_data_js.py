#!/usr/bin/env python3
import argparse
import json
import pathlib
import glob

ROOT = pathlib.Path(__file__).resolve().parents[1]

def build_js(json_path: pathlib.Path):
    obj = json.loads(json_path.read_text(encoding="utf-8"))
    out = json_path.with_name("data.js")
    out.write_text(
        "window.__chapterData = " +
        json.dumps(obj, ensure_ascii=False, indent=2) +
        ";\n",
        encoding="utf-8"
    )
    print("Wrote", out)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("path", nargs="?", help="Path to data.json")
    parser.add_argument("--all", action="store_true")
    args = parser.parse_args()

    if args.all:
        files = glob.glob(str(ROOT / "books" / "*" / "*" / "data.json"))
        for f in sorted(files):
            build_js(pathlib.Path(f))
        return

    if not args.path:
        print("Usage: make_data_js.py <path/to/data.json> or --all")
        return

    build_js(pathlib.Path(args.path))

if __name__ == "__main__":
    main()