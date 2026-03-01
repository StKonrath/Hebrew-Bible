#!/usr/bin/env python3
"""
make_data_js.py — Generate data.js wrappers from data.json files.

Usage:
  python3 tools/make_data_js.py books/song-of-songs/02/data.json
  python3 tools/make_data_js.py --all
"""
import argparse, pathlib
from utils import write_data_js, all_chapter_jsons

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("path", nargs="?", help="Path to data.json")
    ap.add_argument("--all", action="store_true")
    args = ap.parse_args()

    if args.all:
        for f in all_chapter_jsons():
            out = write_data_js(f)
            print("Wrote", out)
        return

    if not args.path:
        print("Usage: make_data_js.py <path/to/data.json> or --all")
        return

    out = write_data_js(pathlib.Path(args.path))
    print("Wrote", out)

if __name__ == "__main__":
    main()
