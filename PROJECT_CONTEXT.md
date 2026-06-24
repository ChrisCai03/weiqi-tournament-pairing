# Project Context

This file is a lightweight handoff note for future sessions working on the Stage 3 McMahon branch.

## Repository

- Main repo: `C:\Users\user\Documents\Pairing software dev`
- Active Stage 3 worktree: `C:\Users\user\Documents\Pairing software dev\.worktrees\stage-3-mcmahon`
- Stage 3 branch: `codex/stage-3-mcmahon`

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
- later: exports, UI, advanced workflows

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

## Current Stage 3 Status

### Completed

- Stage 2 Swiss foundation merged into this worktree
- Stage 3 planning/spec committed
- McMahon format persistence complete:
  - `Tournament.create(..., format="mcmahon")`
  - `TournamentConfig.mcmahon_bar_rank`
  - format round-trips through save/load
- McMahon pairing core complete:
  - shared pairing core extracted
  - McMahon starting-score policy
  - format-dispatched round generation
  - McMahon-aware standings inputs and outputs
- McMahon CLI workflow complete:
  - `create --format mcmahon`
  - `pair-round` dispatches by tournament format
  - `standings` prints start/game/total columns
  - McMahon pairings land with `pairing_method="mcmahon"`

## Recent Verified State

Current verified branch state:

- full suite in the Stage 3 worktree passed after McMahon CLI wiring: `84 passed`

Useful verification commands:

```powershell
python -m pytest tests/unit/test_swiss_pairing.py tests/unit/test_cli.py -q
python -m pytest
```

## Important Branch Commits

Recent branch history:

- `6828f63` Expose McMahon CLI workflow
- `d1a69e5` Add McMahon pairing core
- `24198f3` Add McMahon format persistence
- `3eccd16` Document Stage 3 McMahon plan
- `d585780` Add Swiss regeneration and stale round handling
- `07f85d9` Fix later round Swiss bye fallback
- `e9b8da8` Add later round Swiss pairing
- `12c95f4` Add later round Swiss pairing
- `7c49b4e` Update Stage 2 branch context after slices C and D
- `4e8cd5a` Harden result entry validation
- `2c2e2c2` Add result entry workflow
- `4edad1a` Harden Swiss round metadata and limits
- `08385ec` Add first round Swiss pairing
- `0b0214f` Ignore pending games in standings history

## Expected Next Steps

The next planned work is:

1. polish McMahon explanations and audit wording if needed
2. refresh Stage 3 docs and branch notes if any wording drift remains
3. move on to Stage 4 import/export hardening once McMahon is settled

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
4. continue with the remaining Stage 3 cleanup or Stage 4 planning
