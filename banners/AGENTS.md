# banners/ — banner configs

## Purpose
- One JSON file per banner, rendered by `../tools/build.py` into `../assets/`. `_defaults.json` holds settings shared by all of them.

## Ownership
- `_defaults.json` — central defaults merged under every banner config (theme, variants, geometry, animation, margins).
- Per-banner configs, e.g. `about.json`, `github-stats.json`, `skyline.json`, `tech-stack.json`, `theme-preview.json`.
- The 7 deployable banners (`header, about, focus-areas, tech-stack, github-stats, skyline, thanks`) set all 13 themes and output under `../assets/<name>`; `theme-preview.json` outputs to `../assets/`.
- These configs are the **shared base for every theme**. The `minecraft` look (textures, sizes, fonts, frames) lives in `../themes/minecraft.json` `by_banner`, never here.

## Local Contracts
- `banner.load_config` deep-merges each config over `_defaults.json`; a config only needs its `name`, `output`, `heading`, and content. Keys present in the config win.
- `_defaults.json` keys: `theme`, `variants`, `width`, `height`, `frame`, `underline`, `animation`, `heading_x`, `heading_y`, `margin`. Engine block keys: `heading*`, `underline`, `animation`, `icons`, `lines`, `tiles`, `badges`, `panels`, `boxes`, `text_box`, `stripes`, `skyline`, `textures`; implementation details live in `../tools/banner.py`.
- `variants` may be `null` (single file named by `theme`) or a list (emits `<output>-<theme>.svg`). README banners list all 13 themes.
- Reference only glyph letters and icon ids that exist in `../tools/glyphs.py` / `../tools/icons.py`.
- Colors normally come from the `theme`; `ink` / `ink_muted` override the theme's text colors, and `textures` supplies fixed block fills (used when content sits on a non-theme background). **Theme-scoped overrides** (e.g. any of these for `minecraft`) belong in `../themes/<theme>.json` `by_banner[<banner>]`, never in these base configs — so the other themes stay untouched.

## Work Guidance
- **Restyle every banner at once** by editing only `_defaults.json` (e.g. change `theme`, `animation`, or `margin`).
- **Edit headings** — `"heading"` (plus `heading_x`/`heading_scale`) uses the pixel font: only `A–Z`, space, `-`, `.`, `,`, `!` exist; any other character is silently skipped. `heading_x` centers it; the underline auto-sizes.
- **Edit body text** — `lines[].text` in `about.json` / `focus-areas.json` uses a normal monospace font (any characters) and does **not** auto-wrap: one entry per line, keep each within the banner width, add/remove entries to change the height. `focus-areas.json` picks each bullet via `bullet.id`.
- **Stack badges** — `tech-stack.json` `badges.sections[]` is `{ "label", "items": [slug] }`; reorder or remove by editing `items`. `badges.label_size` / `label_weight` / `label_color` style the section labels. To add a slug: add its shields.io URL to `../tools/badges.py` `REGISTRY`, run `python3 tools/badges.py cache`, then list the slug. A slug missing from `badges_cache.json` is silently dropped (no error).
- **Block textures** — a `textures` block (`base`, `tile` px, `patterns[]` of extra tiles, `regions[]` of `{texture,x,y,w,h}`, `placements[]` of `{src,x,y,width,height}` for a one-shot standalone SVG like `images/clouds.svg`, drawn before regions as background) tiles tiles from `../textures/svg/` behind the content (raw hex allowed via `data-allow-raw-hex="textures"`). Panels/boxes fill from the same patterns via `panels.sections[].bg_texture` / `.box_texture` (or per-item `face_texture`) and `boxes[].texture`. Colors are fixed, not themed; keep canvas dimensions multiples of `tile`. Pair with `ink` / `ink_muted` (and `box_ink` for boxed text) so text stays readable.
- **Contribution skyline** — `skyline.levels` (bottom→top) accept theme token names or literal hex colours; `skyline.empty` colours zero-count cells; `skyline.rise` toggles the bar-rise animation.
- Copy an existing config as a template; keep `output` a path base without extension.
- Files starting with `_` are ignored by `build.py`.
- After any edit, rebuild: `python3 tools/build.py && python3 tools/check.py` (emits all 13 theme variants).

## Verification
- `python3 tools/build.py && python3 tools/check.py`.

## Child DOX Index
- None.
