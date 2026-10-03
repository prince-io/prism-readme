#!/usr/bin/env python3
"""Validate every SVG in the repo.

    python3 tools/check.py

Checks:
  1. parses as XML
  2. element ids are unique within a file
  3. every <use href="#..."> resolves to an id in the same file
  4. no raw hex colors outside token/style blocks (see --allow-legacy)
"""

import glob
import re
import sys
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parent.parent
NS = "{http://www.w3.org/2000/svg}"

HEX = re.compile(r"#[0-9a-fA-F]{6}\b")
STYLE_EL = re.compile(r"<style>.*?</style>", re.S)
STYLE_ATTR = re.compile(r'style="[^"]*"')
COMMENT = re.compile(r"<!--.*?-->", re.S)


def strip_styles(src):
    return STYLE_ATTR.sub("", STYLE_EL.sub("", src))


def main():
    include_archive = "--all" in sys.argv
    ok = True
    for path in sorted(glob.glob(str(ROOT / "**" / "*.svg"), recursive=True)):
        rel = Path(path).relative_to(ROOT)
        if rel.parts and rel.parts[0] == "archive" and not include_archive:
            continue
        try:
            root = ET.parse(path).getroot()
        except ET.ParseError as e:
            ok = False
            print(f"FAIL {rel}: XML: {e}")
            continue

        ids = [e.get("id") for e in root.iter() if e.get("id")]
        dupes = sorted({i for i in ids if ids.count(i) > 1})
        uses = [
            (e.get("href") or "")[1:]
            for e in root.iter()
            if e.tag == NS + "use" and (e.get("href") or "").startswith("#")
        ]
        missing = sorted(set(uses) - set(ids))

        src = open(path).read()
        allow_hex = "data-allow-raw-hex" in src
        raw = HEX.findall(strip_styles(COMMENT.sub("", src)))
        raw_bad = sorted(set(raw)) if not allow_hex else []

        problems = []
        if dupes:
            problems.append(f"dupe ids {dupes}")
        if missing:
            problems.append(f"unresolved use {missing}")
        if raw_bad:
            problems.append(f"raw hex {raw_bad}")

        if problems:
            ok = False
            print(f"FAIL {rel}: " + "; ".join(problems))
        else:
            print(f"OK   {rel}")

    print("PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
