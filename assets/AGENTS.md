# assets/ — SVG banners and libraries

## Purpose
- Generated SVGs and dev artifacts: the deployable `<name>-<theme>.svg` banners (served), `theme-preview-*` samples, the `glyphs.svg`/`icons.svg` libraries, and `icons/` snippets.

## Ownership
- `glyphs.svg` — generated glyph library + reference sheet (`../tools/glyphs.py`).
- `icons.svg` — generated icon library + reference sheet (`../tools/icons.py`).
- `icons/<slug>.svg` — imported pixel-art snippets (`../tools/convert.py`); each is self-contained with a local exact palette and a copyable `<g id="i-<slug>">`.
- `theme-preview-<theme>.svg` — generated per-theme sample sheets (`../tools/build.py`).
- Theme presets live in `../themes/`; repo-wide contracts in `../AGENTS.md` and the child docs.

## Local Contracts
- Generated files are build output: edit the source (`../tools/*.py`, `../banners/*.json`, `../themes/*.json`, `../textures/svg/`), never the SVG.
- One file, everything inline: no external assets, `<script>`, `<foreignObject>`, `@font-face`, or `@import`. `minecraft` block textures are inlined as `<pattern>` fills (tiles from `../textures/svg/`).
- Colors go through `--pf-*` token classes; no raw `#hex` outside token/style blocks.
- `id` values unique; glyphs 5×7 (20×28px), advance 24px, corners chamfered one cell.
- Filenames contain no spaces.

## Work Guidance
- Add a banner by adding `../banners/*.json` and running `python3 tools/build.py`.
- Icons are placed inline by the engine (`icons` / `tiles[].icon`); reference sheets use `<use>`.

## Verification
- `python3 tools/build.py && python3 tools/check.py`.

## Child DOX Index
- `icons/AGENTS.md` — imported pixel-art icon snippets with local exact palettes.
