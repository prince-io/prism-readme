#!/usr/bin/env python3
"""Generate assets/icons.svg from the pixel-art icon bitmaps below.

Icons are independent of the 5x7 font: each has its own width x height and
its own cell size (2-4px). Every character in a bitmap maps to a --pf-*
token class via PALETTE, so icons are multi-color and themeable.

Edit a bitmap and re-run:

    python3 tools/icons.py

See AGENTS.md for the icon spec.
"""

import json
from pathlib import Path

# char -> CSS class (which reads a --pf-* token) for the built-in icons.
PALETTE = {
    "k": "pf-ink",
    "m": "pf-ink-muted",
    "d": "pf-frame-outer",
    "h": "pf-frame-hi",
    "c": "pf-canvas",
    "f": "pf-tile-face",
    "r": "pf-accent-red",
    "g": "pf-accent-green",
    "G": "pf-accent-green-lo",
    "y": "pf-accent-yellow",
    "Y": "pf-accent-gold-lo",
    "b": "pf-accent-blue",
    "w": "pf-cloud",
    "P": "pf-accent-pink",
    "L": "pf-accent-pink-hi",
    "S": "pf-steel",
    "B": "pf-steel-hi",
}

# name -> {cell, rows}. "." and " " are empty.
ICONS = {
    "dot": {
        "cell": 4,
        "rows": [
            "kk",
            "kk",
        ],
    },
    "square": {
        "cell": 4,
        "rows": [
            "kkk",
            "kkk",
            "kkk",
        ],
    },
    "plus": {
        "cell": 4,
        "rows": [
            ".k.",
            "kkk",
            ".k.",
        ],
    },
    "triangle": {
        "cell": 4,
        "rows": [
            "k..",
            "kk.",
            "kkk",
            "kk.",
            "k..",
        ],
    },
}

# Icons imported from pixels by tools/convert.py carry their own exact
# palette: "palette" maps char -> [class, "#hex"] instead of the global
# PALETTE. They are merged in here.
def _load_imported():
    path = Path(__file__).resolve().parent / "imported_icons.json"
    if not path.exists():
        return
    for name, entry in json.loads(path.read_text()).items():
        ICONS[name] = {
            "cell": entry["cell"],
            "rows": entry["rows"],
            "palette": entry["palette"],
        }


_load_imported()


def class_for(icon, ch):
    pal = icon.get("palette")
    return pal[ch][0] if pal else PALETTE[ch]


def local_tokens():
    """class -> hex for every imported (local-palette) icon."""
    out = {}
    for icon in ICONS.values():
        for cls, hexv in icon.get("palette", {}).values():
            out[cls] = hexv
    return out


# Reference-sheet layout.
SHEET_WIDTH = 800
START_X = 24
START_Y = 40
GAP = 24
SCALE = 2
LABEL_GAP = 6


def validate():
    for name, icon in ICONS.items():
        rows = icon["rows"]
        pal = icon.get("palette")
        assert rows, f"{name}: no rows"
        w = len(rows[0])
        for r in rows:
            assert len(r) == w, f"{name}: row {r!r} width {len(r)} != {w}"
        for r in rows:
            for ch in r:
                if ch in ". ":
                    continue
                ok = ch in pal if pal else ch in PALETTE
                assert ok, f"{name}: char {ch!r} not in palette"


def icon_rects(icon):
    cell, rows = icon["cell"], icon["rows"]
    out = []
    for ry, row in enumerate(rows):
        for cx, ch in enumerate(row):
            if ch in ". ":
                continue
            out.append(
                f'<rect x="{cx * cell}" y="{ry * cell}" '
                f'width="{cell}" height="{cell}" class="{class_for(icon, ch)}"/>'
            )
    return out


def build_defs():
    blocks = []
    for name, icon in ICONS.items():
        rects = "\n".join("      " + r for r in icon_rects(icon))
        blocks.append(f'    <g id="i-{name}">\n{rects}\n    </g>')
    return "\n\n".join(blocks)


def icon_size(icon):
    return len(icon["rows"][0]) * icon["cell"], len(icon["rows"]) * icon["cell"]


def build_sheet():
    parts = []
    x, y, row_h, max_y = START_X, START_Y, 0, 0
    for name, icon in ICONS.items():
        w, h = icon_size(icon)
        sw, sh = w * SCALE, h * SCALE
        if x + sw > SHEET_WIDTH - START_X:
            x = START_X
            y += row_h + 34
            row_h = 0
        parts.append(
            f'    <use href="#i-{name}" '
            f'transform="translate({x},{y}) scale({SCALE})" />'
        )
        parts.append(
            f'    <text x="{x}" y="{y + sh + LABEL_GAP + 9}" '
            f'font-family="ui-monospace, monospace" font-size="10" '
            f'class="pf-ink">{name}</text>'
        )
        x += sw + GAP
        row_h = max(row_h, sh)
        max_y = max(max_y, y + sh + 24)
    return "\n".join(parts), int(max_y + 8)


def main():
    validate()
    import banner  # lazy: banner imports this module, so keep it off the top

    raw = json.loads(
        (Path(__file__).resolve().parent.parent / "themes" / "light.json").read_text()
    )
    theme = banner.expand_theme(raw)["tokens"]
    local = local_tokens()
    tokens = dict(theme)
    for cls, hexv in local.items():
        tokens[f"--{cls}"] = hexv
    inline = "".join(f"{k}: {v};" for k, v in tokens.items())
    root = " ".join(f"{k}: {v};" for k, v in tokens.items())
    classes = "\n".join(
        f"    .{cls} {{ fill: var(--{cls}); }}"
        for cls in sorted(set(PALETTE.values()) | set(local))
    )
    sheet, height = build_sheet()
    out = f"""<svg xmlns="http://www.w3.org/2000/svg"
     width="{SHEET_WIDTH}" height="{height}" viewBox="0 0 {SHEET_WIDTH} {height}"
     style="{inline}">
  <style>
    :root {{ {root} }}
{classes}
  </style>

  <!--
    Canonical pixel-icon library for banners (bullets, decor, tile glyphs).
    Each <g id="i-x"> is drawn at (0,0) with its own cell size; every rect
    carries a .pf-* token class, so icons are multi-color and themeable.
    Copy the <g> you need into a banner's <defs>, or let tools/banner.py
    place it inline via config. Scale only by integers.
    Generated by tools/icons.py - edit that, not this file.
  -->

  <defs>
{build_defs()}
  </defs>

  <rect class="pf-canvas" x="0" y="0" width="{SHEET_WIDTH}" height="{height}"/>
{sheet}
</svg>
"""
    target = Path(__file__).resolve().parent.parent / "assets" / "icons.svg"
    target.write_text(out)
    print(f"wrote {target} ({len(ICONS)} icons, {SHEET_WIDTH}x{height})")


if __name__ == "__main__":
    main()
