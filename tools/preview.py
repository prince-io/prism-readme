#!/usr/bin/env python3
"""Generate preview.html for quick local lookup.

Blocks:
  1. README layout: one of each section banner stacked in profile order
  2. every theme sample banner (`assets/theme-preview-*.svg`)
  3. the section banners (`banners/*.json`) rendered in one fixed theme
  4. header and skyline rendered per theme

Section banners are rendered here (and embedded as data URIs) so the page is
self-contained and every section uses the same theme.

    python3 tools/preview.py && xdg-open preview.html    # Linux
    python3 tools/preview.py && open preview.html        # macOS

This is a local convenience page only; GitHub renders the SVGs directly.
"""

import base64
import glob
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))

import banner  # noqa: E402

FIXED_THEME = "light"

# Section banners shown first, in this order.
SECTION_ORDER = [
    "header", "about", "focus-areas", "tech-stack", "github-stats",
    "skyline", "thanks",
]


def main():
    theme_svgs = sorted(
        str(Path(p).relative_to(ROOT))
        for p in glob.glob(str(ROOT / "assets" / "theme-preview-*.svg"))
    )
    theme_cards = "\n".join(
        f'<figure><img src="{p}" alt="{p}"><figcaption>{p}</figcaption></figure>'
        for p in theme_svgs
    )

    theme = banner.load_theme(FIXED_THEME)
    names = [
        Path(p).stem
        for p in glob.glob(str(ROOT / "banners" / "*.json"))
        if not Path(p).stem.startswith("_") and Path(p).stem != "theme-preview"
    ]
    order = [n for n in SECTION_ORDER if n in names]

    rendered = {}
    for name in order:
        config = banner.load_config(ROOT / "banners" / f"{name}.json")
        svg = banner.render(config, theme)
        rendered[name] = "data:image/svg+xml;base64," + base64.b64encode(
            svg.encode("utf-8")
        ).decode("ascii")
    section_cards = [
        f'<figure><img src="{rendered[name]}" alt="{name}">'
        f"<figcaption>{name} &mdash; theme: {FIXED_THEME}</figcaption>"
        "</figure>"
        for name in order
    ]

    # README layout: one of each banner, stacked in profile order.
    readme_parts = []
    for name in order:
        readme_parts.append(f'<img src="{rendered[name]}" alt="{name}">')
        if name == "about":
            gif_rel = f"gifs/{FIXED_THEME}.gif"
            if (ROOT / gif_rel).exists():
                readme_parts.append(
                    f'<img class="gif" src="{gif_rel}" alt="theme gif">'
                )
    readme_stack = "\n".join(readme_parts)

    theme_names = banner.load_config(
        ROOT / "banners" / "theme-preview.json"
    ).get("variants", [])
    header_cfg = banner.load_config(ROOT / "banners" / "header.json")
    header_cards = []
    for tname in theme_names:
        svg = banner.render(header_cfg, banner.load_theme(tname))
        b64 = base64.b64encode(svg.encode("utf-8")).decode("ascii")
        header_cards.append(
            f'<figure><img src="data:image/svg+xml;base64,{b64}" '
            f'alt="header {tname}"><figcaption>header &mdash; {tname}'
            "</figcaption></figure>"
        )

    skyline_cfg = banner.load_config(ROOT / "banners" / "skyline.json")
    skyline_cards = []
    for tname in theme_names:
        svg = banner.render(skyline_cfg, banner.load_theme(tname))
        b64 = base64.b64encode(svg.encode("utf-8")).decode("ascii")
        skyline_cards.append(
            f'<figure><img src="data:image/svg+xml;base64,{b64}" '
            f'alt="skyline {tname}"><figcaption>skyline &mdash; {tname}'
            "</figcaption></figure>"
        )

    html = f"""<!doctype html>
<html><head><meta charset="utf-8"><title>banner preview</title>
<style>
  body {{ margin:0; padding:24px; background:#c9c9c9;
         font:13px ui-monospace, monospace; }}
  h1 {{ font-size:16px; margin:0 0 4px; }}
  h2 {{ font-size:14px; margin:28px 0 10px; border-top:2px solid #888;
        padding-top:12px; }}
  figure {{ margin:0 0 22px; }}
  img {{ width:800px; max-width:100%; display:block;
        image-rendering:pixelated;
        background:
          repeating-conic-gradient(#dcdcdc 0% 25%, #cfcfcf 0% 50%) 50% / 20px 20px; }}
  figcaption {{ color:#333; padding:4px 0; }}
  .readme {{ width:800px; max-width:100%; margin:0 auto 12px;
             background:#fff; padding:16px 0; box-shadow:0 0 0 1px #999; }}
  .readme img {{ width:100%; display:block; image-rendering:pixelated;
                 margin:0 0 16px; }}
  .readme img:last-child {{ margin-bottom:0; }}
  .readme img.gif {{ margin:4px 0 16px; }}
</style></head>
<body>
<h1>banner preview</h1>
<h2>readme layout &mdash; one of each (theme: {FIXED_THEME})</h2>
<div class="readme">
{readme_stack}
</div>
<h2>theme samples &mdash; {len(theme_svgs)}</h2>
{theme_cards}
<h2>section banners &mdash; {len(section_cards)} (theme: {FIXED_THEME})</h2>
{chr(10).join(section_cards)}
<h2>header by theme &mdash; {len(header_cards)}</h2>
{chr(10).join(header_cards)}
<h2>skyline by theme &mdash; {len(skyline_cards)}</h2>
{chr(10).join(skyline_cards)}
</body></html>
"""
    out = ROOT / "preview.html"
    out.write_text(html)
    print(f"wrote {out.relative_to(ROOT)} ({len(theme_svgs)} theme + {len(section_cards)} section)")


if __name__ == "__main__":
    main()
