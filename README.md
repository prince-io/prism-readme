# prism-readme

**A self-contained, theme-rotating banner service for a GitHub profile README.**
Python generates pixel-art SVG banners in 12 themes; a Vercel function serves a
different theme on every time window, plus a matching per-theme GIF.

<img src="https://prism-readme.vercel.app/api/banner/header" width="100%" alt="Header banner">

## Highlights

- **7 banners** — `header`, `about`, `focus-areas`, `tech-stack`, `github-stats`, `skyline`, `thanks`, each rendered in every theme.
- **12 themes** — `light`, `solarized-light`, `paper`, `mint`, `lavender`, `rose`, `dracula`, `nord`, `tokyo-night`, `neon`, `forest`, `volcano`.
- **Time-window rotation** — the served theme is `THEMES[floor(now / THEME_WINDOW_MS) % 12]`, so all banners + the GIF fetched together share one cohesive look.
- **Baked data** — GitHub stats, top languages, streaks and the contribution skyline are fetched at build time and inlined; the runtime does **zero** external calls.
- **Self-contained SVGs** — everything (font, icons, badges) is inline `<rect>`/`<path>`, so it survives GitHub's camo proxy and SVG sanitizer.
- **Hourly refresh** — a GitHub Action re-pulls the data, rebuilds, and commits; Vercel redeploys on the push.

## How it works

```text
tools/*.py  ──build──▶  assets/<name>-<theme>.svg  ──┐
                                                     ├─▶ api/ (Vercel) ─▶ src="…/api/banner/<name>"
gifs/<theme>.gif ────────────────────────────────────┘                     src="…/api/gif"
```

1. **Generate** — `tools/build.py` renders each `banners/*.json` config × 12 `themes/*.json` presets into `assets/`.
2. **Serve** — Vercel functions pick a theme from the clock and stream the matching file (`no-store`, so GitHub refetches each load).
3. **Refresh** — `.github/workflows/refresh-banners.yml` runs hourly, refreshes the caches, rebuilds, and commits.

## Endpoints

| Route | Returns |
|---|---|
| `GET /api/banner/:name` | `assets/<name>-<theme>.svg` (`image/svg+xml`) |
| `GET /api/gif` | `gifs/<theme>.gif` (`image/gif`) |

`:name` ∈ `{ header, about, focus-areas, tech-stack, github-stats, skyline, thanks }`.
Add `?theme=<name>` to force a specific theme (testing).

## Project layout

```text
banner-app/
├── api/                 # Vercel functions: banner/[name].js, gif.js, _theme.js
├── assets/              # generated SVGs (7 × 12) + glyph/icon libraries
├── banners/             # per-banner content configs (JSON)
├── themes/              # 12 palettes (9 colors each)
├── gifs/                # <theme>.gif (one per theme) + cat.gif
├── tools/               # Python generator + data caches
├── .github/workflows/   # hourly refresh Action
├── SNIPPET.md           # copy-paste block for the profile README
└── vercel.json          # bundles assets/ + gifs/ into the functions
```

## Getting started

Requires `python3` (standard library; **Pillow** only for `tools/convert.py`), and optionally
[`gifsicle`](https://www.lcdf.org/gifsicle/) for GIF optimization.

```bash
# render every banner in every theme, then validate
python3 tools/build.py && python3 tools/check.py

# local preview page (preview.html)
python3 tools/preview.py

# refresh the baked data, then rebuild
python3 tools/badges.py cache && python3 tools/stats.py cache && python3 tools/skyline.py cache
```

## Customize

| What | Where |
|---|---|
| Heading / About / Focus text | `banners/about.json`, `banners/focus-areas.json` (`lines[].text`, `heading`) |
| Stack badges | `banners/tech-stack.json` (`badges.sections[].items`); add new slugs to `tools/badges.py` `REGISTRY` and run `badges.py cache` |
| Colors | `themes/*.json` (9-color `primary`/`secondary`/`tertiary` palette) |
| Icons | `python3 tools/convert.py <image> --out assets/icons` |
| Animated backdrop | replace `gifs/<theme>.gif` |
| Rotation speed | env `THEME_WINDOW_MS` (default `60000`) |

Headings use a 5×7 pixel font (`A–Z`, space, `-`, `.`, `,`, `!`); body copy uses a normal
monospace font and does not wrap. After any edit: `build.py && check.py`.

## Deploy

**Vercel** — deploy the repo; no build step is needed. `vercel.json` bundles `assets/*.svg`
and `gifs/*.gif` into the functions, and `/api/banner/*` + `/api/gif` are live immediately.

**Auto-refresh** — `.github/workflows/refresh-banners.yml` runs `on: schedule` (hourly) and
`workflow_dispatch`, commits changed `assets/**` + `tools/*_cache.json`, and lets the Vercel
Git integration redeploy.

## Data sources

All fetched at build time: [shields.io](https://shields.io) (badges),
[github-readme-stats](https://github.com/anuraghazra/github-readme-stats) + [streak-stats](https://streak-stats.demolab.com)
(overall / languages / streaks), and the [contributions API](https://github.com/grubersjoe/github-contributions-api) (skyline).

## Docs

Every folder carries an `AGENTS.md` (DOX hierarchy) — the binding source of truth for that subtree,
starting at the root `AGENTS.md`.
