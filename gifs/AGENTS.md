# gifs/ — per-theme README GIFs

## Purpose
- One animated GIF per theme, so the README GIF matches the rotating banner theme. The app serves `<theme>.gif` alongside the banners.

## Ownership
- `<theme>.gif` — one per preset in `../themes/` (13 total), chosen to match that theme's palette.
- `cat.gif` — kept for reference only; not served.

## Local Contracts
- Filenames are exactly the theme names; keep them in sync with `../themes/*.json`.
- Capped at 800px wide (never upscaled), optimized with gifsicle `-O3`.
- Replace a GIF by overwriting its `<theme>.gif` file — do not rename it.

## Work Guidance
- **Optimize/replace:** `gifsicle -O3 --resize-width 800 <in>.gif -o <theme>.gif` (add `--colors 256 --lossy=100` if still large).
- **Match a theme:** pick the GIF whose dominant colors fit the theme's `primary`/`secondary`/`tertiary` in `../themes/<theme>.json`.

## Verification
- `ls gifs/*.gif` → one file per theme plus `cat.gif`.
- `curl -sI http://localhost:3000/api/gif` returns `image/gif` and an `X-Banner-Theme` matching the banners.

## Child DOX Index
- None.
