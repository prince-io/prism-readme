# tools/ — build-time generators

## Purpose
- Dev-time Python scripts that generate everything under `../assets/`. Not deployed; not needed at runtime. Bare `python3`; `convert.py` is the only script with a third-party dep (Pillow).

## Ownership
- `glyphs.py` — bitmap source + generator for `../assets/glyphs.svg` (the 5×7 uppercase pixel font).
- `icons.py` — bitmap source + generator for `../assets/icons.svg` (multi-color pixel icons). Loads `imported_icons.json` and supports per-icon local palettes.
- `convert.py` — imports flat pixel-art PNG/SVG into `../assets/icons/<slug>.svg` snippets and `imported_icons.json` (needs Pillow).
- `badges.py` — fetches + normalizes shields.io tech badges into `badges_cache.json` (inline `<path>` logos, no external refs).
- `stats.py` — fetches GitHub profile stats into `stats_cache.json` (overall / streaks / languages) for the engine's `panels` block.
- `skyline.py` — fetches daily contributions into `contrib_cache.json` (`cache` command) and provides the isometric geometry the engine's `skyline` block renders.
- `banner.py` — engine: `expand_theme` expands a 9-color palette into the full `--pf-*` token set; `render(config, theme)` turns a JSON config + theme into a complete SVG in inline mode.
- `build.py` — CLI: renders every `../banners/*.json` (optionally one by name) into its configured output under `../assets/` (deployable banners and `theme-preview`).
- `check.py` — CLI: validates every SVG (parse, unique ids, `<use>` refs, no raw hex outside token/style).
- `preview.py` — writes `../preview.html`: theme samples, the section banners in one fixed theme (header → about → focus-areas → tech-stack → github-stats → skyline → thanks), then header and skyline rendered per theme as data URIs. Local only (gitignored).
- `badges_cache.json`, `stats_cache.json`, `contrib_cache.json` — fetched data refreshed by the `cache` CLIs; `imported_icons.json` — imported-icon registry.

## Local Contracts
- Scripts write only into `../assets/`; keep output deterministic.
- Bitmap dicts in `glyphs.py` / `icons.py` are the sources of truth. Never hand-edit generated SVGs.
- Font: 5 cols × 7 rows (20×28px), advance 24px, outer corners chamfered one cell. Rects carry no fill (ink inherited).
- Icons: any W×H, per-icon cell 2–4px, every rect carries a `.pf-*` token class.
- `banner.py` is inline-only (no `<use>`) so generated banners survive GitHub's sanitizer.

## Work Guidance
- Change a bitmap → run its generator. Change a layout → edit `banner.py`/config, not output.
- Themes are data: add `../themes/*.json`, don't hardcode colors in the engine.
- The 7 deployable banners (`header, about, focus-areas, tech-stack, github-stats, skyline, thanks`) set all 12 themes and write under `../assets/`.
- Import art with `convert.py` (writes snippets + registry), never hand-paste raster bytes.
- Imported icons are data: edit `imported_icons.json` via `convert.py`, not by hand.
- Badge bodies come from `badges_cache.json`; refresh with `python3 tools/badges.py cache`. Never reference shields.io from inside an SVG.
- Contribution data comes from `contrib_cache.json`; refresh with `python3 tools/skyline.py cache`.
- Banner output containing badges or a `skyline` block carries `data-allow-raw-hex` (third-party fills / computed shades are not tokens).

## Verification
- `python3 tools/badges.py cache && python3 tools/stats.py cache && python3 tools/skyline.py cache && python3 tools/build.py && python3 tools/check.py`.

## Child DOX Index
- None.
