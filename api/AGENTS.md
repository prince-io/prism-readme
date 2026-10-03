# api/ — serving endpoints

## Purpose
- Vercel serverless functions that select a theme and serve the matching banner SVG or theme GIF to the README.

## Ownership
- `_theme.js` — shared theme selection (`THEMES`, `WINDOW_MS`, `pickTheme`, `resolveTheme`); not a route.
- `banner/[name].js` — `GET /api/banner/:name` → `assets/<name>-<theme>.svg`.
- `gif.js` — `GET /api/gif` → `gifs/<theme>.gif`.

## Local Contracts
- Banner names (allowlist): `header, about, focus-areas, tech-stack, github-stats, skyline, thanks`; anything else → 404 (also rejects path traversal).
- Theme = `THEMES[floor(Date.now() / WINDOW_MS) % 12]`; `WINDOW_MS` = env `THEME_WINDOW_MS` (default 60000). Every banner and the GIF fetched in one window share a theme.
- `?theme=<name>` overrides selection on both endpoints; an unknown value falls back to the window.
- Reads `assets/<name>-<theme>.svg` and `gifs/<theme>.gif` from the project root; no runtime external fetches (badges/stats/skyline are baked at build time).
- Responses: `image/svg+xml; charset=utf-8` / `image/gif`, `Cache-Control: no-store, max-age=0`, `CDN-Cache-Control: no-store`, `X-Banner-Theme: <theme>`, `X-Robots-Tag: noindex`; `HEAD` returns headers only.
- `vercel.json` (`functions["api/**/*.js"].includeFiles = "{assets/*.svg,gifs/*.gif}"`) bundles both asset sets into the functions.

## Work Guidance
- Change the theme set or window: edit `_theme.js` / the `THEME_WINDOW_MS` env.
- Add a banner: add it to the allowlist and add its config in `../banners/`.
- Replace a GIF: swap `../gifs/<theme>.gif` (see `../gifs/AGENTS.md`).

## Verification
- `vercel dev` from the repo root, then `curl -sI http://localhost:3000/api/banner/<name>` and `.../api/gif`; confirm the content types, a cohesive theme across banner + GIF, and `404` for unknown banner names.

## Child DOX Index
- None.
