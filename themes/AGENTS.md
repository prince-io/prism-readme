# themes/ — theme presets

## Purpose
- Token sets used by the banner engine. Banners reference a preset by name; adding a preset is the way to add a new look.

## Ownership
- Presets (12): `light`, `solarized-light`, `paper`, `mint`, `lavender`, `rose`, `dracula`, `nord`, `tokyo-night`, `neon`, `forest`, `volcano` (`.json` each).
- Compare all presets via `../banners/theme-preview.json` (emits `../assets/theme-preview-<theme>.svg`); `../tools/preview.py` embeds only those samples.

## Local Contracts
- Shape: `{ "name", "mode": "light"|"dark", "primary"|"secondary"|"tertiary": { "light", "main", "dark" } }` — **9 colors**. `../tools/banner.py` `expand_theme` derives the full `--pf-*` token set; a preset that carries `tokens` instead is passed through unchanged.
- Every hue must have all three shades (`light`/`main`/`dark`) or expansion breaks.
- No layout or geometry here — colors only.
- **Palette doctrine:** three compatible hues, three shades each; canvas follows `mode`; text (`ink`/`box-ink`) is chosen by luminance contrast; frame and static tiles/boxes are tertiary; underline/separation lines use `ink`; `panel-1/2/3` are the P/S/T tints; accents alias P/S/T so icons are tri-color.

## Work Guidance
- Clone an existing preset; keep the 9-color shape.
- Reference a preset by filename stem from a banner config (`"theme": "dark"`).
- Check all presets side by side via `python3 tools/build.py theme-preview && python3 tools/preview.py`.

## Verification
- `python3 tools/build.py` renders a banner per variant; `python3 tools/check.py` then validates output.

## Child DOX Index
- None.
