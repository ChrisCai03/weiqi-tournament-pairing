# Project Context

## Current Baseline

- Worktree: `C:\Users\user\Documents\Pairing software dev\.worktrees\stage-4-web`
- Branch: `codex/stage-4-web`
- Scope: one local tournament director and one managing process
- Canonical state: schema-version-1 `.tgo.json`

The branch now contains rehabilitated Stages 1–4. It should be treated as the
integration candidate; `main` still lags behind the implemented workflow.

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

## Reserved Behavior

Draws, forfeits, manual overrides, affiliation-aware pairing, handicap,
expanded McMahon bands, SODOS, PDF, and multi-user operation are not active
features.

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

Review the commits after `9fd8a57`, then merge `codex/stage-4-web` into `main`
as one rehabilitation series. Do not delete the worktree or branch until the
user chooses the integration method.
