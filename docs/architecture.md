# Architecture

## Operating Model

The application supports one local tournament director and one active writer.
The `.tgo.json` file is the source of truth. The web UI is not a separate
backend; it is another adapter over the same services used by the CLI.

```text
CLI / Local WSGI Web
          |
pairing.application
          |
Tournament Aggregate ---- Pairing / Standings Engine
          |
JSON Storage / CSV Reports
```

## Package Responsibilities

- `pairing.domain`: persisted models, supported-value contracts, aggregate
  validation, result correction, stale-round state, and audit records.
- `pairing.engine`: pure standings, history, Swiss/McMahon policies, colour and
  bye allocation, strict pairing search, and unavoidable-repeat fallback.
- `pairing.application`: complete load/mutate/validate/save workflows with
  actor-aware audit events and typed outcomes.
- `pairing.storage`: schema validation and durable atomic replacement.
- `pairing.import_export`: CSV parsing and read-only report generation.
- `pairing.cli`: argument parsing and text presentation only.
- `pairing.web`: request dispatch, forms, responses, views, and server
  lifecycle.

Dependencies point inward: domain and engine never import CLI, web, or storage.
Adapters do not mutate tournament objects directly.

## Correctness Contracts

- Complete aggregate validation runs before save and after load.
- Pairing history includes pending games; scoring includes completed results.
- Normal next-round generation requires the previous active round to be
  complete.
- Strict no-repeat pairing is preferred. If impossible, deterministic
  least-penalty repeats are generated with warnings.
- Initial result entry cannot overwrite a completed result.
- Correction retains the prior result snapshot and invalidates later rounds.
- Regeneration snapshots superseded rounds in the audit log before replacing
  active downstream rounds.

## McMahon Policy

The implemented McMahon variant has one ranked bar:

- at or above bar: starting score `1.0`
- below bar or unranked: starting score `0.0`
- total score: starting score plus game score

This deliberately excludes rank bands, SODOS, separate upper/lower bars, and
handicap rules.

## Persistence

Schema version 1 remains compatible. Writes use a temporary sibling file,
flush and `fsync`, then atomic replacement. Failed validation or replacement
leaves the previous file unchanged.

## Quality Gates

- Ruff formatting and lint
- mypy for production modules
- pytest unit, property, integration, and live-server tests
- coverage threshold monitored at 90% or higher
