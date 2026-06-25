# Maintenance Log

## 2026-06-24 — Repository rehabilitation begins

- Baseline branch: `codex/stage-4-web`
- Baseline commit: `9fd8a57`
- Baseline verification: 88 tests passed
- Supported model: one local tournament director and one managing process
- Compatibility target: valid schema-version-1 `.tgo.json` files
- Known defects: pending-round progression, incomplete aggregate validation, unavoidable-repeat failure, incomplete correction history, shallow Stage 4 tests, minimal McMahon coverage
- Design: `docs/superpowers/specs/2026-06-24-repository-rehabilitation-design.md`
- Plan: `docs/superpowers/plans/2026-06-24-repository-rehabilitation.md`

## Rehabilitation Checkpoints

- `fdda4fd` — characterization baseline and corrected false-positive web test
- `b23174c` — field and aggregate validation
- `41a1ea7` — validated, durable schema-v1 storage
- `8947df4` — shared application-service layer
- `1e99568` — CLI migration to services
- `17d4c61` — progression guard and pending pairing history
- `7d4ce34` — unavoidable-repeat fallback and warnings
- `8cb1386` — explicit correction and regeneration snapshots
- `34a91ec` — simplified McMahon policy
- `35eea8f` — service-backed, split web application
- `916c547` — demo and reliable server startup
- `9bd00cf` — property and complete workflow tests
- `4439c94` — Ruff, mypy, coverage, and formatting gates

## Supported and Reserved Contracts

Supported: Swiss, simplified one-bar McMahon, normal wins, pairing byes,
correction, regeneration, CSV reports, CLI, and local web.

Reserved: draws, forfeits, voids, no-shows, manual overrides, affiliation
preferences, handicap, SODOS, expanded McMahon bands, PDF, and multi-user use.

## 2026-06-24 — Final Rehabilitation Verification

- Ruff format: 57 files formatted, check passed
- Ruff lint: passed
- mypy: 39 production modules, no issues
- Python compilation: passed
- pytest: 135 tests passed
- measured production coverage: 92%
- installed `pairing --help`: passed
- installed demo creation: passed
- HTTP routes `/`, `/players`, `/pairings`, `/results`, `/standings`,
  `/exports`, and `/display`: all returned 200
- live pairing mutation: returned 303 and persisted Round 1
- in-app browser: overview navigation and public display verified
- handoff UI: `http://127.0.0.1:8124/display`

All twelve success criteria in the repository rehabilitation design are
satisfied. The branch is ready for review and integration into `main`.

## 2026-06-25 - Stage 5 print-friendly report slice

- Added a `Reports` hub to the local web app
- Added print-friendly pairings, results, and standings report pages
- Added browser-print affordances for future PDF workflows
- Verified the new report routes in Chrome against a sample tournament
- Tests: focused web route tests and the full suite passed after the report
  addition

## 2026-06-25 - Stage 5 tournament trial checkpoint

- 32-player realistic fixture exercised in both Swiss and simplified McMahon
  simulations
- Five rounds completed in both formats
- Determinism normalized across repeated runs and replayed tournament files
- Focused verification evidence:
  - `python -m pytest tests/integration/test_tournament_trials.py -q` -> 3 passed
  - `python -m pytest tests/integration -q` -> 7 passed
- No-repeat, persistence, audit-history, and export checks passed in focused
  integration verification
- Verification scope at this checkpoint: final Stage 5 verification evidence
  only; evidence now includes fresh collect-only count plus the latest observed
  checks
- Evidence now recorded:
  - `python -m pytest --collect-only -q` -> 140 collected tests
  - Ruff formatting check will be rerun later
  - Ruff lint passed
  - mypy: 39 source files, no issues
  - compileall passed
  - full pytest passed
  - coverage: 93%
- Human field trial is still pending
- Documentation updates captured alongside the trial handoff notes
