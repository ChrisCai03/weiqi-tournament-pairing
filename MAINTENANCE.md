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
  - Ruff format: 58 files already formatted
  - Ruff lint passed
  - mypy: 39 source files, no issues
  - compileall passed
  - full pytest: 140 passed
  - coverage: 93%
- Human field trial is still pending
- Documentation updates captured alongside the trial handoff notes

## 2026-06-25 - Stage 5 integrated into main

- Fast-forwarded `codex/stage-5-tournament-trials` into local `main`
- Normalized Ruff formatting for the print-report files in the main checkout
  after the merge exposed a Windows line-ending difference
- Updated `PROJECT_CONTEXT.md` to identify `main` as the active baseline

## 2026-07-02 - Local launcher and audit-integrity checkpoint

- Active branch: `codex/stage-6-director-workflow`
- Added `run_local.bat` for Windows click-and-go prototyping:
  - default tournament: `.tmp\demo.tgo.json`
  - default web URL: `http://127.0.0.1:8123/`
  - existing `.tgo.json` files can be passed or dragged onto the script
- Added tamper-evident local audit integrity:
  - local key file: `.pairing_audit_key` (Git-ignored)
  - algorithm: HMAC-SHA256 over canonical audit entries plus previous
    signature
  - state hash excludes audit integrity fields so source-level tournament edits
    after signing are detected as state-hash mismatches
  - current implementation intentionally leaves room for future key providers
    and stronger encryption/signing backends
- Added CLI operations:
  - `pairing audit-sign event.tgo.json`
  - `pairing audit-verify event.tgo.json`
- Verification evidence at this checkpoint:
  - `python -m pytest tests/unit/test_cli.py -q -k audit` -> 2 passed
  - `python -m ruff check src\pairing\cli\main.py src\pairing\application\service.py tests\unit\test_cli.py` -> passed
  - `python -m pytest tests/unit/test_run_local.py tests/unit/test_audit_integrity.py tests/unit/test_cli.py tests/unit/test_json_store.py -q` -> 43 passed
- Remaining work:
  - expose audit verification status in the web UI
  - decide whether mutating service operations should auto-sign by default
  - add future key-provider/encryption abstraction before broader deployment

## 2026-07-02 - Web audit controls and automatic web signing

- Added an `Audit` tab to the local web UI.
- Added `GET /audit` for director-facing verification status:
  - pass/fail status
  - current tournament state hash
  - verification error list
  - signed/unsigned audit-entry counts
- Added `POST /audit/sign` to sign the current audit log from the web UI.
- Changed audit verification so a read-only verify no longer creates a missing
  local key. Signing remains the operation that creates the key.
- Configured the web app to auto-sign after mutating web operations using a
  `.pairing_audit_key` beside the active tournament file.
- CLI audit commands remain manual and can use `--key-path`; without it they
  use the current working directory.
- Verification evidence at this checkpoint:
  - `python -m pytest tests/unit/test_audit_integrity.py tests/unit/test_cli.py tests/unit/test_web_app.py tests/unit/test_web_routing.py -q` -> 37 passed
  - `python -m pytest tests/unit/test_application_service.py tests/unit/test_audit_integrity.py tests/unit/test_cli.py tests/unit/test_web_app.py tests/unit/test_web_routing.py -q` -> 46 passed
  - focused Ruff checks on changed source/tests -> passed
