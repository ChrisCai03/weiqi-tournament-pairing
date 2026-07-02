# Weiqi Tournament Pairing

Local-first Swiss and simplified McMahon tournament software for Weiqi/Go.

The current product is designed for one tournament director running one local
process. A schema-versioned `.tgo.json` file is the canonical tournament
record; the CLI and simple web UI use the same application services.

## Setup

Python 3.12 or newer is required.

```powershell
python -m pip install -e ".[dev]"
```

Run the quality gates:

```powershell
python -m ruff format --check .
python -m ruff check .
python -m mypy src/pairing
python -m pytest --cov=pairing --cov-report=term-missing -q
```

## Quick Demo

```powershell
pairing demo demo.tgo.json
pairing web demo.tgo.json --port 8000 --open-browser
```

On Windows, double-click `run_local.bat` from the repository root to create or
reuse `.tmp\demo.tgo.json` and open the local web UI on
`http://127.0.0.1:8123/`. You can also drag an existing `.tgo.json` file onto
the script to launch that tournament.

The web server remains attached to the managing terminal. Stop it with
`Ctrl+C`. Without `--open-browser`, open `http://127.0.0.1:8000/`.
The web UI now includes a `Reports` area with print-friendly pairings,
results, and standings pages for browser print/PDF workflows.

## Tournament Workflow

Create and populate a tournament:

```powershell
pairing create event.tgo.json --name "Example Weiqi Open" --rounds 5 --format swiss
pairing import-players event.tgo.json players.csv
```

Run a round:

```powershell
pairing pair-round event.tgo.json
pairing enter-result event.tgo.json --round 1 --board 1 --winner black
pairing standings event.tgo.json
```

Correct a result and rebuild downstream pairings:

```powershell
pairing correct-result event.tgo.json --round 1 --board 1 --winner white
pairing regenerate-from event.tgo.json --round 1
```

Sign and verify the tamper-evident audit log:

```powershell
pairing audit-sign event.tgo.json
pairing audit-verify event.tgo.json
```

The local signing key defaults to `.pairing_audit_key`, which is intentionally
ignored by Git. The web app stores this key beside the active tournament file
and automatically re-signs after web mutations; CLI commands use the current
working directory unless `--key-path` is provided. If a source-level edit
changes the tournament file after signing, verification reports the state-hash
mismatch.

A new round cannot be generated until the preceding round is complete.
Unavoidable repeat opponents produce explicit warnings instead of stopping the
tournament.

## Current Scope

Supported:

- individual Swiss tournaments
- simplified McMahon with one ranked bar
- dan/kyu and unranked players
- CSV player import and report export
- result entry and correction
- auditable downstream regeneration
- tamper-evident local audit-log signing and verification
- local CLI and server-rendered web UI
- Windows click-and-go local launcher
- print-friendly report pages for pairings, results, and standings
- realistic trial coverage with a 32-player fixture and deterministic
  five-round Swiss/McMahon simulations

Reserved for later work:

- draws, forfeits, voids, and no-shows
- manual pairing overrides
- affiliation-aware pairing
- handicap pairing
- SODOS and expanded McMahon bands
- multi-user/networked operation

## Documentation

- [Architecture](docs/architecture.md)
- [Roadmap](docs/roadmap.md)
- [Maintenance log](MAINTENANCE.md)
- [Tournament trial runbook](docs/tournament-trial-runbook.md)
- [Tournament file format](docs/tournament-file-format.md)
- [CSV format](docs/csv-format.md)
- [Rehabilitation design](docs/superpowers/specs/2026-06-24-repository-rehabilitation-design.md)
