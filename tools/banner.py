#!/usr/bin/env python3
"""Render a banner SVG from a JSON config + a theme, in inline mode.

Glyphs and icons are flattened into <rect>s (no <use>), so the output is
safe under GitHub's SVG sanitizer. Imported by tools/build.py; can also be
used directly:

    from banner import render, load_theme
    svg = render(config, load_theme("light"))

See banners/AGENTS.md for the config schema.
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))

import glyphs as _glyphs  # noqa: E402
import icons as _icons  # noqa: E402
import skyline as _skyline  # noqa: E402

GLYPH_CELL = 4
GLYPH_ROWS = 7
ADVANCE = 24

CHASE_DURATION = 0.5   # seconds per chase cycle (smaller = faster)
CHASE_ON = 8           # lit dash length (px) at 2px cells
CHASE_OFF = 6          # dark gap length (px) at 2px cells
CHASE_STEPS = (CHASE_ON + CHASE_OFF) // 2          # phases (14px / 2px = 7)
CHASE_OFF_FRACTION = CHASE_OFF / (CHASE_ON + CHASE_OFF)

CHAR_ALIAS = {" ": "space", "-": "dash", ".": "dot", ",": "comma", "!": "bang"}


def _hex_luminance(hexv):
    h = hexv.lstrip("#")
    chan = []
    for i in (0, 2, 4):
        c = int(h[i:i + 2], 16) / 255
        chan.append(c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4)
    r, g, b = chan
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def _contrast(a, b):
    la, lb = _hex_luminance(a), _hex_luminance(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


def _contrast_pick(bg, options):
    """Return whichever option contrasts most against bg."""
    return max(options, key=lambda c: _contrast(bg, c))


def expand_theme(raw):
    """Expand a 9-color palette into the full --pf-* token dict.

    A palette is three hues (primary/secondary/tertiary), each with a
    `light`/`main`/`dark` shade, plus a `mode` ("light" or "dark"):

        { "name": ..., "mode": "light",
          "primary":   { "light": "#..", "main": "#..", "dark": "#.." },
          "secondary": { ... }, "tertiary": { ... } }

    The 9 raw colors are also exposed as first-class tokens
    (`--pf-primary[-hi|-lo]`, likewise secondary/tertiary), where `hi` is the
    light shade and `lo` the dark shade. A theme that already carries
    "tokens" is passed through unchanged.
    """
    if "tokens" in raw:
        return {"name": raw.get("name"), "tokens": raw["tokens"]}
    light = raw.get("mode", "light") != "dark"
    p, s, t = (raw[k] for k in ("primary", "secondary", "tertiary"))
    panel = "light" if light else "dark"
    canvas = p["light"] if light else p["dark"]
    ink = _contrast_pick(canvas, [s["light"], s["dark"]])
    ink_muted = _contrast_pick(
        canvas, [c for c in (s["light"], s["main"], s["dark"]) if c != ink]
    )
    box_ink = _contrast_pick(t["main"], [s["light"], s["dark"]])
    tokens = {
        # first-class palette (hi = light shade, main, lo = dark shade)
        "--pf-primary-hi": p["light"],
        "--pf-primary": p["main"],
        "--pf-primary-lo": p["dark"],
        "--pf-secondary-hi": s["light"],
        "--pf-secondary": s["main"],
        "--pf-secondary-lo": s["dark"],
        "--pf-tertiary-hi": t["light"],
        "--pf-tertiary": t["main"],
        "--pf-tertiary-lo": t["dark"],
        # structure
        "--pf-frame-outer": t["dark"],
        "--pf-frame-mid": t["main"],
        "--pf-frame-hi": t["light"],
        "--pf-frame-inner": t["dark"],
        "--pf-canvas": canvas,
        "--pf-ink": ink,
        "--pf-ink-muted": ink_muted,
        "--pf-box-ink": box_ink,
        "--pf-tile-face": t["light"] if light else t["dark"],
        "--pf-tile-edge-hi": t["main"],
        "--pf-tile-edge-lo": t["dark"],
        "--pf-panel-1": p[panel],
        "--pf-panel-2": s[panel],
        "--pf-panel-3": t[panel],
        # accents collapse onto the three hues (icons become tri-color)
        "--pf-accent-red": p["main"],
        "--pf-accent-pink": p["main"],
        "--pf-accent-pink-hi": p["light"],
        "--pf-accent-green": t["main"],
        "--pf-accent-green-lo": t["dark"],
        "--pf-accent-yellow": s["main"],
        "--pf-accent-gold-lo": s["dark"],
        "--pf-accent-blue": t["light"],
        "--pf-steel": s["main"],
        "--pf-steel-hi": s["light"],
        "--pf-cloud": s["light"],
    }
    return {"name": raw.get("name"), "tokens": tokens}


def load_theme(name):
    path = ROOT / "themes" / f"{name}.json"
    return expand_theme(json.loads(path.read_text()))


DEFAULTS_PATH = ROOT / "banners" / "_defaults.json"


def _merge(base, override):
    out = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(out.get(key), dict):
            out[key] = _merge(out[key], value)
        else:
            out[key] = value
    return out


def load_config(path):
    """A banner config merged over the shared banners/_defaults.json, so
    common settings (theme, animation, geometry) are central."""
    config = json.loads(Path(path).read_text())
    defaults = (
        json.loads(DEFAULTS_PATH.read_text()) if DEFAULTS_PATH.exists() else {}
    )
    return _merge(defaults, config)


def _badge_cache():
    path = ROOT / "tools" / "badges_cache.json"
    return json.loads(path.read_text()) if path.exists() else {}


def _stats_cache():
    path = ROOT / "tools" / "stats_cache.json"
    return json.loads(path.read_text()) if path.exists() else {}


def _contrib_cache():
    path = ROOT / "tools" / "contrib_cache.json"
    return json.loads(path.read_text()) if path.exists() else {}


SKY_BAR_W = 0.9
SKY_OFF = 0.05


def _layout_skyline(cfg, tokens, width, height):
    """Contribution Skyline: an isometric grid of bars, coloured by the
    theme, painter-sorted. Returns (parts, css)."""
    cache = _contrib_cache()
    days = cache.get("days", [])
    end = cache.get("end")
    if not days or not end:
        return [], ""
    grid = _skyline.build_grid(days, end, cfg.get("week_start", 0))
    cells = grid["cells"]
    big = grid["max"]
    hs = cfg.get("height_scale", 1)
    cam = _skyline.camera(1.0)
    w, off = SKY_BAR_W, SKY_OFF

    hgt = [_skyline.bar_height(c["count"], big, hs) for c in cells]
    xs, ys = [], []

    def add(x, y, z):
        px, py = _skyline.project(cam, x, y, z)
        xs.append(px)
        ys.append(py)

    for i, c in enumerate(cells):
        x0, y0, z = c["week"] + off, c["day"] + off, hgt[i]
        x1, y1 = x0 + w, y0 + w
        add(x0, y0, z); add(x1, y0, z); add(x1, y1, z); add(x0, y1, z)
        add(x0, y0, 0); add(x1, y0, 0); add(x1, y1, 0); add(x0, y1, 0)
    minx, maxx, miny, maxy = min(xs), max(xs), min(ys), max(ys)
    bw, bh = max(1e-6, maxx - minx), max(1e-6, maxy - miny)

    ix, iy = 8, 8
    iw, ih = width - 16, height - 16
    s = min(iw / bw, ih / bh)
    ox = ix + (iw - bw * s) / 2 - minx * s
    oy = iy + (ih - bh * s) / 2 - miny * s
    px = lambda x, y: ox + (x * cam["cs"] - y * cam["sn"]) * s
    py = lambda x, y, z: oy + ((x * cam["sn"] + y * cam["cs"]) * cam["se"] - z * cam["ce"]) * s

    levels = cfg.get("levels", ["pf-primary-hi", "pf-tertiary", "pf-secondary", "pf-primary"])
    empty = cfg.get("empty", "pf-frame-inner")

    def hexof(cls):
        return tokens.get("--" + cls, "#888888")

    level_cols = [hexof(c) for c in levels]
    empty_col = hexof(empty)

    order = sorted(
        range(len(cells)),
        key=lambda i: (cells[i]["week"] + 0.5) * cam["sn"] + (cells[i]["day"] + 0.5) * cam["cs"],
    )
    rise = cfg.get("rise", True)
    step = cfg.get("rise_step", 0.02)
    parts = []
    for k in order:
        c = cells[k]
        x0, y0 = c["week"] + off, c["day"] + off
        x1, y1, z = x0 + w, y0 + w, hgt[k]
        lvl = c["level"]
        base = level_cols[lvl - 1] if lvl > 0 else empty_col
        top, left, right = base, _skyline.shade(base, 0.84), _skyline.shade(base, 0.68)
        tall = z * cam["ce"] * s
        f = 0
        if tall > 0.35 and w * cam["cs"] * s > 0.35:
            f |= 1
        if tall > 0.35 and w * cam["sn"] * s > 0.35:
            f |= 2
        polys = []
        if f & 1:
            polys.append([(px(x0, y1), py(x0, y1, 0)), (px(x1, y1), py(x1, y1, 0)),
                          (px(x1, y1), py(x1, y1, z)), (px(x0, y1), py(x0, y1, z))])
        if f & 2:
            polys.append([(px(x1, y0), py(x1, y0, 0)), (px(x1, y1), py(x1, y1, 0)),
                          (px(x1, y1), py(x1, y1, z)), (px(x1, y0), py(x1, y0, z))])
        polys.append([(px(x0, y0), py(x0, y0, z)), (px(x1, y0), py(x1, y0, z)),
                      (px(x1, y1), py(x1, y1, z)), (px(x0, y1), py(x0, y1, z))])
        colors = [left, right, top] if (f & 1) else [right, top] if (f & 2) else [top]
        # keep face colours aligned with the polygon order above
        face_colors = []
        if f & 1:
            face_colors.append(left)
        if f & 2:
            face_colors.append(right)
        face_colors.append(top)
        body = "\n".join(
            f'        <polygon points="{" ".join(f"{a:.2f},{b:.2f}" for a, b in poly)}" fill="{col}"/>'
            for poly, col in zip(polys, face_colors)
        )
        bx = px((x0 + x1) / 2, (y0 + y1) / 2)
        by = py((x0 + x1) / 2, (y0 + y1) / 2, 0)
        style = f"transform-origin:{bx:.1f}px {by:.1f}px"
        if rise:
            style += f";animation-delay:{(c['week'] * step):.3f}s"
        parts.append(f'    <g class="pf-bar" style="{style}">\n{body}\n    </g>')

    css = ""
    if rise:
        css = (
            "    .pf-bar { animation: pf-bar-rise 24s ease-in-out infinite both; }\n"
            "    @keyframes pf-bar-rise {\n"
            "      0%     { transform: scaleY(0.03); opacity: 0.25; }\n"
            "      8.33%  { transform: scaleY(1); opacity: 1; }\n"
            "      91.67% { transform: scaleY(1); opacity: 1; }\n"
            "      100%   { transform: scaleY(0.03); opacity: 0.25; }\n"
            "    }"
        )
    return parts, css


def _box(x, y, w, h, face="pf-tile-face", face_cls="", border=4, cell=4,
         chase=False, border_color="pf-secondary"):
    """Box: a single thick border around a face fill. With chase=on the border
    is drawn as cell-sized segments whose opacity phase runs around the
    perimeter (marching / alternating on-off); the face stays static."""
    face_class = f"{face} {face_cls}".strip()
    if border <= 0:
        return f'    <rect class="{face_class}" x="{x}" y="{y}" width="{w}" height="{h}"/>'
    face_rect = (
        f'    <rect class="{face_class}" x="{x + border}" y="{y + border}" '
        f'width="{w - 2 * border}" height="{h - 2 * border}"/>'
    )
    if not chase:
        return (
            f'    <rect class="{border_color}" x="{x}" y="{y}" '
            f'width="{w}" height="{h}"/>\n'
            + face_rect
        )

    segs = []

    def run(sx, sy, length, horizontal, reverse=False):
        pos = 0
        while pos < length:
            seg = min(cell, length - pos)
            if horizontal:
                off = (length - pos - seg) if reverse else pos
                segs.append((sx + off, sy, seg, border))
            else:
                off = (length - pos - seg) if reverse else pos
                segs.append((sx, sy + off, border, seg))
            pos += seg

    # clockwise: top L->R (incl. corners), right T->B, bottom R->L, left B->T
    run(x, y, w, True)
    run(x + w - border, y + border, h - 2 * border, False)
    run(x, y + h - border, w, True, reverse=True)
    run(x, y + border, h - 2 * border, False, reverse=True)

    parts = [face_rect]
    for i, (sx, sy, sw, sh) in enumerate(segs):
        parts.append(
            f'    <rect class="{border_color} pf-chase pf-chase-{i % CHASE_STEPS}" '
            f'x="{sx}" y="{sy}" width="{sw}" height="{sh}"/>'
        )
    return "\n".join(parts)


def _layout_panels(cfg, width, start_y):
    """Subheaded stat sections. Each section pulls items from the stats cache
    via "source" (overall/streaks/languages) or takes explicit "items", and
    lays them out in N columns. With "box": true each item sits in a 4-ring
    pixel box.

    Sections flow left-to-right into rows by their "span" (fraction of the
    available width, default 1.0): e.g. a 0.42 section and a 0.58 section sit
    side by side, and the next full-width section drops to a new row.
    """
    cache = _stats_cache()
    ox = cfg.get("origin_x", 28)
    right = width - ox
    avail = right - ox
    gap = cfg.get("gap", 26)
    sec_gap = cfg.get("section_gap", 28)
    col_gap = cfg.get("col_gap", 28)
    title_size = cfg.get("title_size", 14)
    item_size = cfg.get("item_size", 13)
    row_h = cfg.get("row_h", 22)
    pad = cfg.get("pad", 12)
    value_size = cfg.get("value_size", 20)
    box_gap = cfg.get("box_gap", 10)
    radius = cfg.get("radius", 0)

    metas = []
    for sec in cfg.get("sections", []):
        items = sec.get("items") or cache.get(sec.get("source", ""), [])
        if not items:
            continue
        cols = max(1, sec.get("columns", 1))
        nrows = (len(items) + cols - 1) // cols
        has_sub = any(i.get("sub") for i in items)
        boxed = bool(sec.get("box"))
        rh = row_h + (12 if has_sub else 0)
        sub_gap = 16
        if boxed:
            box_h = pad + item_size + 4 + value_size + (sub_gap if has_sub else 0) + pad
            content_h = nrows * box_h + (nrows - 1) * box_gap
        else:
            box_h = 0
            content_h = nrows * rh
        header = (title_size + 6 + 12) if sec.get("title", "") else 0
        metas.append({
            "sec": sec, "items": items, "cols": cols, "nrows": nrows,
            "has_sub": has_sub, "boxed": boxed, "rh": rh, "box_h": box_h,
            "sub_gap": sub_gap, "block_h": pad + header + content_h + pad,
            "span": max(0.01, float(sec.get("span", 1.0))),
        })

    groups, cur, cur_span = [], [], 0.0
    for m in metas:
        if cur and cur_span + m["span"] > 1.0001:
            groups.append(cur)
            cur, cur_span = [], 0.0
        cur.append(m)
        cur_span += m["span"]
    if cur:
        groups.append(cur)

    parts = []
    y = start_y
    for group in groups:
        total_span = sum(m["span"] for m in group)
        k = len(group)
        widths = [(avail - (k - 1) * sec_gap) * m["span"] / total_span for m in group]
        row_block_h = max(m["block_h"] for m in group)
        x = ox
        for m, w in zip(group, widths):
            x0, x1 = x, x + w
            sec, items = m["sec"], m["items"]
            cx0, cx1 = x0 + pad, x1 - pad
            bg = sec.get("bg")
            if bg:
                if sec.get("card_anim") == "chase":
                    parts.append(_box(
                        x0, y, w, row_block_h, bg,
                        border=sec.get("border_w", 4),
                        border_color=sec.get("border", "pf-secondary"),
                        cell=2, chase=True,
                    ))
                else:
                    parts.append(
                        f'    <rect class="{bg}" x="{x0}" y="{y}" '
                        f'width="{w}" height="{row_block_h}" rx="{radius}"/>'
                    )
            cy = y + pad
            title = sec.get("title", "")
            if title:
                parts.append(_text({
                    "x": cx0, "y": cy + title_size, "size": title_size,
                    "weight": 700, "letter_spacing": 1, "text": title,
                }))
                cy += title_size + 6
                parts.append(
                    f'    <rect class="pf-ink" x="{cx0}" y="{cy}" '
                    f'width="{cx1 - cx0}" height="1"/>'
                )
                cy += 12
            colw = (cx1 - cx0 - (m["cols"] - 1) * col_gap) / m["cols"]
            for i, item in enumerate(items):
                c, r = divmod(i, m["nrows"])
                ix = cx0 + c * (colw + col_gap)
                value = str(item["value"]) + (" " + item["unit"] if item.get("unit") else "")
                if m["boxed"]:
                    iy = cy + r * (m["box_h"] + box_gap)
                    face = item.get("face", sec.get("face", "pf-tertiary"))
                    parts.append(_box(
                        ix, iy, colw, m["box_h"], face, "",
                        border=sec.get("box_border_w", 0),
                        cell=2, chase=sec.get("box_anim") == "chase",
                    ))
                    cxm = ix + colw / 2
                    ly = iy + pad + item_size
                    parts.append(_text({"x": cxm, "y": ly, "size": item_size, "color": "pf-box-ink", "anchor": "middle", "text": item["label"]}))
                    vy = ly + 4 + value_size
                    parts.append(_text({"x": cxm, "y": vy, "size": value_size, "weight": 700, "color": "pf-box-ink", "anchor": "middle", "text": value}))
                    if item.get("sub"):
                        parts.append(_text({"x": cxm, "y": vy + m["sub_gap"], "size": item_size - 3, "color": "pf-box-ink", "anchor": "middle", "text": item["sub"]}))
                else:
                    iy = cy + r * m["rh"] + item_size
                    parts.append(_text({"x": ix, "y": iy, "size": item_size, "color": "pf-ink-muted", "text": item["label"]}))
                    parts.append(_text({"x": ix + colw, "y": iy, "size": item_size, "weight": 700, "color": "pf-ink", "anchor": "end", "text": value}))
                    if item.get("sub"):
                        parts.append(_text({"x": ix, "y": iy + 14, "size": item_size - 2, "color": "pf-ink-muted", "text": item["sub"]}))
            x += w + sec_gap
        y += row_block_h + gap
    return parts, y


def _layout_badges(cfg, cache, width, start_y):
    """Flow shields.io badges (pre-normalized) into wrapped rows under
    section labels. Returns (markup_parts, bottom_y)."""
    bx = cfg.get("origin_x", 24)
    gap = cfg.get("gap", 8)
    row_gap = cfg.get("row_gap", 10)
    section_gap = cfg.get("section_gap", 18)
    label_size = cfg.get("label_size", 13)
    right = width - bx
    parts = []
    y = start_y
    for si, sec in enumerate(cfg.get("sections", [])):
        if si:
            y += section_gap
        parts.append(
            _text(
                {
                    "x": bx,
                    "y": y + label_size,
                    "size": label_size,
                    "weight": 700,
                    "letter_spacing": 1,
                    "text": sec["label"],
                }
            )
        )
        y += label_size + 10
        x = bx
        row_h = 0
        for slug in sec.get("items", []):
            b = cache.get(slug)
            if not b:
                continue
            w, h = b["w"], b["h"]
            if x > bx and x + w > right:
                x = bx
                y += row_h + row_gap
                row_h = 0
            parts.append(f'    <g transform="translate({x},{y})">{b["body"]}</g>')
            x += w + gap
            row_h = max(row_h, h)
        y += row_h
    return parts, y


def _glyph_for(ch):
    key = CHAR_ALIAS.get(ch, ch)
    return _glyphs.GLYPHS.get(key)


def _heading_groups(text, x0, y0, mode="pop"):
    """One <g> per glyph, so each letter can animate on its own. A glyph may
    carry its own cell size and advance (small punctuation); short glyphs are
    baseline-aligned to the 28px cap height."""
    groups = []
    cursor = x0
    for i, ch in enumerate(text):
        glyph = _glyph_for(ch)
        if not glyph:
            cursor += _glyphs.DEFAULT_ADVANCE
            continue
        cell, rows, advance = _glyphs.parts(glyph)
        y_off = GLYPH_ROWS * GLYPH_CELL - len(rows) * cell
        rects = []
        for ry, row in enumerate(rows):
            for cx, mark in enumerate(row):
                if mark == "#":
                    rects.append(
                        f'          <rect x="{cursor + cx * cell}" '
                        f'y="{y0 + y_off + ry * cell}" '
                        f'width="{cell}" height="{cell}"/>'
                    )
        cursor += advance
        if not rects:
            continue
        cls = f"pf-step-{i}" if mode == "step" else f"pf-letter pf-letter-{i}"
        body = "\n".join(rects)
        groups.append(f'      <g class="{cls}">\n{body}\n      </g>')
    return groups


def _heading_advance(text):
    total = 0
    for ch in text:
        glyph = _glyph_for(ch)
        total += _glyphs.parts(glyph)[2] if glyph else _glyphs.DEFAULT_ADVANCE
    return total


def _icon_group(icon_id, x, y, scale):
    icon = _icons.ICONS[icon_id]
    cell, rows = icon["cell"], icon["rows"]
    rects = []
    for ry, row in enumerate(rows):
        for cx, ch in enumerate(row):
            if ch in ". ":
                continue
            rects.append(
                f'        <rect x="{cx * cell}" y="{ry * cell}" '
                f'width="{cell}" height="{cell}" class="{_icons.class_for(icon, ch)}"/>'
            )
    body = "\n".join(rects)
    # Placement transform lives on the outer <g>; the animation (which sets its
    # own transform) lives on the inner <g>, so CSS can't override placement.
    return (
        f'    <g transform="translate({x},{y}) scale({scale})">\n'
        f'      <g class="pf-icon">\n{body}\n      </g>\n'
        f"    </g>"
    )


def _dominant_hex(icon_id):
    """Most common colour of an icon's exact palette (imported icons)."""
    icon = _icons.ICONS.get(icon_id)
    pal = icon.get("palette") if icon else None
    if not pal:
        return None
    counts = {}
    for row in icon["rows"]:
        for ch in row:
            if ch not in ". ":
                counts[ch] = counts.get(ch, 0) + 1
    if not counts:
        return None
    return pal[max(counts, key=counts.get)][1]


def _icon_height(icon_id, scale):
    icon = _icons.ICONS[icon_id]
    return len(icon["rows"]) * icon["cell"] * scale


def _icon_width(icon_id, scale):
    icon = _icons.ICONS[icon_id]
    return len(icon["rows"][0]) * icon["cell"] * scale


def _frame(width, height):
    return (
        f'    <rect class="pf-frame-outer" x="0" y="0" '
        f'width="{width}" height="{height}"/>\n'
        f'    <rect class="pf-frame-mid" x="2" y="2" '
        f'width="{width - 4}" height="{height - 4}"/>\n'
        f'    <rect class="pf-frame-hi" x="2" y="2" width="{width - 4}" height="1"/>\n'
        f'    <rect class="pf-frame-hi" x="2" y="2" width="1" height="{height - 4}"/>\n'
        f'    <rect class="pf-frame-inner" x="6" y="6" '
        f'width="{width - 12}" height="{height - 12}"/>\n'
        f'    <rect class="pf-canvas" x="8" y="8" '
        f'width="{width - 16}" height="{height - 16}"/>'
    )


def _tile(t):
    x, y = t["x"], t["y"]
    w, h = t["width"], t["height"]
    face = t.get("face", "pf-tile-face")
    return (
        f'    <rect class="pf-frame-outer" x="{x}" y="{y}" width="{w}" height="{h}"/>\n'
        f'    <rect class="pf-frame-mid" x="{x + 1}" y="{y + 1}" '
        f'width="{w - 2}" height="{h - 2}"/>\n'
        f'    <rect class="pf-frame-inner" x="{x + 2}" y="{y + 2}" '
        f'width="{w - 4}" height="{h - 4}"/>\n'
        f'    <rect class="{face}" x="{x + 3}" y="{y + 3}" '
        f'width="{w - 6}" height="{h - 6}"/>'
    )


def _text(t):
    x, y = t["x"], t.get("y", 0)
    size = t.get("size", 14)
    color = t.get("color", "pf-ink")
    anchor = t.get("anchor", "start")
    weight = t.get("weight", 500)
    style = t.get("style", "normal")
    letter = t.get("letter_spacing", 0.5)
    text = (
        t["text"]
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )
    return (
        f'    <text class="{color}" x="{x}" y="{y}" '
        f'text-anchor="{anchor}" font-family="ui-monospace, monospace" '
        f'font-size="{size}" font-weight="{weight}" font-style="{style}" '
        f'letter-spacing="{letter}">{text}</text>'
    )


def _step_text(t, base):
    """A text line whose characters each pop in on their own (pf-step-N),
    like the heading. Returns (markup, char_count) so indices stay sequential
    across the heading and every step line."""
    x, y = t["x"], t.get("y", 0)
    size = t.get("size", 14)
    color = t.get("color", "pf-ink")
    anchor = t.get("anchor", "start")
    weight = t.get("weight", 500)
    style = t.get("style", "normal")
    letter = t.get("letter_spacing", 0.5)
    tspans = []
    for i, ch in enumerate(t["text"]):
        ch = "\u00a0" if ch == " " else ch
        ch = ch.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        tspans.append(f'<tspan class="pf-step-{base + i}">{ch}</tspan>')
    return (
        f'    <text class="{color}" x="{x}" y="{y}" '
        f'text-anchor="{anchor}" font-family="ui-monospace, monospace" '
        f'font-size="{size}" font-weight="{weight}" font-style="{style}" '
        f'letter-spacing="{letter}">{"".join(tspans)}</text>'
    ), len(t["text"])


def _wrap_text(text, max_chars):
    """Greedy word-wrap to max_chars per line (monospace)."""
    lines, cur = [], ""
    for word in text.split(" "):
        cand = word if not cur else f"{cur} {word}"
        if not cur or len(cand) <= max_chars:
            cur = cand
        else:
            lines.append(cur)
            cur = word
    if cur or not lines:
        lines.append(cur)
    return lines


def _text_box(cfg, cursor, base_step):
    """Auto-wrapping, auto-height boxed text. Returns (parts, bottom, step_used)."""
    x = cfg.get("x", 28)
    w = cfg["width"]
    pad = cfg.get("pad", 16)
    border = cfg.get("border_w", 4)
    face = cfg.get("face", "pf-tertiary")
    border_color = cfg.get("border", "pf-secondary")
    size = cfg.get("size", 18)
    color = cfg.get("color", "pf-ink")
    align = cfg.get("align", "center")
    line_h = cfg.get("line_h", 1.4)
    step = bool(cfg.get("step"))
    text = cfg.get("text", "")

    content_w = w - 2 * border - 2 * pad
    max_chars = max(1, int(content_w / (size * 0.6)))
    lines = _wrap_text(text, max_chars)
    lh = size * line_h
    box_h = 2 * border + 2 * pad + len(lines) * lh
    y = cfg.get("y")
    if y is None:
        y = cursor

    anchor = "middle" if align == "center" else "start"
    tx = x + w / 2 if align == "center" else x + border + pad
    parts = [_box(x, y, w, box_h, face, border=border, border_color=border_color)]
    used = 0
    for j, line in enumerate(lines):
        t = {
            "x": tx, "y": y + border + pad + size + j * lh,
            "size": size, "color": color, "anchor": anchor, "text": line,
        }
        if step:
            markup, count = _step_text(t, base_step + used)
            used += count
            parts.append(markup)
        else:
            parts.append(_text(t))
    return parts, y + box_h, used


def _stripes(cfg, width, height, frame=True):
    """Pixel-grid diagonal color stripes scrolling top-left -> bottom-right,
    clipped to the canvas. Bands are staircases of `cell`-sized blocks (a
    function of col+row), so the edges stay blocky. Returns (defs, group, css)."""
    cell = cfg.get("cell", 4)
    stripe = cfg.get("width", 24)
    band = max(1, round(stripe / cell))       # blocks per band along an axis
    colors = cfg.get("colors", ["pf-primary", "pf-secondary", "pf-tertiary"])
    n = len(colors)
    speed = cfg.get("speed", 6)
    period = n * band * cell                  # seamless translate distance
    inset = 8 if frame else 0

    bars = []
    y = 0
    while y < height:
        x = -period
        while x < width:
            d = x // cell + y // cell
            idx = (d // band) % n
            run = (band - d % band) * cell
            bars.append(
                f'        <rect class="{colors[idx]}" x="{x}" y="{y}" '
                f'width="{min(run, width - x)}" height="{cell}"/>'
            )
            x += run
        y += cell

    defs = (
        f'  <defs>\n    <clipPath id="pf-stripe-clip">\n'
        f'      <rect x="{inset}" y="{inset}" width="{width - 2 * inset}" '
        f'height="{height - 2 * inset}"/>\n    </clipPath>\n  </defs>'
    )
    group = (
        f'    <g clip-path="url(#pf-stripe-clip)">\n'
        f'      <g class="pf-stripes" shape-rendering="crispEdges">\n'
        + "\n".join(bars)
        + "\n      </g>\n    </g>"
    )
    css = (
        f"    .pf-stripes {{ animation: pf-stripes {speed}s linear infinite; }}\n"
        "    @keyframes pf-stripes {\n"
        "      from { transform: translateX(0); }\n"
        f"      to   {{ transform: translateX({period}px); }}\n    }}"
    )
    return defs, group, css


def _style_block(tokens, underline_x, heading="", anim=None, n_lines=0,
                 box_chase=False, step_count=None, stripes_css="", skyline_css=""):
    anim = anim or {}
    n = step_count if step_count is not None else len(heading)
    inline = "".join(f"{k}: {v};" for k, v in tokens.items())
    root = " ".join(f"{k}: {v};" for k, v in tokens.items())
    classes = "\n".join(
        f"    .{k[2:]} {{ fill: var(--{k[2:]}); }}"
        for k in tokens
    )

    def build_line_block(dur):
        if not n_lines:
            return ""
        css = "\n".join(
            f"    .pf-line-{i} {{ animation-delay: calc({dur} * {i} * 0.03); }}"
            for i in range(n_lines)
        )
        return (
            f"    .pf-line {{ animation: pf-line-in {dur} ease-out infinite both; }}\n"
            + css
            +             "\n    @keyframes pf-line-in {\n"
            "      0%   { opacity: 0; transform: translateY(-8px); }\n"
            "      8%   { opacity: 1; transform: translateY(0); }\n"
            "      88%  { opacity: 1; transform: translateY(0); }\n"
            "      100% { opacity: 0; transform: translateY(0); }\n"
            "    }"
        )

    def build_chase_block():
        if not box_chase:
            return ""
        d = f"{CHASE_DURATION}s"
        delays = "\n".join(
            f"    .pf-chase-{k} {{ animation-delay: calc({d} * {-k} / {CHASE_STEPS}); }}"
            for k in range(CHASE_STEPS)
        )
        off = CHASE_OFF_FRACTION * 100
        return (
            f"    .pf-chase {{ animation: pf-chase {d} linear infinite; }}\n"
            + delays
            + "\n    @keyframes pf-chase {\n"
            f"      0%, {off:.3f}% {{ opacity: 0; }}\n"
            f"      {off + 0.001:.3f}%, 100% {{ opacity: 1; }}\n"
            "    }"
        )

    chase_block = build_chase_block()

    appear = max(0.001, float(anim.get("appear", 0.2)))
    disappear = max(0.001, float(anim.get("disappear", appear)))
    hold = max(0.0, float(anim.get("hold", 5.0)))
    forward = n * appear
    reverse = n * disappear
    total = max(0.001, forward + hold + reverse)

    def pct(t):
        return t / total * 100.0

    letter_css, kfs = [], []
    for i in range(n):
        a = i * appear
        d = forward + hold + (n - 1 - i) * disappear
        pa, pd = pct(a), pct(d)
        letter_css.append(
            f"    .pf-step-{i} {{ animation: pf-step-{i} {total:.3f}s steps(1, end) infinite; }}"
        )
        kfs.append(
            f"""    @keyframes pf-step-{i} {{
      0%, {pa:.4f}% {{ opacity: 0; }}
      {pa + 0.001:.4f}%, {pd:.4f}% {{ opacity: 1; }}
      {pd + 0.001:.4f}%, 100% {{ opacity: 0; }}
    }}"""
        )
    # the underline wipes in with the heading letters only, not step lines
    head_forward = max(0.001, len(heading) * appear)
    pf, ph = pct(head_forward), pct(forward + hold)
    underline = (
        f"    .pf-underline {{ animation: pf-wipe-cycle {total:.3f}s ease-in-out infinite; "
        f"transform-origin: {underline_x}px center; }}"
    )
    wipe = f"""    @keyframes pf-wipe-cycle {{
      0% {{ transform: scaleX(0); }}
      {pf:.4f}% {{ transform: scaleX(1); }}
      {ph:.4f}% {{ transform: scaleX(1); }}
      100% {{ transform: scaleX(0); }}
    }}"""
    line_block = build_line_block(f"{total:.3f}s")
    return inline, f"""  <style>
    :root {{ {root} }}

{classes}

    .pf-tile {{ animation: none; }}
    .pf-icon {{ animation: none; }}
{underline}
{chr(10).join(letter_css)}
{line_block}
{chase_block}
{stripes_css}
{skyline_css}

{wipe}
{chr(10).join(kfs)}
  </style>"""


def render(config, theme):
    tokens = theme["tokens"]
    anim = config.get("animation", {})
    if isinstance(anim, str):
        anim = {"mode": anim}
    mode = anim.get("mode", "pop")
    width = config.get("width", 800)
    hx = config.get("heading_x", 36)
    hy = config.get("heading_y", 32)
    margin = config.get("margin", 16)
    heading = config.get("heading", "")
    hscale = config.get("heading_scale", 1)
    boxes_cfg = config.get("boxes", [])
    stripes_cfg = config.get("stripes")
    stripes_css = ""

    underline_cfg = config.get("underline", True)
    underline_on = underline_cfg is not False
    uy = hy + round(GLYPH_ROWS * GLYPH_CELL * hscale) + 8
    u_w = (_heading_advance(heading) - 4) * hscale + 8
    if isinstance(underline_cfg, dict) and "width" in underline_cfg:
        u_w = underline_cfg["width"]

    # --- vertical cursor for auto-placed content ---
    cursor = uy + 3 + 18
    textbox_parts, textbox_bottom = [], None
    step_total = len(heading)
    tb_cfg = config.get("text_box")
    if tb_cfg:
        textbox_parts, textbox_bottom, used = _text_box(tb_cfg, cursor, step_total)
        step_total += used
        cursor = max(cursor, textbox_bottom + 16)
    lines = []
    bullet_data = []
    raw_lines = config.get("lines", [])
    line_step = config.get("line_step")
    bullet_w = max(
        [
            _icon_width(ln["bullet"]["id"], ln["bullet"].get("scale", 1))
            for ln in raw_lines
            if ln.get("bullet")
        ]
        or [0]
    )
    for ln in raw_lines:
        size = ln.get("size", 14)
        lx = ln.get("x", hx)
        y = ln.get("y")
        if y is None:
            y = cursor + size
        out = {**ln, "y": y, "x": lx}
        if ln.get("bullet"):
            bid = ln["bullet"]["id"]
            bscale = ln["bullet"].get("scale", 1)
            ih = _icon_height(bid, bscale)
            bullet_data.append((bid, lx, y - round(size * 0.35) - ih // 2, bscale))
            out["x"] = lx + bullet_w + 10
        if line_step:
            cursor = y + line_step - size
        else:
            cursor = max(cursor, y + size * 0.3 + 6)
        lines.append(out)

    tiles_cfg = []
    for t in config.get("tiles", []):
        y = t.get("y")
        if y is None:
            y = cursor + 10
        cursor = max(cursor, y + t["height"] + 10)
        tiles_cfg.append({**t, "y": y})

    # Icons: an omitted / "center" y vertically centres within the banner.
    # x is the left offset; "right" is padding from the banner's right edge.
    icons_cfg = []
    theme_name = theme.get("name")
    for ic in config.get("icons", []):
        icon_id = ic.get("id")
        if "by_theme" in ic:                       # per-theme override
            icon_id = ic["by_theme"].get(theme_name, ic.get("id"))
        if not icon_id:
            continue
        scale = ic.get("scale", 1)
        y = ic.get("y")
        centered = y is None or (isinstance(y, str) and y in ("center", "middle", "auto"))
        if "center_x" in ic:
            x = int(ic["center_x"]) - _icon_width(icon_id, scale) // 2
        elif "right" in ic:
            x = width - int(ic["right"]) - _icon_width(icon_id, scale)
        else:
            x = int(ic["x"])
        icons_cfg.append(
            {
                "id": icon_id,
                "x": x,
                "scale": scale,
                "y": None if centered else int(y),
                "_centered": centered,
            }
        )

    # Per-box face picked to contrast an icon (boxes[].face_contrast), and a
    # matching high-contrast colour for the heading/underline.
    box_faces = {}
    heading_color = config.get("heading_color", "pf-ink")
    mains = {
        k: tokens.get("--" + k)
        for k in ("pf-primary", "pf-secondary", "pf-tertiary")
        if tokens.get("--" + k)
    }
    light = {
        k: tokens.get("--" + k)
        for k in ("pf-primary-hi", "pf-secondary-hi", "pf-tertiary-hi")
        if tokens.get("--" + k)
    }
    for bi, b in enumerate(boxes_cfg):
        fc = b.get("face_contrast")
        icon_id = (
            (icons_cfg[0]["id"] if icons_cfg else None) if fc is True
            else (fc if isinstance(fc, str) else None)
        )
        dom = _dominant_hex(icon_id) if icon_id else None
        if not dom or not light:
            continue
        box_faces[bi] = max(light, key=lambda k: _contrast(dom, light[k]))
    if box_faces and mains:
        face_hex = tokens.get("--" + next(iter(box_faces.values())))
        if face_hex:
            heading_color = max(mains, key=lambda k: _contrast(face_hex, mains[k]))

    # Badges (shields.io, pre-normalized to inline markup).
    badges_cfg = config.get("badges")
    badge_parts, badge_bottom = [], cursor
    if badges_cfg:
        badge_parts, badge_bottom = _layout_badges(
            badges_cfg, _badge_cache(), width, badges_cfg.get("origin_y", cursor)
        )

    # Panels (subheaded stat sections from the stats cache).
    panels_cfg = config.get("panels")
    panel_parts, panel_bottom = [], badge_bottom
    if panels_cfg:
        start = panels_cfg.get("origin_y", badge_bottom if badges_cfg else cursor)
        panel_parts, panel_bottom = _layout_panels(panels_cfg, width, start)

    # --- height ---
    if config.get("height", "auto") == "auto":
        bottom = uy + 3
        for ln in lines:
            bottom = max(bottom, ln["y"] + ln.get("size", 14) * 0.3)
        for bid, _bx, _by, bsc in bullet_data:
            bottom = max(bottom, _by + _icon_height(bid, bsc))
        for t in tiles_cfg:
            bottom = max(bottom, t["y"] + t["height"])
        for b in boxes_cfg:
            bottom = max(bottom, b["y"] + b["height"])
        if textbox_bottom is not None:
            bottom = max(bottom, textbox_bottom)
        center_h = max(
            [_icon_height(ic["id"], ic["scale"]) for ic in icons_cfg if ic["_centered"]]
            or [0]
        )
        for ic in icons_cfg:
            if not ic["_centered"]:
                bottom = max(bottom, ic["y"] + _icon_height(ic["id"], ic["scale"]))
        height = int(
            max(
                100,
                bottom + margin,
                center_h + 2 * margin,
                badge_bottom + margin,
                panel_bottom + margin,
            )
        )
    else:
        height = int(config["height"])

    # resolve vertically-centred icons now that height is known
    for ic in icons_cfg:
        if ic["_centered"]:
            ic["y"] = round((height - _icon_height(ic["id"], ic["scale"])) / 2)

    # --- assemble ---
    parts = []
    if stripes_cfg:
        stripe_defs, stripe_group, stripes_css = _stripes(
            stripes_cfg, width, height, config.get("frame", True)
        )
        parts.append(stripe_defs)
    if config.get("frame", True):
        parts.append(_frame(width, height))
    if stripes_cfg:
        parts.append(stripe_group)
    for bi, b in enumerate(boxes_cfg):
        parts.append(_box(
            b["x"], b["y"], b["width"], b["height"],
            box_faces.get(bi, b.get("face", "pf-tile-face")),
            border=b.get("border_w", 4),
            border_color=b.get("border", "pf-secondary"),
        ))
    parts.extend(textbox_parts)

    if heading:
        groups = "\n".join(_heading_groups(heading, hx, hy, mode))
        scale = ""
        if hscale != 1:
            scale = (
                f' transform="translate({hx} {hy}) scale({hscale}) '
                f'translate({-hx} {-hy})" shape-rendering="crispEdges"'
            )
        parts.append(f'    <g class="{heading_color}"{scale}>\n{groups}\n    </g>')

    for ic in icons_cfg:
        parts.append(
            _icon_group(ic["id"], ic["x"], ic["y"], ic.get("scale", 1))
        )

    if underline_on:
        parts.append(
            f'    <g class="pf-underline">\n'
            f'      <rect class="{heading_color}" x="{hx}" y="{uy}" '
            f'width="{u_w}" height="3"/>\n'
            f"    </g>"
        )

    for bid, bxp, byp, bsc in bullet_data:
        parts.append(_icon_group(bid, bxp, byp, bsc))

    for i, ln in enumerate(lines):
        if ln.get("step"):
            markup, count = _step_text(ln, step_total)
            step_total += count
            parts.append(markup)
        else:
            parts.append(f'    <g class="pf-line pf-line-{i}">\n{_text(ln)}\n    </g>')

    for t in tiles_cfg:
        tile_g = [_tile(t)]
        if "icon" in t:
            ic = t["icon"]
            tile_g.append(
                _icon_group(ic["id"], ic["x"], ic["y"], ic.get("scale", 1))
            )
        if "label" in t:
            lab = t["label"]
            label = {
                "x": lab.get("x", t["x"] + t["width"] // 2),
                "y": lab.get("y", t["y"] + t["height"] // 2 + lab.get("size", 15) // 2),
                "anchor": lab.get("anchor", "middle"),
                "size": lab.get("size", 15),
                "color": lab.get("color", "pf-ink"),
                "weight": lab.get("weight", 700),
                **{k: v for k, v in lab.items() if k in ("style", "letter_spacing")},
                "text": lab["text"],
            }
            tile_g.append(_text(label))
        parts.append('    <g class="pf-tile">\n' + "\n".join(tile_g) + "\n    </g>")

    parts.extend(badge_parts)
    parts.extend(panel_parts)

    skyline_cfg = config.get("skyline")
    skyline_css = ""
    if skyline_cfg:
        skyline_parts, skyline_css = _layout_skyline(
            skyline_cfg, tokens, width, height
        )
        parts.extend(skyline_parts)

    # merge local palettes of every imported icon used (placed, tiled, bulleted)
    # so their token/class definitions exist. Key by class, not by char, so
    # multiple imported icons don't collide.
    local = {}

    def _collect(icon_id):
        for cls, hexv in _icons.ICONS[icon_id].get("palette", {}).values():
            local[cls] = hexv

    for ic in icons_cfg:
        _collect(ic["id"])
    for t in tiles_cfg:
        if "icon" in t:
            _collect(t["icon"]["id"])
    for bid, _bx, _by, _bs in bullet_data:
        _collect(bid)
    tokens = dict(tokens)
    for cls, hexv in local.items():
        tokens[f"--{cls}"] = hexv

    body = "\n\n".join(parts)
    box_chase = bool(panels_cfg) and any(
        s.get("box_anim") == "chase" or s.get("card_anim") == "chase"
        for s in panels_cfg.get("sections", [])
    )
    inline_style, style_block = _style_block(
        tokens, hx, heading, anim, len(lines), box_chase,
        step_count=step_total if mode == "step" else None,
        stripes_css=stripes_css,
        skyline_css=skyline_css,
    )
    markers = []
    if badges_cfg:
        markers.append("badges")
    if skyline_cfg:
        markers.append("skyline")
    marker = f' data-allow-raw-hex="{" ".join(markers)}"' if markers else ""
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{width}" height="{height}" viewBox="0 0 {width} {height}"{marker}\n'
        f'     style="{inline_style}">\n'
        f"{style_block}\n\n"
        f"{body}\n"
        f"</svg>\n"
    )
