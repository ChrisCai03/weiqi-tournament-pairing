# Project Context

This file is a lightweight handoff note for future sessions working on the Stage 4 web branch.

## Repository

- Main repo: `C:\Users\user\Documents\Pairing software dev`
- Active Stage 4 worktree: `C:\Users\user\Documents\Pairing software dev\.worktrees\stage-4-web`
- Stage 4 branch: `codex/stage-4-web`

## High-Level Product Direction

The project is an open-source local-first Weiqi/Go tournament pairing application.

Current priorities:

1. correctness
2. auditability
3. simple local workflow
4. modular engine separate from CLI/UI

The current product path is:

- Stage 1: data model, JSON storage, CSV import, CLI foundation
- Stage 2: Swiss tournament workflow
- Stage 3: McMahon tournament workflow
- Stage 4: local web console, CSV exports, public display page
- later: PDF output, advanced workflows

## Key Design Documents

- Stage 1 broad design:
  - `docs/superpowers/specs/2026-06-22-weiqi-tournament-design.md`
- Stage 2 Swiss design:
  - `docs/superpowers/specs/2026-06-23-stage-2-swiss-design.md`
- Stage 2 implementation plan:
  - `docs/superpowers/plans/2026-06-23-stage-2-swiss.md`
- Stage 3 McMahon design:
  - `docs/superpowers/specs/2026-06-24-stage-3-mcmahon-design.md`
- Stage 3 implementation plan:
  - `docs/superpowers/plans/2026-06-24-stage-3-mcmahon.md`

## Current Stage 4 Status

### Completed

- Stage 2 Swiss foundation is merged in
- Stage 3 McMahon workflow is merged in
- Stage 4 web console is implemented:
  - overview, players, pairings, results, standings, exports, display routes
  - player CSV import form
  - CSV export endpoints for players, pairings, results, standings
  - public display page for boards
- CLI now includes `web`:
  - `pairing web <tournament_path> --host 127.0.0.1 --port 8000`

## Recent Verified State

Current verified branch state:

- full suite in the Stage 4 worktree passed: `88 passed`
- local browser smoke test passed against a demo tournament

Useful verification commands:

```powershell
python -m pytest tests/unit/test_swiss_pairing.py tests/unit/test_cli.py -q
python -m pytest
```

## Important Branch Commits

Recent branch history:

- `799a479` Refresh Stage 3 handoff notes
- `6828f63` Expose McMahon CLI workflow
- `d1a69e5` Add McMahon pairing core
- `24198f3` Add McMahon format persistence
- `3eccd16` Document Stage 3 McMahon plan
- `d585780` Add Swiss regeneration and stale round handling
- `07f85d9` Fix later round Swiss bye fallback
- `e9b8da8` Add later round Swiss pairing

## Expected Next Steps

The next planned work is:

1. add PDF output or a simple print-friendly pairing sheet
2. harden manual override and repair flows in the web UI
3. split the web app into smaller modules once the interface settles

## Local Conventions Learned So Far

- Use `apply_patch` for file edits.
- Keep changes small and commit-safe.
- Verify with fresh test runs before claiming completion.
- The project uses Python 3.12 from:
  - `C:\Users\user\AppData\Local\Programs\Python\Python312\python.exe`
- Git worktree cleanup on Windows can be messy due to temp/cache permissions. Avoid unnecessary churn in `.tmp` and `.pytest_cache`.

## Architectural Notes

- JSON `.tgo.json` is the canonical local save format.
- CSV is for import/export, not full tournament persistence.
- Pairing and standings logic should stay in `src/pairing/engine/`.
- CLI should remain thin and orchestration-focused.
- Tournament state should reject malformed persisted data rather than silently inventing defaults.

## Resume Checklist

If a future session resumes here:

1. open this file
2. inspect `git log --oneline -8`
3. run `python -m pytest`
4. continue with Stage 4 polish or the next export/report slice
