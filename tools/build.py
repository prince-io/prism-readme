#!/usr/bin/env python3
"""Render every banners/*.json into assets/*.svg.

    python3 tools/build.py            # build all configs
    python3 tools/build.py about      # build one by name

Inline output mode: glyphs and icons are flattened to rects.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))

import banner  # noqa: E402


def build_one(cfg_path):
    config = banner.load_config(cfg_path)
    variants = config.get("variants") or [config.get("theme", "light")]
    base = ROOT / config["output"]
    written = []
    for theme_name in variants:
        theme = banner.load_theme(theme_name)
        svg = banner.render(config, theme)
        if len(variants) == 1:
            out = base.with_suffix(".svg")
        else:
            out = base.parent / f"{base.name}-{theme_name}.svg"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(svg)
        written.append(out)
    return written


def main():
    only = sys.argv[1] if len(sys.argv) > 1 else None
    configs = [c for c in sorted((ROOT / "banners").glob("*.json"))
               if not c.name.startswith("_")]
    if only:
        configs = [c for c in configs if c.stem == only]
    if not configs:
        print("no configs found")
        return
    for cfg in configs:
        written = build_one(cfg)
        rel = ", ".join(str(w.relative_to(ROOT)) for w in written)
        print(f"{cfg.name}: {rel}")


if __name__ == "__main__":
    main()
