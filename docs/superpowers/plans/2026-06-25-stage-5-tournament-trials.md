# Stage 5 Tournament Trials Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Exercise the rehabilitated application with realistic rosters and complete deterministic tournaments, then document a repeatable tournament-director trial process.

**Architecture:** Keep trial data and simulation helpers in the test tree so production APIs remain focused. Drive every simulated event through `TournamentService` and the schema-versioned JSON store, checking pairing invariants, persistence, audit history, completion, and report exports after multiple rounds. Record the operational trial procedure in documentation rather than adding premature PDF or multi-user behavior.

**Tech Stack:** Python 3.12, pytest, existing domain/application/storage/import-export modules, CSV and JSON fixtures.

---

## File Structure

- `tests/fixtures/players/realistic-open.csv`: realistic mixed-rank, mixed-affiliation roster used by trial tests.
- `tests/integration/test_tournament_trials.py`: deterministic Swiss and McMahon full-event simulations and reusable invariant helpers.
- `docs/tournament-trial-runbook.md`: manual trial procedure and structured director feedback form.
- `docs/roadmap.md`: Milestone C progress and the next product decision.
- `PROJECT_CONTEXT.md`: current supported baseline and continuation guidance.
- `MAINTENANCE.md`: dated implementation and verification record.

### Task 1: Add the realistic roster fixture

**Files:**
- Create: `tests/fixtures/players/realistic-open.csv`
- Create: `tests/integration/test_tournament_trials.py`

- [ ] **Step 1: Write the failing fixture-loading test**

Add a test that imports `tests/fixtures/players/realistic-open.csv` into a new tournament through `TournamentService.import_players_file`. Assert that 32 players are imported, seeds are unique and ordered, dan/kyu/unranked players are represented, and country, club, and school metadata survive persistence.

- [ ] **Step 2: Run the focused test to verify RED**

Run:

```powershell
python -m pytest tests/integration/test_tournament_trials.py::test_realistic_roster_imports_with_affiliation_metadata -q
```

Expected: FAIL because the fixture does not exist.

- [ ] **Step 3: Add the CSV fixture**

Create a 32-player roster with the documented columns:

```csv
name,rank,country,club,school,team,notes
```

Use unique names, a realistic spread from `5d` to `15k` plus two unranked players, and several repeated clubs/schools so future affiliation-aware work has useful regression data. Do not add malformed rows; import validation already has focused unit tests.

- [ ] **Step 4: Run the focused test to verify GREEN**

Run:

```powershell
python -m pytest tests/integration/test_tournament_trials.py::test_realistic_roster_imports_with_affiliation_metadata -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

```powershell
git add tests/fixtures/players/realistic-open.csv tests/integration/test_tournament_trials.py
git commit -m "Add realistic tournament roster fixture"
```

### Task 2: Simulate complete Swiss and McMahon events

**Files:**
- Modify: `tests/integration/test_tournament_trials.py`

- [ ] **Step 1: Add shared invariant helpers**

Add test-only helpers that:

- complete pending games with a deterministic alternating black/white winner policy;
- assert every player appears exactly once per round, including a bye recipient;
- assert board numbers are consecutive;
- assert no player receives more than one pairing bye;
- reload the `.tgo.json` file after every mutation;
- verify generated CSV pairings, results, and standings reports are non-empty.

- [ ] **Step 2: Add the five-round Swiss trial**

Import the 32-player fixture, generate and complete five rounds through `TournamentService`, and assert:

- all five rounds are completed;
- each round contains 16 games and no bye;
- the final standings contain all 32 players;
- generation and result-entry audit counts match the event;
- saving and loading preserve the final tournament exactly;
- all supported CSV report exports contain their expected headers.

- [ ] **Step 3: Run the Swiss trial**

Run:

```powershell
python -m pytest tests/integration/test_tournament_trials.py::test_complete_realistic_five_round_swiss_trial -q
```

Expected: PASS, or a reproducible failure exposing a production defect. If a defect appears, stop this task and use `superpowers:systematic-debugging` before changing production code.

- [ ] **Step 4: Add the five-round McMahon trial**

Run the same roster as a simplified McMahon event and assert:

- all generated rounds identify `mcmahon` as their pairing method;
- all rounds complete and persist;
- standings retain separate starting and game scores;
- the strongest ranked players begin with scores no lower than the weakest ranked players;
- report exports remain available after the complete event.

- [ ] **Step 5: Run the McMahon trial and full integration directory**

Run:

```powershell
python -m pytest tests/integration/test_tournament_trials.py -q
python -m pytest tests/integration -q
```

Expected: PASS.

- [ ] **Step 6: Commit**

```powershell
git add tests/integration/test_tournament_trials.py
git commit -m "Exercise complete realistic tournament trials"
```

### Task 3: Publish the tournament trial runbook and handoff state

**Files:**
- Create: `docs/tournament-trial-runbook.md`
- Modify: `docs/roadmap.md`
- Modify: `PROJECT_CONTEXT.md`
- Modify: `MAINTENANCE.md`
- Modify: `README.md`

- [ ] **Step 1: Write the trial runbook**

Document:

- prerequisites and sample-event creation;
- roster import and pre-round checks;
- round generation, printing, result entry, correction, and regeneration checks;
- backup and recovery observations;
- a structured feedback table covering severity, workflow step, expected behavior, observed behavior, workaround, and evidence;
- explicit non-goals: PDF generation, multi-user use, manual overrides, withdrawals, and late entry.

- [ ] **Step 2: Refresh roadmap and context**

Mark realistic regression fixtures and larger deterministic simulations complete in Milestone C. Keep PDF deferred until manual print-layout trials are complete. Name the next product decision as either Tournament Director Essentials design work or a small corrective slice discovered during field trials.

- [ ] **Step 3: Add the maintenance entry and README link**

Record the fixture size, simulated formats and round counts, verification commands, and any limitations found. Link the trial runbook from the README documentation list.

- [ ] **Step 4: Verify documentation references**

Run:

```powershell
rg -n "tournament-trial-runbook|realistic|simulation|PDF" README.md PROJECT_CONTEXT.md MAINTENANCE.md docs/roadmap.md docs/tournament-trial-runbook.md
```

Expected: every new artifact and decision is represented consistently.

- [ ] **Step 5: Commit**

```powershell
git add README.md PROJECT_CONTEXT.md MAINTENANCE.md docs/roadmap.md docs/tournament-trial-runbook.md
git commit -m "Document repeatable tournament trial workflow"
```

### Task 4: Final review and verification

**Files:**
- Modify only files required by review findings.

- [ ] **Step 1: Run all quality gates**

```powershell
python -m ruff format --check .
python -m ruff check .
python -m mypy src/pairing
python -m compileall -q src
python -m pytest --cov=pairing --cov-report=term-missing -q
```

- [ ] **Step 2: Request final code review**

Give the reviewer the full plan, base SHA `63128fc`, branch head SHA, and ask for specification compliance followed by code quality review.

- [ ] **Step 3: Resolve and re-review all important findings**

Use the original implementer for task-local corrections. Re-run the affected focused tests and the complete quality gates before accepting the review.

- [ ] **Step 4: Record final verification**

Update `MAINTENANCE.md` with fresh test, lint, typing, compilation, and coverage evidence.

- [ ] **Step 5: Commit final handoff state**

```powershell
git add MAINTENANCE.md
git commit -m "Record Stage 5 tournament trial verification"
```

