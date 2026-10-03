#!/usr/bin/env python3
"""Generate assets/glyphs.svg from the 5x7 bitmap font below.

Each glyph is 5 columns (20px) x 7 rows (28px) on the 4px grid.
'#' = ink, '.' = empty. Fill is inherited from the parent .pf-ink group,
so the generated <rect>s carry no fill. Edit a bitmap and re-run:

    python3 tools/glyphs.py

Outer corners are chamfered one cell, like O: a top/bottom stroke stops
one cell short of the side stroke. See AGENTS.md for the font spec.
"""

from pathlib import Path

CELL = 4
COLS = 5
ROWS = 7

GLYPHS = {
    "A": [
        ".###.",
        "#...#",
        "#...#",
        "#####",
        "#...#",
        "#...#",
        "#...#",
    ],
    "B": [
        "####.",
        "#...#",
        "#...#",
        "####.",
        "#...#",
        "#...#",
        "####.",
    ],
    "C": [
        ".###.",
        "#...#",
        "#....",
        "#....",
        "#....",
        "#...#",
        ".###.",
    ],
    "D": [
        "####.",
        "#...#",
        "#...#",
        "#...#",
        "#...#",
        "#...#",
        "####.",
    ],
    "E": [
        "#####",
        "#....",
        "#....",
        "####.",
        "#....",
        "#....",
        "#####",
    ],
    "F": [
        "#####",
        "#....",
        "#....",
        "####.",
        "#....",
        "#....",
        "#....",
    ],
    "G": [
        ".###.",
        "#...#",
        "#....",
        "#.###",
        "#...#",
        "#...#",
        ".###.",
    ],
    "H": [
        "#...#",
        "#...#",
        "#...#",
        "#####",
        "#...#",
        "#...#",
        "#...#",
    ],
    "I": [
        ".###.",
        "..#..",
        "..#..",
        "..#..",
        "..#..",
        "..#..",
        ".###.",
    ],
    "J": [
        "..###",
        "....#",
        "....#",
        "....#",
        "#...#",
        "#...#",
        ".###.",
    ],
    "K": [
        "#...#",
        "#..#.",
        "#.#..",
        "##...",
        "#.#..",
        "#..#.",
        "#...#",
    ],
    "L": [
        "#....",
        "#....",
        "#....",
        "#....",
        "#....",
        "#....",
        "#####",
    ],
    "M": [
        "#...#",
        "##.##",
        "#.#.#",
        "#...#",
        "#...#",
        "#...#",
        "#...#",
    ],
    "N": [
        "#...#",
        "##..#",
        "#.#.#",
        "#..##",
        "#...#",
        "#...#",
        "#...#",
    ],
    "O": [
        ".###.",
        "#...#",
        "#...#",
        "#...#",
        "#...#",
        "#...#",
        ".###.",
    ],
    "P": [
        "####.",
        "#...#",
        "#...#",
        "####.",
        "#....",
        "#....",
        "#....",
    ],
    "Q": [
        ".###.",
        "#...#",
        "#...#",
        "#...#",
        "#.#.#",
        "#..#.",
        ".##.#",
    ],
    "R": [
        "####.",
        "#...#",
        "#...#",
        "####.",
        "#.#..",
        "#..#.",
        "#...#",
    ],
    "S": [
        ".###.",
        "#...#",
        "#....",
        ".###.",
        "....#",
        "#...#",
        ".###.",
    ],
    "T": [
        "#####",
        "..#..",
        "..#..",
        "..#..",
        "..#..",
        "..#..",
        "..#..",
    ],
    "U": [
        "#...#",
        "#...#",
        "#...#",
        "#...#",
        "#...#",
        "#...#",
        ".###.",
    ],
    "V": [
        "#...#",
        "#...#",
        "#...#",
        "#...#",
        "#...#",
        ".#.#.",
        "..#..",
    ],
    "W": [
        "#...#",
        "#...#",
        "#...#",
        "#...#",
        "#.#.#",
        "##.##",
        "#...#",
    ],
    "X": [
        "#...#",
        "#...#",
        ".#.#.",
        "..#..",
        ".#.#.",
        "#...#",
        "#...#",
    ],
    "Y": [
        "#...#",
        "#...#",
        ".#.#.",
        "..#..",
        "..#..",
        "..#..",
        "..#..",
    ],
    "Z": [
        "#####",
        "....#",
        "...#.",
        "..#..",
        ".#...",
        "#....",
        "#####",
    ],
    "space": [
        ".....",
        ".....",
        ".....",
        ".....",
        ".....",
        ".....",
        ".....",
    ],
    "dash": [
        ".....",
        ".....",
        ".....",
        ".###.",
        ".....",
        ".....",
        ".....",
    ],
    # Punctuation — full-height (7-row) but narrower than letters, at the
    # same 4px pixel size, with a tighter 14px advance.
    "dot": {
        "cell": 4,
        "advance": 14,
        "rows": [".", ".", ".", ".", ".", ".", "#"],
    },
    "comma": {
        "cell": 4,
        "advance": 14,
        "rows": ["..", "..", "..", "..", "..", ".#", "#."],
    },
    "bang": [
        "..#..",
        "..#..",
        "..#..",
        "..#..",
        "..#..",
        ".....",
        "..#..",
    ],
}

DEFAULT_ADVANCE = COLS * CELL + CELL  # 24px for a full 5x7 glyph


def parts(glyph):
    """Return (cell, rows, advance) for a glyph (list = 5x7, or dict form)."""
    if isinstance(glyph, dict):
        return (
            glyph.get("cell", CELL),
            glyph["rows"],
            glyph.get("advance", DEFAULT_ADVANCE),
        )
    return CELL, glyph, DEFAULT_ADVANCE

# Reference-sheet layout: glyph id order and positions.
SHEET_ROW_1 = [g for g in list(GLYPHS)[:26]]          # A-Z
SHEET_ROW_2 = ["space", "dash", "dot", "comma", "bang"]
SHEET_WIDTH = 800
START_X = 36
ADVANCE = COLS * CELL + CELL  # 24px: glyph + one 4px cell gap
ROW_1_Y = 56
ROW_2_Y = 130
SHEET_HEIGHT = 190


def validate():
    for name, glyph in GLYPHS.items():
        cell, rows, _ = parts(glyph)
        assert rows, f"{name}: no rows"
        w = len(rows[0])
        for r in rows:
            assert len(r) == w, f"{name}: row {r!r} is {len(r)} wide (want {w})"
        if not isinstance(glyph, dict):
            assert len(rows) == ROWS and w == COLS, f"{name}: not 5x7"
        assert any("#" in r for r in rows) or name == "space", f"{name}: empty glyph"


def glyph_body(glyph):
    """Draw the glyph at (0,0), baseline-aligned within the 28px cap height."""
    cell, rows, _ = parts(glyph)
    y_off = ROWS * CELL - len(rows) * cell
    rects = []
    for ry, row in enumerate(rows):
        for cx, ch in enumerate(row):
            if ch == "#":
                rects.append(
                    f'      <rect x="{cx * cell}" y="{y_off + ry * cell}" '
                    f'width="{cell}" height="{cell}"/>'
                )
    if not rects:
        return ""
    return "\n".join(rects)


def build_defs():
    blocks = []
    for name, glyph in GLYPHS.items():
        body = glyph_body(glyph)
        if body:
            blocks.append(f"    <!-- {name} -->\n    <g id=\"g-{name}\">\n{body}\n    </g>")
        else:
            blocks.append(f"    <!-- {name} -->\n    <g id=\"g-{name}\"></g>")
    return "\n\n".join(blocks)


def build_sheet():
    def uses(row, y):
        return "\n".join(
            f'    <use href="#g-{g}" x="{START_X + i * ADVANCE}" y="{y}"/>'
            for i, g in enumerate(row)
        )

    return f"""{uses(SHEET_ROW_1, ROW_1_Y)}

    <!-- space / dash / dot -->
{uses(SHEET_ROW_2, ROW_2_Y)}"""


def main():
    validate()
    out = f"""<svg xmlns="http://www.w3.org/2000/svg"
     width="{SHEET_WIDTH}" height="{SHEET_HEIGHT}" viewBox="0 0 {SHEET_WIDTH} {SHEET_HEIGHT}"
     style="--pf-canvas: #f4e4bc; --pf-ink: #3d2818;">
  <style>
    :root {{ --pf-canvas: #f4e4bc; --pf-ink: #3d2818; }}
    .pf-canvas {{ fill: var(--pf-canvas); }}
    .pf-ink    {{ fill: var(--pf-ink); }}
  </style>

  <!--
    Canonical pixel glyph library: uppercase A-Z plus space, dash, bang.
    Letters are 5 cols x 7 rows (20x28px) at a 4px cell, advance 24px, outer
    corners chamfered one cell like O. dot/comma are small 2px-cell marks
    with a tighter advance, baseline-aligned. No fill on the rects: ink is
    inherited from .pf-ink. Copy the <g id="g-X"> snippet you need into a
    banner's <defs>, then compose with <use href="#g-X" x=".." y="32"/>.
    Within one file only. Generated by tools/glyphs.py - edit that, not this.
  -->

  <defs>
{build_defs()}
  </defs>

  <rect class="pf-canvas" x="0" y="0" width="{SHEET_WIDTH}" height="{SHEET_HEIGHT}"/>
  <g class="pf-ink">
{build_sheet()}
  </g>
</svg>
"""
    target = Path(__file__).resolve().parent.parent / "assets" / "glyphs.svg"
    target.write_text(out)
    print(f"wrote {target} ({len(GLYPHS)} glyphs)")


if __name__ == "__main__":
    main()
