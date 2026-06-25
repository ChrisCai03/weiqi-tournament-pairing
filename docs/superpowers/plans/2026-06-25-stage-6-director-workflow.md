# Stage 6 Tournament Director Workflow Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver an OpenGotha-inspired, auditable single-director workflow with per-round participation, rich results, operations visibility, validated pairing repair, and recoverable backups.

**Architecture:** Implement four independently releasable slices. Persist new optional schema-v1 fields with compatibility defaults, keep scoring/history pure, route all mutations through focused application services, and expose the same operations through CLI and server-rendered web adapters.

**Tech Stack:** Python 3.12, dataclasses, JSON, WSGI, pytest, Hypothesis, Ruff, mypy.

---

## File Structure

### Slice 6A

- `src/pairing/domain/participation.py`: typed per-round participation records.
- `src/pairing/domain/result.py`: persisted outcome code and score pair.
- `src/pairing/domain/config.py`: rich scoring and late-entry defaults.
- `src/pairing/domain/tournament.py`: compatibility serialization and aggregate result/participation commands.
- `src/pairing/engine/scoring.py`: pure result counter and game-score semantics.
- `src/pairing/engine/history.py`: played/void encounter policy.
- `src/pairing/engine/standings.py`: score-pair-driven standings.
- `src/pairing/engine/round_generation.py`: eligible-player selection.
- `src/pairing/application/participation.py`: participation workflows.
- `src/pairing/application/outcomes.py`: rich result workflows.
- `src/pairing/application/service.py`: compatibility facade.
- `src/pairing/cli/main.py`: participation and outcome commands.
- `src/pairing/import_export/csv_export.py`: outcome-aware result exports.
- `tests/unit/test_participation.py`: participation policy tests.
- `tests/unit/test_result_outcomes.py`: outcome scoring tests.
- `tests/integration/test_stage6_workflows.py`: persisted Slice 6A workflows.

### Slice 6B

- `src/pairing/application/round_operations.py`: derived operations projection.
- `src/pairing/web/routes.py`: quick-check, audit, and operations routes.
- `src/pairing/web/views.py`: dashboard, quick-check, audit, and rich result controls.
- `src/pairing/web/forms.py`: rich outcome and participation parsing.
- `src/pairing/cli/main.py`: `quick-check` and `audit`.
- `tests/unit/test_round_operations.py`: projection tests.
- `tests/unit/test_web_stage6.py`: web workflow tests.

### Slice 6C

- `src/pairing/domain/override.py`: typed manual override records.
- `src/pairing/engine/repair.py`: pure preview, validation, and warning generation.
- `src/pairing/application/repair.py`: accepted repair workflows.
- `src/pairing/web/routes.py`: preview/accept repair endpoints.
- `src/pairing/web/views.py`: pending-game repair controls.
- `src/pairing/cli/main.py`: repair commands.
- `tests/unit/test_pairing_repair.py`: repair validation tests.
- `tests/integration/test_stage6_repairs.py`: persisted repair/audit tests.

### Slice 6D

- `src/pairing/application/backups.py`: snapshot, retention, listing, restore.
- `src/pairing/application/service.py`: backup facade and destructive-operation hooks.
- `src/pairing/cli/main.py`: backup commands.
- `src/pairing/web/routes.py`: backup listing/create/restore endpoints.
- `src/pairing/web/views.py`: recovery UI.
- `tests/unit/test_backups.py`: safe snapshot/restore tests.
- `tests/integration/test_stage6_tournament_trial.py`: realistic workflow trial.
- `README.md`, `PROJECT_CONTEXT.md`, `MAINTENANCE.md`, `docs/roadmap.md`, `docs/tournament-trial-runbook.md`: final handoff.

## Slice 6A: Participation and Rich Results

### Task 1: Persist configurable rich result outcomes

**Files:**
- Modify: `src/pairing/domain/validation.py`
- Modify: `src/pairing/domain/config.py`
- Modify: `src/pairing/domain/result.py`
- Create: `src/pairing/engine/scoring.py`
- Modify: `src/pairing/domain/game.py`
- Test: `tests/unit/test_result_outcomes.py`
- Test: `tests/unit/test_domain_serialization.py`

- [ ] Write failing tests for legacy normal/bye deserialization and every new outcome code.
- [ ] Verify RED with `python -m pytest tests/unit/test_result_outcomes.py tests/unit/test_domain_serialization.py -q`.
- [ ] Add configuration defaults from the design and validate finite numeric scores and positive backup retention.
- [ ] Add `Result.completed_outcome(...)` that resolves a supported outcome code to result type, winner, black/white score, and timestamp.
- [ ] Preserve `Result.completed(...)` as a normal-win compatibility constructor.
- [ ] Normalize legacy results lacking score fields during `from_dict`.
- [ ] Run focused tests and `python -m ruff check` on changed files.
- [ ] Commit `Add configurable tournament result outcomes`.

### Task 2: Score standings and history from persisted outcomes

**Files:**
- Modify: `src/pairing/engine/scoring.py`
- Modify: `src/pairing/engine/standings.py`
- Modify: `src/pairing/engine/history.py`
- Modify: `src/pairing/import_export/csv_export.py`
- Test: `tests/unit/test_result_outcomes.py`
- Test: `tests/unit/test_standings.py`
- Test: `tests/unit/test_swiss_pairing.py`

- [ ] Write failing tests proving both-win adds a win and configured score to both players.
- [ ] Write failing tests proving both-loss adds a loss and configured score to both players.
- [ ] Write failing tests proving both cases count once for opponent history and SOS.
- [ ] Write failing tests proving void contributes no points, encounter, colour history, or SOS.
- [ ] Verify each test fails for missing semantics.
- [ ] Implement pure `player_game_contribution(game, player_id)` and `counts_as_played(result)`.
- [ ] Make standings and history consume those helpers.
- [ ] Add draws to `StandingEntry` and outcome/score columns to result CSV.
- [ ] Run focused pairing/standings/export tests.
- [ ] Commit `Score standings from persisted result outcomes`.

### Task 3: Persist per-round participation

**Files:**
- Create: `src/pairing/domain/participation.py`
- Modify: `src/pairing/domain/tournament.py`
- Modify: `src/pairing/domain/player.py`
- Modify: `src/pairing/domain/__init__.py`
- Test: `tests/unit/test_participation.py`
- Test: `tests/unit/test_domain_serialization.py`

- [ ] Write failing tests for default participation, withdrawal, absence, re-entry, and late-entry records.
- [ ] Verify RED.
- [ ] Implement `ParticipationRecord` validation/serialization.
- [ ] Add optional `participation` to the tournament aggregate and schema-v1 dictionary.
- [ ] Implement `participation_status(player_id, round_number)` and `eligible_players(round_number)`.
- [ ] Normalize missing records from legacy files without materializing unnecessary entries.
- [ ] Reject unknown players, invalid rounds, duplicate player/round records, and non-finite adjustments.
- [ ] Run focused tests.
- [ ] Commit `Add per-round participation records`.

### Task 4: Add participation and outcome application workflows

**Files:**
- Create: `src/pairing/application/participation.py`
- Create: `src/pairing/application/outcomes.py`
- Modify: `src/pairing/application/results.py`
- Modify: `src/pairing/application/service.py`
- Modify: `src/pairing/engine/round_generation.py`
- Modify: `src/pairing/engine/swiss.py`
- Modify: `src/pairing/engine/mcmahon.py`
- Test: `tests/unit/test_application_service.py`
- Test: `tests/integration/test_stage6_workflows.py`

- [ ] Write failing persisted tests for withdraw-from-round, one-round absence, re-entry, and late entry.
- [ ] Write failing tests that ineligible players are excluded from generated rounds.
- [ ] Write failing tests for `record_outcome` and `correct_outcome`, including downstream invalidation.
- [ ] Verify RED.
- [ ] Implement focused services using load/validate/mutate/audit/save.
- [ ] Delegate from `TournamentService` and retain old normal-win wrappers.
- [ ] Make round generation consume `eligible_players(next_round_number)`.
- [ ] Reject participation changes contradicting completed games.
- [ ] Audit effective round, reason, adjustment, outcome code, and score pair.
- [ ] Run focused unit/integration tests.
- [ ] Commit `Add audited participation and outcome workflows`.

### Task 5: Expose Slice 6A through the CLI

**Files:**
- Modify: `src/pairing/cli/main.py`
- Test: `tests/unit/test_cli.py`
- Test: `tests/integration/test_stage6_workflows.py`

- [ ] Write failing parser/workflow tests for `withdraw`, `reenter`, `set-participation`, `late-entry`, `enter-outcome`, and `correct-outcome`.
- [ ] Verify RED.
- [ ] Add stable player-ID arguments and explicit reason/effective-round options.
- [ ] Print typed outcomes and warnings without duplicating service rules.
- [ ] Run CLI and Stage 6 integration tests.
- [ ] Run full quality gates for Slice 6A.
- [ ] Commit `Expose Stage 6 participation and outcomes`.

## Slice 6B: Operations Dashboard

### Task 6: Derive truthful round operations status

**Files:**
- Create: `src/pairing/application/round_operations.py`
- Modify: `src/pairing/application/results.py`
- Modify: `src/pairing/application/service.py`
- Test: `tests/unit/test_round_operations.py`

- [ ] Write failing projection tests for future, active, partial-result, completed, and blocked rounds.
- [ ] Verify RED.
- [ ] Implement the design's `RoundOperationsStatus` fields as a read-only projection.
- [ ] Include actionable blocker/warning messages.
- [ ] Expose `TournamentService.round_operations()`.
- [ ] Run focused tests and commit `Add round operations status projection`.

### Task 7: Add quick-check, rich result, and audit web workflows

**Files:**
- Modify: `src/pairing/web/forms.py`
- Modify: `src/pairing/web/routes.py`
- Modify: `src/pairing/web/views.py`
- Modify: `src/pairing/cli/main.py`
- Test: `tests/unit/test_web_stage6.py`
- Test: `tests/unit/test_cli.py`

- [ ] Write failing route and CLI tests for operations, quick check, audit, and rich outcome entry.
- [ ] Verify RED.
- [ ] Add `/operations`, `/quick-check`, and `/audit` views.
- [ ] Add POST participation and outcome routes calling services.
- [ ] Add `quick-check` and `audit` CLI rendering.
- [ ] Show score pairs and correction/invalidation warnings.
- [ ] Run focused and full gates.
- [ ] Commit `Add tournament director operations dashboard`.

## Slice 6C: Pairing Repair

### Task 8: Model and validate manual repairs

**Files:**
- Create: `src/pairing/domain/override.py`
- Create: `src/pairing/engine/repair.py`
- Modify: `src/pairing/domain/tournament.py`
- Test: `tests/unit/test_pairing_repair.py`
- Test: `tests/unit/test_domain_serialization.py`

- [ ] Write failing tests for typed legacy normalization and all hard violations.
- [ ] Write failing warning tests for repeat, score gap, colour imbalance, affiliation, and second bye.
- [ ] Verify RED.
- [ ] Implement immutable repair proposals and typed override records.
- [ ] Implement swap, colour exchange, board move, bye replacement, and pending regeneration previews.
- [ ] Require notes only when warnings are accepted.
- [ ] Run focused tests and commit `Validate manual pairing repairs`.

### Task 9: Persist accepted repairs and expose controls

**Files:**
- Create: `src/pairing/application/repair.py`
- Modify: `src/pairing/application/service.py`
- Modify: `src/pairing/cli/main.py`
- Modify: `src/pairing/web/routes.py`
- Modify: `src/pairing/web/views.py`
- Test: `tests/integration/test_stage6_repairs.py`
- Test: `tests/unit/test_web_stage6.py`

- [ ] Write failing preview/accept integration tests including stale-state rejection.
- [ ] Verify RED.
- [ ] Persist accepted before/after games, warnings, note, actor, and audit event.
- [ ] Add CLI and web preview/accept actions.
- [ ] Prevent mutation of completed games.
- [ ] Run focused and full gates.
- [ ] Commit `Add audited manual pairing repair workflow`.

## Slice 6D: Recovery and Trial

### Task 10: Add validated backup snapshots

**Files:**
- Create: `src/pairing/application/backups.py`
- Modify: `src/pairing/application/service.py`
- Modify: `src/pairing/cli/main.py`
- Modify: `src/pairing/web/routes.py`
- Modify: `src/pairing/web/views.py`
- Test: `tests/unit/test_backups.py`

- [ ] Write failing tests for snapshot naming, hash, retention, listing, and restore-to-new-file.
- [ ] Verify RED.
- [ ] Create snapshots before destructive workflows and block mutation on backup failure.
- [ ] Validate restored files and never overwrite the active file.
- [ ] Add CLI/web create, list, and restore.
- [ ] Run focused tests and commit `Add tournament backup and recovery workflow`.

### Task 11: Extend realistic Stage 6 trial and documentation

**Files:**
- Create: `tests/integration/test_stage6_tournament_trial.py`
- Modify: `README.md`
- Modify: `PROJECT_CONTEXT.md`
- Modify: `MAINTENANCE.md`
- Modify: `docs/roadmap.md`
- Modify: `docs/tournament-trial-runbook.md`
- Modify: `docs/tournament-file-format.md`

- [ ] Write a failing realistic trial covering late entry, withdrawal/re-entry, absence, both-win, both-loss, accepted repair, correction/regeneration, and restore.
- [ ] Verify RED.
- [ ] Add only implementation fixes required by the trial.
- [ ] Update supported/reserved contracts and operator instructions.
- [ ] Run all quality gates and record exact evidence.
- [ ] Commit `Complete Stage 6 director workflow trial`.

### Task 12: Final review and resumable handoff

- [ ] Request specification review of the full branch.
- [ ] Resolve and re-review every Critical or Important finding.
- [ ] Request code-quality review of the full branch.
- [ ] Re-run Ruff format/lint, mypy, compileall, full pytest with coverage, and `git diff --check`.
- [ ] Confirm the worktree is clean and every slice ends in a commit.
- [ ] Commit final maintenance evidence as `Record Stage 6 verification`.

