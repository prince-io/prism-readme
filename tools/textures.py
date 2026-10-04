#!/usr/bin/env python3
"""Convert pixel-art block textures into tileable SVG tiles.

Each input PNG is reduced to its native grid (default 16x16, nearest) and
emitted as a self-contained SVG tile: horizontal equal-color runs become
<rect>s, and colors live in a <style> block as local numeric tokens
(exact hex, not themeable). The colors are kept out of raw `fill=` so the
output passes tools/check.py.

Usage:
    python3 tools/textures.py                     # textures/*.png -> textures/svg
    python3 tools/textures.py --sky '#78A7FF'     # also emit textures/svg/sky.svg
    python3 tools/textures.py stone.png --out /tmp/svg
"""

import argparse
import base64
import glob
import io
import re
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent


def slugify(stem):
    stem = re.sub(r"_\d+x\d+$", "", stem)          # drop _512x512 suffix
    stem = re.sub(r"[^a-z0-9]+", "-", stem.lower())
    return re.sub(r"-+", "-", stem).strip("-")


def read_grid(path, size):
    im = Image.open(path).convert("RGBA")
    if im.size != (size, size):
        im = im.resize((size, size), Image.NEAREST)
    return [im.getpixel((x, y)) for y in range(size) for x in range(size)]


def emit(slug, px, size, merge=True):
    """Render one tile. `px` is row-major (size*size) RGBA tuples."""
    order, index = [], {}
    for c in px:
        if c[3] == 0:
            continue
        key = c[:3]
        if key not in index:
            index[key] = len(order)
            order.append(key)

    vars_ = "\n".join(
        f"      --pf-tex-{slug}-{i}: #{r:02x}{g:02x}{b:02x};"
        for i, (r, g, b) in enumerate(order)
    )
    classes = "\n".join(
        f"      .pf-tex-{slug}-{i} {{ fill: var(--pf-tex-{slug}-{i}); }}"
        for i in range(len(order))
    )

    rects = []
    for y in range(size):
        x = 0
        while x < size:
            c = px[y * size + x]
            if c[3] == 0:
                x += 1
                continue
            n = 1
            if merge:
                while x + n < size and px[y * size + x + n][:3] == c[:3]:
                    n += 1
            k = index[c[:3]]
            rects.append(
                f'  <rect x="{x}" y="{y}" width="{n}" height="1" '
                f'class="pf-tex-{slug}-{k}"/>'
            )
            x += n

    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="512" height="512" '
        f'viewBox="0 0 {size} {size}" shape-rendering="crispEdges">\n'
        f"  <style>\n    :root {{\n{vars_}\n    }}\n{classes}\n  </style>\n"
        + "\n".join(rects)
        + "\n</svg>\n"
    )


def hex_rgb(value):
    h = value.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def embed_svg(path, width=None):
    """Wrap a raster at native (or resized) size in a self-contained SVG <image>."""
    im = Image.open(path).convert("RGBA")
    if width and width != im.width:
        h = round(width * im.height / im.width)
        im = im.resize((width, h), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, format="PNG")
    b64 = base64.b64encode(buf.getvalue()).decode("ascii")
    w, h = im.size
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
        f'viewBox="0 0 {w} {h}">\n'
        f'  <image x="0" y="0" width="{w}" height="{h}" '
        f'href="data:image/png;base64,{b64}"/>\n</svg>\n'
    )


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("inputs", nargs="*", help="PNG file(s); default textures/*.png")
    ap.add_argument("--out", default="textures/svg", help="output dir (repo-relative)")
    ap.add_argument("--size", type=int, default=16, help="native grid size")
    ap.add_argument("--sky", default=None, metavar="#RRGGBB",
                    help="also emit a solid sky tile of this color")
    ap.add_argument("--embed", action="store_true",
                    help="emit a native-size self-contained <image> SVG (no tiling)")
    ap.add_argument("--embed-width", type=int, default=None,
                    help="resize embedded raster to this width (aspect kept)")
    args = ap.parse_args()

    files = args.inputs or sorted(glob.glob(str(ROOT / "textures" / "*.png")))
    if not files:
        raise SystemExit("no input textures found")

    out_dir = ROOT / args.out
    out_dir.mkdir(parents=True, exist_ok=True)

    for f in files:
        slug = slugify(Path(f).stem)
        out = out_dir / f"{slug}.svg"
        if args.embed:
            out.write_text(embed_svg(f, args.embed_width))
            w, h = Image.open(f).size
            note = f" (from {w}x{h})" if args.embed_width else ""
            print(f"{Path(f).name:34s} -> {out.relative_to(ROOT)}  embedded{note}")
            continue
        px = read_grid(f, args.size)
        out.write_text(emit(slug, px, args.size))
        colors = len({c[:3] for c in px if c[3]})
        print(f"{Path(f).name:34s} -> {out.relative_to(ROOT)}  {args.size}x{args.size}, {colors} colors")

    if args.sky:
        rgb = hex_rgb(args.sky)
        px = [(*rgb, 255)] * (args.size * args.size)
        out = out_dir / "sky.svg"
        out.write_text(emit("sky", px, args.size, merge=False))
        print(f"{'sky':34s} -> {out.relative_to(ROOT)}  {args.size}x{args.size}, 1 color {args.sky}")


if __name__ == "__main__":
    main()
