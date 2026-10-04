# textures/ — Minecraft block tiles

## Purpose
- Generated 16×16 vector tiles that give the `minecraft` theme its block fills. Build-time inputs embedded into the banner SVGs; never served at runtime.

## Ownership
- `svg/<name>.svg` — one tile per block the theme references: `ancient-debris-side`, `coal-ore`, `crimson-planks`, `deepslate`, `deepslate-diamond-ore`, `deepslate-gold-ore`, `deepslate-lapis-ore`, `deepslate-redstone-ore`, `dirt`, `end-stone`, `gold-ore`, `grass-block-side`, `iron-ore`, `lapis-ore`, `nether-bricks`, `nether-gold-ore`, `nether-quartz-ore`, `netherrack`, `oak-log`, `oak-planks`, `quartz-block-bottom`, `sky`, `stone`. (`sky` is a solid fill; the rest are block patterns.)
- `images/clouds.svg` — the single standalone embed, placed once via `header`'s `textures.placements` (transparent, native 832×277).

## Local Contracts
- Only tiles actually referenced by `../themes/minecraft.json` are kept; add a tile only when a banner uses it.
- Tiles are produced by `../tools/textures.py` from Minecraft block PNGs, but those sources are **not** committed here — the committed SVGs are the authoritative build inputs. Regenerating requires the original PNGs.
- Each tile uses `viewBox="0 0 16 16"`, `width/height=512`, `shape-rendering="crispEdges"`, and a numeric local palette `--pf-tex-<slug>-n` (exact hex, non-themeable) so `check.py` passes. Colors are fixed, not themed.
- Keep banner canvas dimensions multiples of the configured `tile` (64).

## Work Guidance
- Regenerate (only when the PNG sources are available): `python3 tools/textures.py --sky '#78A7FF'`.
- Embed a one-shot image: `python3 tools/textures.py <png> --embed --out textures/images`.
- Reference tiles from `../themes/minecraft.json` (theme block), never from the shared `banners/*.json` base configs.

## Verification
- `python3 tools/build.py && python3 tools/check.py` → `PASS`.

## Child DOX Index
- None.
