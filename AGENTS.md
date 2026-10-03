# DOX framework

- DOX is a highly performant AGENTS.md hierarchy installed here.
- Agents must follow DOX instructions across any edits.

## Core Contract

- AGENTS.md files are binding work contracts for their subtrees.
- Work products, source materials, instructions, records, assets, and durable docs must stay understandable from the nearest applicable AGENTS.md plus every parent AGENTS.md above it.

## Read Before Editing

1. Read the root AGENTS.md.
2. Identify every file or folder you expect to touch.
3. Walk from the repository root to each target path.
4. Read every AGENTS.md found along each route.
5. If a parent AGENTS.md lists a child AGENTS.md whose scope contains the path, read that child and continue from there.
6. Use the nearest AGENTS.md as the local contract and parent docs for repo-wide rules.
7. If docs conflict, the closer doc controls local work details, but no child doc may weaken DOX.

Do not rely on memory. Re-read the applicable DOX chain in the current session before editing.

## Update After Editing

Every meaningful change requires a DOX pass before the task is done.

Update the closest owning AGENTS.md when a change affects:

- purpose, scope, ownership, or responsibilities
- durable structure, contracts, workflows, or operating rules
- required inputs, outputs, permissions, constraints, side effects, or artifacts
- user preferences about behavior, communication, process, organization, or quality
- AGENTS.md creation, deletion, move, rename, or index contents

Update parent docs when parent-level structure, ownership, workflow, or child index changes. Update child docs when parent changes alter local rules. Remove stale or contradictory text immediately. Small edits that do not change behavior or contracts may leave docs unchanged, but the DOX pass still must happen.

## Hierarchy

- Root AGENTS.md is the DOX rail: project-wide instructions, global preferences, durable workflow rules, and the top-level Child DOX Index.
- Child AGENTS.md files own domain-specific instructions and their own Child DOX Index.
- Each parent explains what its direct children cover and what stays owned by the parent.
- The closer a doc is to the work, the more specific and practical it must be.

## Child Doc Shape

- Create a child AGENTS.md when a folder becomes a durable boundary with its own purpose, rules, responsibilities, workflow, materials, or quality standards.
- Work Guidance must reflect the current standards of the project or user instructions; if there are no specific standards or instructions yet, leave it empty.
- Verification must reflect an existing check; if no verification framework exists yet, leave it empty and update it when one exists.

Default section order:

- Purpose
- Ownership
- Local Contracts
- Work Guidance
- Verification
- Child DOX Index

## Style

- Keep docs concise, current, and operational.
- Document stable contracts, not diary entries.
- Put broad rules in parent docs and concrete details in child docs.
- Prefer direct bullets with explicit names.
- Do not duplicate rules across many files unless each scope needs a local version.
- Delete stale notes instead of explaining history.
- Trim obvious statements, repeated rules, misplaced detail, and warnings for risks that no longer exist.

## Closeout

1. Re-check changed paths against the DOX chain.
2. Update nearest owning docs and any affected parents or children.
3. Refresh every affected Child DOX Index.
4. Remove stale or contradictory text.
5. Run existing verification when relevant.
6. Report any docs intentionally left unchanged and why.

## User Preferences

Record durable user requests here or in the relevant child AGENTS.md.

---

# banner-app/ — dynamic banner service + generator

## Purpose

- Self-contained project: the Python generator (`tools/`) builds themed banner SVGs into `assets/`, and a Vercel function (`api/`) serves them to the profile README, rotating the theme per time window (1 of 12). This folder is the repo root and the Vercel deploy root.

## Ownership

- `README.md` — the copy-paste snippet for the profile README (not part of the build).
- `assets/<name>-<theme>.svg` — served data: 7 banners × 12 themes = 84 generated SVGs, plus dev sheets (`glyphs.svg`, `icons.svg`, `icons/`, `theme-preview-*`). Build output; never hand-edited.
- `tools/` — generator pipeline (engine, font/icons, caches, CLIs). See `tools/AGENTS.md`.
- `banners/` — per-banner content configs. See `banners/AGENTS.md`.
- `themes/` — 12 palette presets. See `themes/AGENTS.md`.
- `gifs/` — per-theme README GIFs (`<theme>.gif`). See `gifs/AGENTS.md`.
- `api/` — Vercel endpoints that serve the SVGs and the theme GIF. See `api/AGENTS.md`.
- `vercel.json` — function config (`functions["api/**/*.js"].includeFiles = "assets/*.svg"`).

## Local Contracts

- Content edits go in `banners/*.json` (About/Focus lines, tech list, headings) or `themes/*.json`; rebuild — never hand-edit `assets/`.
- The serving contract (name allowlist, theme window, cache headers) lives in `api/AGENTS.md`.
- No runtime external fetches: badges, stats, and skyline are baked at build time.

## Work Guidance

- **Edit content** (headings, About/Focus text, stack badges): see `banners/AGENTS.md`; **add/remove images**: see `assets/icons/AGENTS.md`.
- Rebuild: `python3 tools/build.py && python3 tools/check.py`.
- Refresh live data then rebuild: `python3 tools/badges.py cache && python3 tools/stats.py cache && python3 tools/skyline.py cache`.
- Auto-refresh: `.github/workflows/refresh-banners.yml` runs the cache + rebuild hourly and commits changes; the Vercel Git integration then redeploys the push.
- Preview locally: `python3 tools/preview.py` → `preview.html` (gitignored).
- Import new art: `python3 tools/convert.py` (see `tools/AGENTS.md`).
- Deploy: `vercel --prod` from this folder; alias `https://readme-profile-app.vercel.app`.

## Verification

- `python3 tools/build.py && python3 tools/check.py` → `PASS`.
- `vercel dev` then request each name (e.g. `curl -sI http://localhost:3000/api/banner/header`) → `image/svg+xml`; theme flips across a `THEME_WINDOW_MS` boundary and matches across banners in one window.

## Child DOX Index

- `tools/AGENTS.md` — generator pipeline: font, icons, engine, CLIs, caches.
- `banners/AGENTS.md` — per-banner content configs consumed by the engine.
- `themes/AGENTS.md` — 12 palette presets.
- `gifs/AGENTS.md` — per-theme README GIFs.
- `assets/AGENTS.md` — generated SVGs and libraries (contains `icons/AGENTS.md`).
- `api/AGENTS.md` — Vercel banner endpoint (theme selection + serving).
- `.github/AGENTS.md` — GitHub Actions (hourly banner refresh).
