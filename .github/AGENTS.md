# .github/ — automation

## Purpose
- GitHub Actions that keep the served banners current.

## Ownership
- `workflows/refresh-banners.yml` — hourly cache refresh + rebuild; commits changed assets.

## Local Contracts
- Runs hourly (`cron "0 * * * *"`) and on `workflow_dispatch`, on the default branch.
- Needs `contents: write`; commits `assets/**` + `tools/*_cache.json` only when they change.
- Uses stdlib Python only (`convert.py` and `textures.py`, the Pillow-based scripts, are not run here).
- The commit is what triggers the Vercel Git integration to redeploy.

## Work Guidance
- Adjust cadence by editing the `cron` in `workflows/refresh-banners.yml`.
- Run manually from the Actions tab (`workflow_dispatch`).

## Verification
- Trigger `workflow_dispatch` and confirm the job commits (or logs "No changes to commit").
- Confirm the follow-up Vercel deployment succeeds.

## Child DOX Index
- None.
