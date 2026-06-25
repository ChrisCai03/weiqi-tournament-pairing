# Tournament Trial Runbook

This runbook documents the repeatable local trial workflow for Stage 5.
It assumes one tournament director, one managing terminal, and one local
process. Automated realistic simulations have already been completed; a human
field trial has not yet been conducted. PDF export remains deferred until the
print-layout trial is complete.

## Prerequisites

- Branch: `codex/stage-5-tournament-trials`
- Python 3.12 and the project development dependencies installed
- A writable local path for the tournament file, such as `trial-open.tgo.json`
- The realistic roster fixture at `tests/fixtures/players/realistic-open.csv`
- One managing terminal only; do not split the workflow across multiple
  operators or background services

## Sample event creation and import

Swiss sample:

```powershell
pairing create trial-open.tgo.json --name "Trial Open" --rounds 5 --format swiss
pairing import-players trial-open.tgo.json tests/fixtures/players/realistic-open.csv
```

Simplified McMahon sample:

```powershell
pairing create trial-mcmahon.tgo.json --name "Trial McMahon" --rounds 5 --format mcmahon
pairing import-players trial-mcmahon.tgo.json tests/fixtures/players/realistic-open.csv
```

The imported roster should contain 32 players and preserve the player metadata
needed for later reporting and audit review.

## Pre-round checks

Before generating the first round, confirm:

- the roster imported cleanly and still shows 32 players;
- the seed order is stable and deterministic;
- rank, country, club, school, team, and notes fields survived persistence;
- the tournament file opens cleanly after a save/reload cycle;
- there is no active round in progress and no stale uncompleted round;
- the event is still being run from one local process.

Useful inspection commands:

```powershell
pairing standings trial-open.tgo.json
```

When using the web UI, verify the local `/reports`, `/pairings`, `/results`,
and `/standings` pages before starting the round cycle.

## Round generation, printing, result entry, correction, and regeneration

Generate a round only after the previous round is complete:

```powershell
pairing pair-round trial-open.tgo.json
```

Expected checks:

- 32-player events produce 16 games and no bye;
- board numbers are consecutive;
- the pairing method matches the selected format;
- the generated round can be printed or browser-printed without clipped rows or
  missing headings.

Enter results for every game:

```powershell
pairing enter-result trial-open.tgo.json --round 1 --board 1 --winner black
```

Expected checks:

- each result persists immediately;
- the round remains blocked from regeneration until all boards are complete;
- standings update after the last pending result is entered.

If a result must be corrected:

```powershell
pairing correct-result trial-open.tgo.json --round 1 --board 1 --winner white
pairing regenerate-from trial-open.tgo.json --round 1
```

Expected checks:

- the correction is recorded in the audit trail;
- downstream rounds are removed and rebuilt deterministically;
- a regeneration does not silently change player count, seeds, or prior-round
  records.

Print the pairing, result, and standings pages after the round is settled and
inspect the browser print preview for each one. PDF export should not be added
or accepted during this stage.

## Backup and recovery observations

Before each mutation window, copy the tournament file to a backup path. During
automated simulations, restoring a copied `.tgo.json` file reproduced the same
round history, standings, and export output as the saved checkpoint.

Check the restored file for:

- identical player count and seed order;
- identical completed-round count;
- intact audit history for generation, entry, correction, and regeneration;
- identical CSV export availability.

This is still a checkpoint observation from automated simulations. Use the
human field trial to validate real operational recovery with the tournament
director present.

## Post-event export and standings checks

After the final round:

- export the players, pairings, results, and standings CSVs;
- confirm the expected headers are present in each export;
- confirm the final standings include all 32 players exactly once;
- confirm the final order is stable after a save/reload cycle;
- archive the finished `.tgo.json` file together with the exports.

## Structured feedback table

Use one row per observation during the field trial. The table below captures
both automated checkpoints and any later live-trial findings.

| Severity | Workflow step | Expected | Observed | Workaround | Evidence |
| --- | --- | --- | --- | --- | --- |
| Low | Sample import | 32-player roster imports with metadata intact | Automated simulations confirmed the realistic fixture and persistence path | None needed so far | `MAINTENANCE.md` 2026-06-25 entry |
| Low | Round generation and completion | Five deterministic rounds complete without repeat surprises | Automated Swiss and McMahon simulations completed with no-repeat checks and stable outputs | None needed so far | `MAINTENANCE.md` 2026-06-25 entry |
| Medium | Print preview | Pairing, result, and standings pages print cleanly from the browser | Print-friendly pages are in place, but the human print-layout trial is still pending | Use browser print preview and note any clipping or layout drift | `docs/roadmap.md` and `MAINTENANCE.md` |
| Low | Backup recovery | Restoring a copied tournament file reproduces the saved checkpoint | Restored checkpoints matched the saved simulation state in automated verification | Restore from the last known good `.tgo.json` copy | `MAINTENANCE.md` 2026-06-25 entry |

## Explicit non-goals

- PDF generation
- multi-user or networked operation
- manual pairing override records
- withdrawal handling
- late entry handling

Keep the trial focused on a single director using a single local process.
Anything outside the items above belongs in a future product decision, not in
the trial procedure.
