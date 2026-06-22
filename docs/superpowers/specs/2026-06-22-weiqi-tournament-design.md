# Weiqi Tournament Pairing Software Design

## Goal

Build an open-source tournament pairing application for Weiqi/Go and related board games, starting with a correctness-first Swiss pairing MVP. The system should keep the pairing engine independent from storage and UI, make pairing decisions explainable, and support practical tournament director workflows such as CSV import, manual adjustment, result entry, standings, exports, and audit trails.

## MVP Scope

The first prototype will support individual Swiss tournaments for Weiqi/Go.

Included:

- Create and save a tournament file.
- Import players from CSV.
- Use manually entered dan/kyu ranks as the initial strength signal.
- Configure basic Swiss tournament settings.
- Generate round pairings.
- Enter results.
- Generate standings.
- Export pairings, results, and standings to CSV.
- Export printable pairing and result sheets to PDF.
- Allow manual pairing adjustments with clear warnings.
- Record audit events and pairing explanations.

Deferred:

- McMahon pairing.
- Team tournaments.
- Knockout and round-robin.
- External ratings APIs, including future Singapore Weiqi Association integrations.
- Multi-user editing.
- Online tournament hosting.
- Full desktop packaging.

## Technology Stack

The recommended first stack is Python with a CLI and a local JSON tournament file.

- Language: Python 3.12 or newer.
- Package/test tooling: `pytest`, `hypothesis`, and standard `unittest.mock` where useful.
- Data validation: Python dataclasses first; add Pydantic only if validation complexity becomes painful.
- Pairing optimization: start with deterministic rule-based/greedy Swiss logic, then introduce `networkx` weighted matching when the simple algorithm reaches its limits.
- Storage: single JSON tournament file as the canonical MVP save format.
- Import/export: CSV via Python standard library.
- PDF: initially simple report generation through a small dependency selected during implementation.
- UI: CLI first; later local web UI with FastAPI plus React, optionally wrapped with Tauri.

JSON is preferred over XML for the MVP because it is built into Python, easy to diff, easy to test, and naturally represents nested tournament data. CSV remains first-class for player import and report export, but it should not be the canonical save format because tournament state contains nested rounds, games, corrections, configuration, manual overrides, and audit history.

Recommended save extension: `.tgo.json`.

## Research Lessons

Swiss-system pairing pairs players with similar current scores while avoiding repeat opponents. Chess Swiss rules, especially FIDE Dutch-system concepts, are useful because they distinguish hard criteria from quality criteria, use score groups, track floaters, define bye rules, and treat colour assignment as a fairness concern.

McMahon is especially important for future Go support because players begin with initial points based on strength, reducing severe early mismatches. It should be added after the Swiss engine is tested because it can reuse most infrastructure: standings, score groups, constraints, pairings, explanations, byes, and audit logs.

Weighted matching is a strong future direction. A graph can represent players as nodes and legal pairings as edges, with edge weights encoding penalties for poor rank proximity, colour imbalance, repeated float patterns, and affiliation conflicts. For MVP, simpler deterministic Swiss logic is acceptable, but the architecture should leave room for a matching-based optimizer.

Existing tournament tools show the value of full tournament workflows, but the new application should avoid hiding assumptions. Configuration, warnings, pairing reasons, and recalculation effects should be visible.

## Core Domain Model

### Tournament

Represents a complete tournament.

Fields:

- `id`
- `name`
- `game_type`
- `format`
- `status`
- `created_at`
- `updated_at`
- `schema_version`
- `config`
- `players`
- `rounds`
- `audit_log`

### TournamentConfig

Captures rules and settings that affect scoring, pairing, output, and validation.

Fields:

- `round_count`
- `pairing_method`
- `score_win`
- `score_loss`
- `score_draw`
- `score_bye`
- `allow_draws`
- `rank_system`
- `colour_policy`
- `bye_policy`
- `handicap_policy`
- `affiliation_policy`
- `tiebreak_order`
- `random_seed`

Initial assumptions:

- `pairing_method` is `swiss`.
- `rank_system` is manual dan/kyu.
- `score_win` is 1.
- `score_loss` is 0.
- Draws are disabled by default.

### Player

Represents an individual participant.

Fields:

- `id`
- `display_name`
- `rank`
- `rank_sort_value`
- `country`
- `club`
- `school`
- `team_id`
- `status`
- `seed_number`
- `notes`

`rank_sort_value` normalizes ranks so the engine can compare players. For example, stronger dan ranks sort above weaker dan ranks, and all dan ranks sort above kyu ranks. The exact conversion must be documented and tested.

### Team

Included in the model early but not active in the MVP pairing workflow.

Fields:

- `id`
- `name`
- `club`
- `school`
- `country`
- `member_player_ids`

### Round

Represents one tournament round.

Fields:

- `number`
- `status`
- `generated_at`
- `pairing_seed`
- `pairing_method`
- `pairing_config_hash`
- `games`
- `explanation_summary`

Statuses:

- `draft`
- `published`
- `completed`
- `stale`

### Game

Represents a board assignment and result container.

Fields:

- `id`
- `round_number`
- `board_number`
- `black_player_id`
- `white_player_id`
- `handicap`
- `komi`
- `result`
- `pairing_explanation`
- `manual_override_id`

### Result

Represents the outcome of a game.

Fields:

- `status`
- `winner_player_id`
- `black_score`
- `white_score`
- `result_type`
- `entered_at`
- `entered_by`
- `correction_of`

Result types:

- `normal`
- `forfeit`
- `bye`
- `no_show`
- `void`

### PairingConstraint

Represents a hard rule or soft preference.

Fields:

- `id`
- `name`
- `severity`
- `weight`
- `scope`
- `enabled`
- `description`

Severity values:

- `hard`
- `soft`
- `warning`

### TieBreakRule

Represents a standings tie-break calculation.

Initial supported rules:

- Total score.
- Number of wins.
- SOS.
- SOSOS.
- Direct encounter, where applicable.

SODOS and McMahon score should be added with McMahon support.

### AuditLogEntry

Append-only event record.

Fields:

- `id`
- `timestamp`
- `event_type`
- `actor`
- `round_number`
- `summary`
- `details`
- `state_hash_before`
- `state_hash_after`

Important event types:

- `tournament_created`
- `players_imported`
- `config_changed`
- `round_pairings_generated`
- `result_entered`
- `result_corrected`
- `manual_override_applied`
- `round_marked_stale`
- `export_generated`

### ManualOverrideRecord

Captures human changes to engine-generated pairings.

Fields:

- `id`
- `timestamp`
- `round_number`
- `before_games`
- `after_games`
- `warnings`
- `director_note`

## Save File Design

The canonical MVP save file is one JSON document.

Example shape:

```json
{
  "schema_version": 1,
  "tournament": {
    "id": "example",
    "name": "Example Weiqi Open",
    "game_type": "go",
    "format": "swiss",
    "status": "draft"
  },
  "config": {},
  "players": [],
  "teams": [],
  "rounds": [],
  "manual_overrides": [],
  "audit_log": []
}
```

The file should be written atomically: save to a temporary file in the same directory, then replace the original. The application should maintain a schema version and provide explicit migration functions when the format changes.

## Pairing Engine Architecture

The engine should be pure application logic with no dependency on file storage, UI, or PDF generation.

Interface:

```text
PairingMethod.generate(context, config) -> PairingProposal
PairingMethod.validate(proposal, context, config) -> ValidationReport
PairingMethod.explain(proposal, context, config) -> ExplanationReport
```

Core services:

- `StandingsCalculator`: computes score and tie-break values from completed rounds.
- `PairingHistory`: answers whether players have met, colour history, byes, floats, and withdrawals.
- `ScoreGroupBuilder`: groups players by current score.
- `ConstraintEvaluator`: evaluates hard constraints and soft penalties.
- `SwissPairingMethod`: creates Swiss pairings.
- `ColourAllocator`: assigns black/white while balancing colour history.
- `ByeAllocator`: selects the best bye candidate.
- `PairingExplainer`: produces human-readable reasons and warnings.
- `AuditTrailBuilder`: creates audit entries from commands and pairing output.

## Swiss Pairing MVP

The first Swiss implementation should be deterministic and explainable.

Process:

1. Select active players for the round.
2. Compute standings.
3. Sort players by score, then rank strength, then seed number, then stable player id.
4. Build score groups.
5. Pair within score groups where possible.
6. Float unpaired players to adjacent lower score groups.
7. Avoid repeated opponents as a hard rule where possible.
8. Assign a bye if there is an odd number of players.
9. Allocate colours.
10. Assign board numbers by score group and rank strength.
11. Produce explanations and warnings.

Hard constraints:

- A player may appear in at most one game per round.
- Withdrawn players are not paired.
- Repeated opponents are disallowed unless the director explicitly accepts an unavoidable-repeat warning.
- A player should not receive a second full-point pairing bye.

Soft constraints:

- Prefer similar scores.
- Prefer similar ranks within score groups.
- Avoid same school/club pairings where possible.
- Balance colour count.
- Avoid three same colours in a row.
- Avoid repeated floating patterns.

The MVP does not need to implement full FIDE Dutch compliance. It should borrow useful concepts, especially score groups, floaters, byes, hard-vs-soft criteria, and colour preferences.

## Manual Overrides

Manual overrides are allowed, but never silent.

Workflow:

1. Director edits a draft round.
2. Engine validates the edited pairings.
3. UI/CLI shows warnings and hard violations.
4. Hard violations require explicit confirmation and a director note.
5. The accepted override records before/after pairings, warnings, and note.
6. Standings and audit logs refer to the accepted pairing state.

Examples of warnings:

- Players have already met.
- Same school pairing could have been avoided.
- Player receives third black/white in a row.
- Rank difference is unusually large.
- Player receives a second bye.

## Result Correction and Stale Rounds

Result correction can affect standings and therefore later pairings.

Rules:

- Correcting a result updates the affected game and appends a correction event.
- If later rounds already exist, mark those rounds as `stale`.
- The director may keep later rounds as manually accepted history or recalculate from a chosen round.
- Recalculation should use the stored config and seed unless the director explicitly changes them.

## Import and Export

### Player CSV Import

Initial columns:

- `name`
- `rank`
- `country`
- `club`
- `school`
- `team`
- `notes`

Import should report:

- Missing names.
- Invalid ranks.
- Duplicate names.
- Unknown columns.
- Rows imported with warnings.

### CSV Exports

Supported exports:

- Players.
- Pairings by round.
- Results by round.
- Standings.
- Audit log.

### PDF Exports

Initial PDFs:

- Pairing sheet.
- Result entry sheet.
- Standings sheet.

PDF layout should be plain and reliable before it is pretty.

## Future McMahon Design

McMahon should reuse the same engine infrastructure.

Additional config:

- `upper_bar_rank`
- `lower_bar_rank`
- `initial_score_by_rank`
- `mcm_score_policy`
- `handicap_policy`

Additional behavior:

- Compute initial McMahon score from manual rank.
- Pair by current McMahon score.
- Show initial score and game score separately.
- Include McMahon score in standings.
- Add Go-common tie-breaks such as SOS, SOSOS, and SODOS.

## Project Structure

```text
pairwise-go/
  pyproject.toml
  README.md
  docs/
    architecture.md
    csv-format.md
    pairing-rules.md
    superpowers/
      specs/
        2026-06-22-weiqi-tournament-design.md
  src/
    pairing/
      __init__.py
      domain/
        __init__.py
        audit.py
        config.py
        game.py
        player.py
        result.py
        round.py
        tournament.py
      engine/
        __init__.py
        base.py
        bye.py
        colours.py
        constraints.py
        explanations.py
        history.py
        standings.py
        swiss.py
        tiebreaks.py
      storage/
        __init__.py
        json_store.py
        migrations.py
      import_export/
        __init__.py
        csv_import.py
        csv_export.py
        pdf_export.py
      cli/
        __init__.py
        main.py
  tests/
    unit/
    property/
    regression/
    fixtures/
```

## Roadmap

### Stage 0: Research and Requirements

- Finalize MVP assumptions.
- Document rank conversion.
- Document Swiss pairing principles.
- Define JSON schema version 1.
- Define CSV import format.

### Stage 1: Data Model and CLI Prototype

- Create package skeleton.
- Implement domain models.
- Implement JSON save/load.
- Implement tournament creation command.
- Implement player CSV import command.

### Stage 2: Swiss Pairing

- Implement standings calculation.
- Implement round 1 pairing.
- Implement later-round Swiss pairing.
- Implement bye allocation.
- Implement colour assignment.
- Implement pairing explanations.

### Stage 3: McMahon Pairing

- Add initial McMahon score from rank.
- Add upper/lower bar settings.
- Add McMahon standings.
- Add SODOS and McMahon-specific explanations.

### Stage 4: Simple UI

- Build local web UI.
- Show tournament setup, player list, pairings, results, standings, and audit log.
- Keep engine API independent from UI.

### Stage 5: Import/Export and Real Tournament Testing

- Harden CSV import/export.
- Add PDF pairing/result/standing sheets.
- Test with realistic tournament fixtures.
- Collect tournament director feedback.

### Stage 6: Advanced Features

- Team events.
- Round-robin and knockout.
- Friendly exchange matches.
- External rank/rating APIs.
- Matching or integer-programming optimizer.
- Advanced repair workflows.

## Edge Cases and Failure Modes

- Odd number of players.
- No legal bye candidate under strict rules.
- Repeated opponent unavoidable.
- Same school avoidance impossible.
- Many players with identical ranks and scores.
- Player withdraws after pairings are published.
- Player re-enters after missed rounds.
- Late entry after round 1.
- Result correction after later rounds exist.
- Manual override creates worse pairing.
- Rank parsing ambiguity such as `1 dan`, `1d`, `shodan`, `1 kyu`, `1k`.
- Unranked players.
- Colour imbalance over many rounds.
- Pairing reproducibility across software versions.
- Export generated from stale rounds.
- Tournament file edited by hand with invalid references.

## Testing Strategy

Unit tests:

- Rank parsing and normalization.
- Player import validation.
- Score calculation.
- Tie-break calculation.
- Colour history.
- Bye eligibility.
- JSON save/load round trips.

Property-based tests:

- Every active player appears at most once per round.
- No inactive player is paired.
- Even active player count produces no bye.
- Odd active player count produces exactly one bye.
- Same input, config, and seed produce same pairings.

Regression tests:

- Small known tournaments with expected pairings.
- Scenarios with repeated-opponent pressure.
- Scenarios with same-school pressure.
- Result correction scenarios.

Simulation tests:

- Generate many random tournaments and assert invariants after each round.
- Simulate withdrawals, late entries, and corrections.

Explanation tests:

- Every soft penalty in a selected pairing appears in the explanation.
- Every manual override warning is understandable and tied to a rule.
- Unavoidable constraint violations state why they were unavoidable.

## Recommended Architecture Diagram

```text
CLI / Future Local Web UI
    |
Application Commands
    |-- create tournament
    |-- import players
    |-- generate pairings
    |-- enter results
    |-- export reports
    |
Core Domain Model
    |-- Tournament
    |-- Player / Team
    |-- Round / Game / Result
    |-- Config / Constraints / TieBreaks
    |-- Audit Log / Manual Overrides
    |
Pairing Engine
    |-- Swiss Pairing Method
    |-- Future McMahon Pairing Method
    |-- Standings Calculator
    |-- Constraint Evaluator
    |-- Colour Allocator
    |-- Bye Allocator
    |-- Explanation Builder
    |
Persistence
    |-- JSON Tournament Store
    |-- Schema Migrations
    |-- Atomic Save
    |
Import / Export
    |-- CSV Import
    |-- CSV Export
    |-- PDF Export
```

## Initial GitHub Issues

1. Create Python project skeleton and test setup.
2. Define domain models for tournament, player, round, game, result, config, and audit log.
3. Implement JSON tournament save/load with schema version 1.
4. Implement dan/kyu rank parser and normalization.
5. Implement player CSV import with validation report.
6. Implement tournament creation CLI command.
7. Implement standings calculator.
8. Implement Swiss round 1 pairing.
9. Implement Swiss later-round pairing with no-repeat checks.
10. Implement bye allocation.
11. Implement colour history and colour assignment.
12. Implement pairing explanation reports.
13. Implement manual override validation.
14. Implement result entry and correction.
15. Implement stale-round marking after corrections.
16. Implement CSV exports for pairings, results, and standings.
17. Implement simple PDF pairing and result sheets.
18. Add property-based pairing invariant tests.
19. Add regression fixtures for difficult pairing scenarios.
20. Document MVP tournament workflow.

## First Three Coding Tasks

1. Create the Python package skeleton, test setup, domain models, and JSON tournament save/load.
2. Implement dan/kyu rank parsing plus CSV player import with validation.
3. Implement Swiss pairing for round 1 and later rounds, including no-repeat checks, byes, colour assignment, and explanations.

## Open Clarifications

The design assumes Japanese-style dan/kyu notation for MVP input, accepting compact forms such as `3d` and `5k`. More localized rank labels can be added after the parser has a tested baseline.

The design assumes individual tournaments first. Team fields are allowed on players and in the save format, but team pairing behavior is deferred.

The design assumes JSON is the canonical save format. CSV remains an exchange/report format, not the source of truth.
