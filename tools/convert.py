#!/usr/bin/env python3
"""Import clean pixel-art images into reusable icon snippets.

Handles PNG, or SVG wrapping an embedded raster <image> (data URI). The
image must be flat-color, hard-alpha, axis-aligned pixel art (possibly
upscaled by a non-integer factor). For each input it:

  * finds the native cell grid (transition-line detection, gap splitting)
  * crops to the content bounding box
  * samples one color per cell and keeps exact hex
  * writes a self-contained snippet to <out>/<slug>.svg
  * merges the bitmap + palette into <json>

Usage:
    python3 tools/convert.py <image> --out assets/icons --json tools/imported_icons.json
    python3 tools/convert.py path/to/Diamond.png --cell 4 --stdout

Icons keep a local exact palette ("./pf-<slug>-n"); they are not themeable.
"""

import argparse
import base64
import io
import json
import re
from pathlib import Path
from statistics import median

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
CHARSET = "123456789abcdefghijklmnopqrstuvwxyz"


def load_image(path):
    path = Path(path)
    if path.suffix.lower() == ".svg":
        src = path.read_text()
        m = re.search(r"base64,([A-Za-z0-9+/=\s]+?)['\"]", src, re.S)
        if not m:
            raise SystemExit(f"{path}: no embedded raster (base64) found")
        raw = base64.b64decode(re.sub(r"\s", "", m.group(1)))
        return Image.open(io.BytesIO(raw)).convert("RGBA")
    return Image.open(path).convert("RGBA")


def fill_gaps(lines, far):
    xs = sorted(set(lines) | {far})
    gaps = [xs[i + 1] - xs[i] for i in range(len(xs) - 1)]
    base = round(median(gaps)) if gaps else 1
    out = [xs[0]]
    for i in range(len(xs) - 1):
        a, b = xs[i], xs[i + 1]
        k = max(1, round((b - a) / base))
        for j in range(1, k + 1):
            out.append(round(a + (b - a) * j / k))
    return out


def extract(path):
    im = load_image(path)
    bbox = im.getchannel("A").getbbox()
    if not bbox:
        raise SystemExit(f"{path}: image is fully transparent")
    x0, y0, x1, y1 = bbox
    px = im.load()

    xl, yl = set(), set()
    for y in range(y0, y1):
        prev = None
        for x in range(x0, x1):
            c = px[x, y]
            if c != prev:
                xl.add(x)
                prev = c
    for x in range(x0, x1):
        prev = None
        for y in range(y0, y1):
            c = px[x, y]
            if c != prev:
                yl.add(y)
                prev = c

    xE = fill_gaps(xl, x1)
    yE = fill_gaps(yl, y1)
    cols, rows = len(xE) - 1, len(yE) - 1

    color_index = {}
    grid = []
    nonuniform = 0
    for r in range(rows):
        line = []
        for c in range(cols):
            cx = (xE[c] + xE[c + 1]) // 2
            cy = (yE[r] + yE[r + 1]) // 2
            col = px[cx, cy]
            if col[3] == 0:
                line.append(".")
            else:
                if col not in color_index:
                    color_index[col] = CHARSET[len(color_index)]
                line.append(color_index[col])
            if len(set(im.crop((xE[c], yE[r], xE[c + 1], yE[r + 1])).getdata())) > 1:
                nonuniform += 1
        grid.append("".join(line))
    if nonuniform:
        raise SystemExit(
            f"{path}: {nonuniform} non-uniform cells - not flat pixel art?"
        )
    return cols, rows, grid, color_index


def slugify(name):
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", name.lower())).strip("-")


def build_entry(slug, cell, grid, color_index):
    palette = {}
    for color, ch in color_index.items():
        token = f"pf-{slug}-{ch}"
        palette[ch] = [token, "#%02x%02x%02x" % (color[0], color[1], color[2])]
    return {"cell": cell, "rows": grid, "palette": palette}


def icon_rects(entry):
    cell = entry["cell"]
    out = []
    for ry, row in enumerate(entry["rows"]):
        for cx, ch in enumerate(row):
            if ch == ".":
                continue
            out.append(
                f'    <rect x="{cx * cell}" y="{ry * cell}" width="{cell}" '
                f'height="{cell}" class="{entry["palette"][ch][0]}"/>'
            )
    return out


def snippet_svg(slug, entry, display):
    cell = entry["cell"]
    cols = len(entry["rows"][0])
    rows = len(entry["rows"])
    w, h = cols * cell, rows * cell
    tokens = {f"--{tok}": hexv for tok, hexv in entry["palette"].values()}
    inline = "".join(f"{k}: {v};" for k, v in tokens.items())
    root = " ".join(f"{k}: {v};" for k, v in tokens.items())
    classes = "\n".join(
        f"    .{tok} {{ fill: var(--{tok}); }}" for tok, _ in entry["palette"].values()
    )
    body = "\n".join(icon_rects(entry))
    return f"""<svg xmlns="http://www.w3.org/2000/svg"
     width="{w * display}" height="{h * display}" viewBox="0 0 {w} {h}"
     shape-rendering="crispEdges"
     style="{inline}">
  <style>
    :root {{ {root} }}
{classes}
  </style>

  <!-- {slug}: {cols}x{rows} cells of {cell}px. Copy the <g id="i-{slug}"> below into a banner <defs>. -->
  <g id="i-{slug}">
{body}
  </g>
</svg>
"""


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("inputs", nargs="+", help="image file(s) or directory")
    ap.add_argument("--cell", type=int, default=3)
    ap.add_argument("--display", type=int, default=2, help="standalone SVG display scale")
    ap.add_argument("--out", default="assets/icons", help="snippet output dir")
    ap.add_argument("--json", default="tools/imported_icons.json", help="registry file")
    ap.add_argument("--stdout", action="store_true", help="print registry, don't write")
    args = ap.parse_args()

    files = []
    for inp in args.inputs:
        p = Path(inp)
        if p.is_dir():
            files += sorted(p.glob("*.png")) + sorted(p.glob("*.svg"))
        else:
            files.append(p)
    if not files:
        raise SystemExit("no input images found")

    out_dir = ROOT / args.out
    registry_path = ROOT / args.json
    registry = json.loads(registry_path.read_text()) if registry_path.exists() else {}

    if not args.stdout:
        out_dir.mkdir(parents=True, exist_ok=True)

    for f in files:
        slug = slugify(f.stem)
        cols, rows, grid, color_index = extract(f)
        entry = build_entry(slug, args.cell, grid, color_index)
        registry[slug] = entry
        if args.stdout:
            print(f"{slug}: {cols}x{rows}, {len(color_index)} colors")
        else:
            out = out_dir / f"{slug}.svg"
            out.write_text(snippet_svg(slug, entry, args.display))
            print(f"{f.name:20} -> {out.relative_to(ROOT)}  {cols}x{rows}, {len(color_index)} colors")

    if args.stdout:
        print(json.dumps(registry, indent=2))
    else:
        registry_path.write_text(json.dumps(registry, indent=2) + "\n")
        print(f"updated {registry_path.relative_to(ROOT)} ({len(registry)} icons)")


if __name__ == "__main__":
    main()
