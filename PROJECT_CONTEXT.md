# Project Context

## Current Baseline

- Worktree: `C:\Users\user\Documents\Pairing software dev`
- Branch: `codex/stage-5-tournament-trials`
- Integration target: `main` after verification
- Scope: one local tournament director and one managing process
- Canonical state: schema-version-1 `.tgo.json`

This active feature work branch contains rehabilitated Stages 1-4, the first
Stage 5 report slice, and the completed realistic tournament simulations. It
should be treated as the active implementation baseline until verification is
complete and the work is integrated into `main`.

## Architecture

CLI and web call `TournamentService`. Services own persistence workflows.
Domain and engine code remain independent of storage and presentation.

Read:

1. `README.md`
2. `docs/architecture.md`
3. `MAINTENANCE.md`
4. `docs/roadmap.md`

## Supported Behavior

- Swiss and simplified one-bar McMahon
- deterministic pairings
- pending-round progression guard
- pending pairings in opponent/colour history
- unavoidable repeat warnings
- explicit result correction
- auditable regeneration snapshots
- CSV import/export
- local WSGI UI and public display
- print-friendly reports for pairings, results, and standings
- realistic 32-player tournament simulations for Swiss and McMahon coverage

## Reserved Behavior

Draws, forfeits, manual overrides, affiliation-aware pairing, handicap,
expanded McMahon bands, SODOS, PDF output, and multi-user operation are not
active features.

## Verification

Run:

```powershell
python -m ruff format --check .
python -m ruff check .
python -m mypy src/pairing
python -m compileall -q src
python -m pytest --cov=pairing --cov-report=term-missing -q
```

## Integration Recommendation

Continue with the Stage 5 report and tournament-trial milestones on the active
feature work branch. Keep report surfaces small, printable, and easy to verify
before adding PDF or more advanced output. Merge into `main` after the
verification checkpoint is complete.
