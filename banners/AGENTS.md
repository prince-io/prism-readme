# banners/ — banner configs

## Purpose
- One JSON file per banner, rendered by `../tools/build.py` into `../assets/`. `_defaults.json` holds settings shared by all of them.

## Ownership
- `_defaults.json` — central defaults merged under every banner config (theme, variants, geometry, animation, margins).
- Per-banner configs, e.g. `about.json`, `github-stats.json`, `skyline.json`, `tech-stack.json`, `theme-preview.json`.
- The 7 deployable banners (`header, about, focus-areas, tech-stack, github-stats, skyline, thanks`) set all 12 themes and output under `../assets/<name>`; `theme-preview.json` outputs to `../assets/`.

## Local Contracts
- `banner.load_config` deep-merges each config over `_defaults.json`; a config only needs its `name`, `output`, `heading`, and content. Keys present in the config win.
- `_defaults.json` keys: `theme`, `variants`, `width`, `height`, `frame`, `underline`, `animation`, `heading_x`, `heading_y`, `margin`. Engine block keys: `heading*`, `underline`, `animation`, `icons`, `lines`, `tiles`, `badges`, `panels`, `boxes`, `text_box`, `stripes`, `skyline`; implementation details live in `../tools/banner.py`.
- `variants` may be `null` (single file named by `theme`) or a list (emits `<output>-<theme>.svg`). README banners list all 12 themes.
- Reference only glyph letters and icon ids that exist in `../tools/glyphs.py` / `../tools/icons.py`.
- Colors never appear here; select a `theme` preset from `../themes/`.

## Work Guidance
- **Restyle every banner at once** by editing only `_defaults.json` (e.g. change `theme`, `animation`, or `margin`).
- **Edit headings** — `"heading"` (plus `heading_x`/`heading_scale`) uses the pixel font: only `A–Z`, space, `-`, `.`, `,`, `!` exist; any other character is silently skipped. `heading_x` centers it; the underline auto-sizes.
- **Edit body text** — `lines[].text` in `about.json` / `focus-areas.json` uses a normal monospace font (any characters) and does **not** auto-wrap: one entry per line, keep each within the banner width, add/remove entries to change the height. `focus-areas.json` picks each bullet via `bullet.id`.
- **Stack badges** — `tech-stack.json` `badges.sections[]` is `{ "label", "items": [slug] }`; reorder or remove by editing `items`. To add a slug: add its shields.io URL to `../tools/badges.py` `REGISTRY`, run `python3 tools/badges.py cache`, then list the slug. A slug missing from `badges_cache.json` is silently dropped (no error).
- Copy an existing config as a template; keep `output` a path base without extension.
- Files starting with `_` are ignored by `build.py`.
- After any edit, rebuild: `python3 tools/build.py && python3 tools/check.py` (emits all 12 theme variants).

## Verification
- `python3 tools/build.py && python3 tools/check.py`.

## Child DOX Index
- None.
