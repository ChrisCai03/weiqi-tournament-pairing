# Repository Rehabilitation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rehabilitate the Stage 1–4 repository into a validated, test-driven local tournament application whose CLI and web UI share reliable workflows.

**Architecture:** Preserve the schema-v1 JSON model and pure pairing engine, add aggregate validation and a `pairing.application` service layer, then make CLI and WSGI adapters thin. Correct pairing progression, history, unavoidable-repeat, result-correction, and simplified McMahon contracts before expanding integration/property coverage and operational documentation.

**Tech Stack:** Python 3.12, standard-library dataclasses/JSON/CSV/argparse/WSGI, pytest, Hypothesis, Ruff, mypy, pytest-cov.

---

## File Structure

Create:

- `MAINTENANCE.md`: chronological maintenance decisions, verification, and known limitations.
- `docs/architecture.md`: current repository architecture and module contracts.
- `docs/roadmap.md`: post-rehabilitation product roadmap.
- `src/pairing/application/__init__.py`: public application-service exports.
- `src/pairing/application/service.py`: persisted tournament use cases.
- `src/pairing/application/results.py`: typed service outcomes.
- `src/pairing/domain/validation.py`: field constants and aggregate validation.
- `src/pairing/engine/pairing_result.py`: pairing outcome and warning types.
- `src/pairing/web/forms.py`: WSGI form decoding.
- `src/pairing/web/responses.py`: HTTP response helpers.
- `src/pairing/web/routes.py`: route table and request dispatch.
- `src/pairing/web/views.py`: server-rendered HTML.
- `tests/property/test_pairing_invariants.py`: generated Swiss/McMahon invariants.
- `tests/integration/test_tournament_workflows.py`: persisted multi-round workflows.
- `tests/integration/test_live_server.py`: real HTTP server lifecycle.
- `tests/unit/test_application_service.py`: service use cases and rollback.
- `tests/unit/test_domain_validation.py`: aggregate validation.
- `tests/unit/test_web_routing.py`: route and method semantics.

Modify:

- `pyproject.toml`: development tools and quality configuration.
- `README.md`: installation, CLI, demo, and web startup.
- `PROJECT_CONTEXT.md`: integration baseline and handoff.
- `docs/tournament-file-format.md`: complete schema-v1 contract.
- `docs/superpowers/specs/2026-06-24-repository-rehabilitation-design.md`: only if implementation proves a necessary correction.
- `src/pairing/cli/main.py`: thin service adapter and demo command.
- `src/pairing/domain/audit.py`: validated audit fields.
- `src/pairing/domain/config.py`: supported/reserved policy validation.
- `src/pairing/domain/game.py`: game validation.
- `src/pairing/domain/player.py`: player validation.
- `src/pairing/domain/result.py`: supported result and correction contract.
- `src/pairing/domain/round.py`: round validation and status consistency.
- `src/pairing/domain/tournament.py`: aggregate validation and correction behavior.
- `src/pairing/engine/bye.py`: accurate bye decisions.
- `src/pairing/engine/colours.py`: explicit penalty calculation.
- `src/pairing/engine/explanations.py`: format- and compromise-aware explanations.
- `src/pairing/engine/history.py`: pairing history includes pending games.
- `src/pairing/engine/mcmahon.py`: explicit simplified policy and warnings.
- `src/pairing/engine/pairing_core.py`: no-repeat and fallback search.
- `src/pairing/engine/round_generation.py`: typed generation result dispatch.
- `src/pairing/engine/swiss.py`: progression and repeat fallback.
- `src/pairing/import_export/csv_export.py`: active-round and typed lookup behavior.
- `src/pairing/storage/json_store.py`: validate-before-save and durable atomic replace.
- `src/pairing/web/app.py`: application assembly only.
- `src/pairing/web/server.py`: startup errors, URL, optional browser open.
- `tests/unit/test_cli.py`: service-backed CLI and demo behavior.
- `tests/unit/test_json_store.py`: malformed aggregate and atomic failure.
- `tests/unit/test_mcmahon_pairing.py`: expanded policy coverage.
- `tests/unit/test_standings.py`: pairing/result history separation.
- `tests/unit/test_swiss_pairing.py`: progression and repeat fallback.
- `tests/unit/test_web_app.py`: persisted web workflows.

## Task 1: Maintenance Baseline and Characterization Tests

**Files:**

- Create: `MAINTENANCE.md`
- Modify: `tests/unit/test_web_app.py`
- Modify: `tests/unit/test_swiss_pairing.py`
- Modify: `tests/unit/test_mcmahon_pairing.py`
- Create: `tests/integration/test_tournament_workflows.py`

- [ ] **Step 1: Write the maintenance baseline**

Create `MAINTENANCE.md` with:

```markdown
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
```

- [ ] **Step 2: Replace the false-positive web persistence assertion**

In `tests/unit/test_web_app.py`, import `load_tournament` and replace:

```python
saved = Tournament.from_dict(Tournament.create("Example Weiqi Open").to_dict())
assert tournament_path.exists()
```

with:

```python
saved = load_tournament(tournament_path)
assert [round_obj.number for round_obj in saved.rounds] == [1]
assert saved.rounds[0].pairing_method == "swiss"
```

- [ ] **Step 3: Add deterministic characterization assertions**

Add a Swiss test that records the ordered player-name pairs for a fixed eight-player first round, and a McMahon test that records the ordered pairs for fixed ranks around the bar. Assert exact names rather than only counts.

- [ ] **Step 4: Add a complete current-behavior persisted workflow**

Create `tests/integration/test_tournament_workflows.py`:

```python
from pairing.cli.main import main
from pairing.domain import Player, Tournament
from pairing.storage import load_tournament, save_tournament


def test_swiss_file_survives_create_pair_result_and_reload(tmp_path) -> None:
    path = tmp_path / "event.tgo.json"
    tournament = Tournament.create("Characterization Open", round_count=2)
    tournament.players.extend(
        [
            Player.create("Alice", rank="4d", seed_number=1),
            Player.create("Bob", rank="3d", seed_number=2),
            Player.create("Cara", rank="2d", seed_number=3),
            Player.create("Devin", rank="1d", seed_number=4),
        ]
    )
    save_tournament(tournament, path)

    assert main(["pair-round", str(path)]) == 0
    assert main(
        ["enter-result", str(path), "--round", "1", "--board", "1", "--winner", "black"]
    ) == 0

    loaded = load_tournament(path)
    assert loaded.rounds[0].games[0].result.status == "completed"
    assert loaded.audit_log[-1].event_type == "result_entered"
```

- [ ] **Step 5: Run characterization tests**

Run:

```powershell
python -m pytest tests/unit/test_web_app.py tests/unit/test_swiss_pairing.py tests/unit/test_mcmahon_pairing.py tests/integration/test_tournament_workflows.py -q
```

Expected: PASS.

- [ ] **Step 6: Commit**

```powershell
git add MAINTENANCE.md tests/unit/test_web_app.py tests/unit/test_swiss_pairing.py tests/unit/test_mcmahon_pairing.py tests/integration/test_tournament_workflows.py
git commit -m "Add rehabilitation characterization baseline"
```

## Task 2: Domain Field and Aggregate Validation

**Files:**

- Create: `src/pairing/domain/validation.py`
- Create: `tests/unit/test_domain_validation.py`
- Modify: `src/pairing/domain/player.py`
- Modify: `src/pairing/domain/config.py`
- Modify: `src/pairing/domain/result.py`
- Modify: `src/pairing/domain/game.py`
- Modify: `src/pairing/domain/round.py`
- Modify: `src/pairing/domain/tournament.py`

- [ ] **Step 1: Write failing aggregate tests**

Create tests for blank names, duplicate IDs/seeds/rounds, unsupported statuses, config mismatch, unknown player references, duplicate round participation, invalid bye shape, and invalid winners.

Representative test:

```python
def test_tournament_validation_rejects_unknown_game_player() -> None:
    tournament = Tournament.create("Validation Open")
    alice = Player.create("Alice", rank="1d", seed_number=1)
    tournament.players.append(alice)
    game = Game.create(
        round_number=1,
        board_number=1,
        black_player_id=alice.id,
        white_player_id="missing",
        pairing_explanation=[],
    )
    tournament.rounds.append(
        Round.create(number=1, games=[game], pairing_method="swiss", pairing_seed=1)
    )

    with pytest.raises(ValueError, match="unknown player"):
        tournament.validate()
```

- [ ] **Step 2: Run tests to verify RED**

Run:

```powershell
python -m pytest tests/unit/test_domain_validation.py -q
```

Expected: FAIL because `Tournament.validate` and field checks do not exist.

- [ ] **Step 3: Add supported-value constants and helpers**

Create `validation.py` with immutable sets:

```python
TOURNAMENT_FORMATS = frozenset({"swiss", "mcmahon"})
TOURNAMENT_STATUSES = frozenset({"draft", "active", "completed"})
PLAYER_STATUSES = frozenset({"active", "withdrawn"})
ROUND_STATUSES = frozenset({"draft", "published", "completed", "stale"})
RESULT_STATUSES = frozenset({"pending", "completed"})
RESULT_TYPES = frozenset({"pending", "normal", "bye"})
PAIRING_METHODS = frozenset({"swiss", "mcmahon"})
```

Add `require_non_blank`, `require_choice`, `require_positive`, and `require_unique` helpers with user-readable `ValueError` messages.

- [ ] **Step 4: Validate model factories and deserializers**

Call the helpers from `create` and `from_dict`. Do not accept arbitrary status or result strings.

- [ ] **Step 5: Implement `Tournament.validate()`**

Build player/round/game ID indexes once. Validate every relationship and enforce one appearance per player per round. Require a bye to have exactly one player and a completed bye result naming that player.

- [ ] **Step 6: Run focused and existing domain tests**

Run:

```powershell
python -m pytest tests/unit/test_domain_validation.py tests/unit/test_domain_serialization.py tests/unit/test_round_models.py -q
```

Expected: PASS.

- [ ] **Step 7: Commit**

```powershell
git add src/pairing/domain tests/unit/test_domain_validation.py tests/unit/test_domain_serialization.py tests/unit/test_round_models.py
git commit -m "Validate tournament aggregate state"
```

## Task 3: Storage Integrity and Schema-v1 Compatibility

**Files:**

- Modify: `src/pairing/storage/json_store.py`
- Modify: `tests/unit/test_json_store.py`
- Modify: `docs/tournament-file-format.md`

- [ ] **Step 1: Write failing save/load integrity tests**

Add tests proving:

- `save_tournament` rejects an invalid aggregate.
- invalid saves leave existing bytes unchanged.
- load rejects duplicate IDs, unknown references, and invalid winners.
- valid Stage 1 and Stage 4 schema-v1 fixtures still load.

Use `monkeypatch` to make `os.replace` raise `OSError` and assert the original file is unchanged.

- [ ] **Step 2: Run tests to verify RED**

Run:

```powershell
python -m pytest tests/unit/test_json_store.py -q
```

Expected: FAIL on accepted malformed aggregate and validate-before-save cases.

- [ ] **Step 3: Validate at both storage boundaries**

Before serializing, call `tournament.validate()`. After `Tournament.from_dict`, call `validate()` before returning.

- [ ] **Step 4: Make atomic writes durable and clean**

Open the temporary file explicitly, write JSON, flush, call `os.fsync`, then `os.replace`. In `finally`, remove a leftover temporary file if replacement did not occur.

- [ ] **Step 5: Update the file-format contract**

Document all current config, player, round, game, result, and audit fields; list supported and reserved values.

- [ ] **Step 6: Run storage and full baseline tests**

Run:

```powershell
python -m pytest tests/unit/test_json_store.py -q
python -m pytest -q
```

Expected: PASS.

- [ ] **Step 7: Commit**

```powershell
git add src/pairing/storage/json_store.py tests/unit/test_json_store.py docs/tournament-file-format.md
git commit -m "Harden schema v1 tournament storage"
```

## Task 4: Application Service Layer

**Files:**

- Create: `src/pairing/application/__init__.py`
- Create: `src/pairing/application/results.py`
- Create: `src/pairing/application/service.py`
- Create: `tests/unit/test_application_service.py`

- [ ] **Step 1: Write failing service tests**

Test create, import, generate, enter result, correct result, regenerate, standings, and CSV export. Assert saved state and audit actor.

Representative API:

```python
service = TournamentService(path)
outcome = service.generate_next_round(actor="web")
assert outcome.round_number == 1
assert load_tournament(path).audit_log[-1].actor == "web"
```

Also snapshot file bytes before an invalid operation and assert they are unchanged.

- [ ] **Step 2: Run tests to verify RED**

Run:

```powershell
python -m pytest tests/unit/test_application_service.py -q
```

Expected: FAIL because `pairing.application` does not exist.

- [ ] **Step 3: Add typed outcomes**

Define frozen dataclasses:

```python
@dataclass(frozen=True, slots=True)
class ImportOutcome:
    imported_count: int
    warnings: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class RoundOutcome:
    round_number: int
    game_count: int
    warnings: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ResultOutcome:
    round_number: int
    board_number: int
    corrected: bool
    invalidated_rounds: tuple[int, ...]
```

- [ ] **Step 4: Implement service load-mutate-validate-save workflow**

`TournamentService` stores a `Path`. Each mutating method loads once, mutates through domain/engine functions, appends audit events, validates, then saves once.

- [ ] **Step 5: Keep read operations mutation-free**

Standings and exports load and return data without saving or adding audit entries.

- [ ] **Step 6: Run service tests**

Run:

```powershell
python -m pytest tests/unit/test_application_service.py -q
```

Expected: PASS.

- [ ] **Step 7: Commit**

```powershell
git add src/pairing/application tests/unit/test_application_service.py
git commit -m "Add tournament application services"
```

## Task 5: Migrate CLI to Application Services

**Files:**

- Modify: `src/pairing/cli/main.py`
- Modify: `tests/unit/test_cli.py`

- [ ] **Step 1: Add CLI characterization for actor and unchanged failures**

Assert generated round audit entries use actor `cli`, and invalid commands leave the file unchanged.

- [ ] **Step 2: Run the new tests to verify RED**

Run:

```powershell
python -m pytest tests/unit/test_cli.py -q
```

Expected: FAIL because current round generation has no audit entry.

- [ ] **Step 3: Replace command mutation with service calls**

Keep parser construction in `main.py`; replace each load-mutate-save branch with a single `TournamentService` call.

- [ ] **Step 4: Preserve user-facing output**

Keep existing successful command text unless the new contract requires a warning line. Print `RoundOutcome.warnings` to stderr as `Warning: ...`.

- [ ] **Step 5: Run CLI and service tests**

Run:

```powershell
python -m pytest tests/unit/test_cli.py tests/unit/test_application_service.py -q
```

Expected: PASS.

- [ ] **Step 6: Commit**

```powershell
git add src/pairing/cli/main.py tests/unit/test_cli.py
git commit -m "Route CLI workflows through application services"
```

## Task 6: Correct Pairing History and Round Progression

**Files:**

- Modify: `src/pairing/engine/history.py`
- Modify: `src/pairing/engine/swiss.py`
- Modify: `src/pairing/engine/mcmahon.py`
- Modify: `src/pairing/engine/round_generation.py`
- Modify: `tests/unit/test_standings.py`
- Modify: `tests/unit/test_swiss_pairing.py`
- Modify: `tests/unit/test_mcmahon_pairing.py`

- [ ] **Step 1: Write failing progression/history tests**

Add tests that:

- Round 2 is rejected while Round 1 has pending normal games.
- Pending pairings appear in opponent and colour history.
- Standings still ignore pending results for score.
- A completed bye does not block progression when all normal games are complete.

- [ ] **Step 2: Run tests to verify RED**

Run:

```powershell
python -m pytest tests/unit/test_standings.py tests/unit/test_swiss_pairing.py tests/unit/test_mcmahon_pairing.py -q
```

Expected: FAIL on pending pairing history and progression.

- [ ] **Step 3: Separate pairing history from scored-result history**

Remove the completed-result guard from opponent/colour history; continue skipping stale rounds and byes.

- [ ] **Step 4: Add a shared progression precondition**

In `round_generation.py`, add:

```python
def validate_next_round_allowed(tournament: Tournament) -> None:
    active_rounds = [item for item in tournament.rounds if item.status != "stale"]
    if any(item.status == "stale" for item in tournament.rounds):
        raise ValueError("Tournament has stale rounds that must be regenerated first.")
    if active_rounds and active_rounds[-1].status != "completed":
        raise ValueError(f"Round {active_rounds[-1].number} must be completed first.")
```

Call it before format dispatch and at the start of both public format-specific generators so direct `swiss.generate_next_round` and `mcmahon.generate_next_round` calls enforce the same contract.

- [ ] **Step 5: Run focused tests**

Run:

```powershell
python -m pytest tests/unit/test_standings.py tests/unit/test_swiss_pairing.py tests/unit/test_mcmahon_pairing.py -q
```

Expected: PASS.

- [ ] **Step 6: Commit**

```powershell
git add src/pairing/engine tests/unit/test_standings.py tests/unit/test_swiss_pairing.py tests/unit/test_mcmahon_pairing.py
git commit -m "Enforce round progression and pairing history"
```

## Task 7: Unavoidable-Repeat Fallback and Pairing Warnings

**Files:**

- Create: `src/pairing/engine/pairing_result.py`
- Modify: `src/pairing/engine/pairing_core.py`
- Modify: `src/pairing/engine/swiss.py`
- Modify: `src/pairing/engine/mcmahon.py`
- Modify: `src/pairing/engine/explanations.py`
- Modify: `src/pairing/engine/round_generation.py`
- Modify: `tests/unit/test_swiss_pairing.py`
- Modify: `tests/unit/test_mcmahon_pairing.py`

- [ ] **Step 1: Write failing repeat-pressure tests**

Create a four-player complete round-robin history and assert the next generation succeeds with deterministic repeat warnings instead of raising.

- [ ] **Step 2: Run tests to verify RED**

Run:

```powershell
python -m pytest tests/unit/test_swiss_pairing.py tests/unit/test_mcmahon_pairing.py -q
```

Expected: FAIL with `Unable to generate ... without repeated opponents`.

- [ ] **Step 3: Add typed generation warnings**

Define:

```python
@dataclass(frozen=True, slots=True)
class PairingWarning:
    code: str
    message: str
    player_ids: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class GeneratedRound:
    round: Round
    warnings: tuple[PairingWarning, ...] = ()
```

- [ ] **Step 4: Add least-bad fallback search**

When strict search returns `None`, run deterministic matching that minimizes repeat count first, then score distance, rank distance, and stable IDs. Attach a warning for each repeated pair.

- [ ] **Step 5: Add warnings to explanations and audit outcome**

Put warning messages in affected games and round summary. Return warnings to the application service for audit and CLI/web display.

- [ ] **Step 6: Run pairing and application tests**

Run:

```powershell
python -m pytest tests/unit/test_swiss_pairing.py tests/unit/test_mcmahon_pairing.py tests/unit/test_application_service.py tests/unit/test_cli.py -q
```

Expected: PASS.

- [ ] **Step 7: Commit**

```powershell
git add src/pairing/engine src/pairing/application tests/unit/test_swiss_pairing.py tests/unit/test_mcmahon_pairing.py tests/unit/test_application_service.py tests/unit/test_cli.py
git commit -m "Handle unavoidable repeated pairings"
```

## Task 8: Result Correction and Auditable Regeneration

**Files:**

- Modify: `src/pairing/domain/result.py`
- Modify: `src/pairing/domain/tournament.py`
- Modify: `src/pairing/application/service.py`
- Modify: `tests/unit/test_application_service.py`
- Modify: `tests/unit/test_cli.py`
- Modify: `tests/integration/test_tournament_workflows.py`

- [ ] **Step 1: Write failing correction tests**

Assert first entry uses `result_entered`; second entry on the same game uses `result_corrected`, stores the old result snapshot, sets `correction_of` to the correction event ID, and invalidates later rounds.

- [ ] **Step 2: Write failing regeneration-history test**

Create three rounds, correct Round 1, regenerate from Round 1, and assert the regeneration audit entry contains serialized snapshots of old Rounds 2 and 3 before active rounds become `[1, 2]`.

- [ ] **Step 3: Run tests to verify RED**

Run:

```powershell
python -m pytest tests/unit/test_application_service.py tests/unit/test_cli.py tests/integration/test_tournament_workflows.py -q
```

Expected: FAIL because correction and stale snapshots are absent.

- [ ] **Step 4: Separate entry from correction**

Move workflow behavior into service methods `record_result` and `correct_result`; reject accidental overwrite through `record_result`.

- [ ] **Step 5: Preserve stale round snapshots**

Before purging, serialize stale rounds into audit details:

```python
details={
    "boundary_round": boundary,
    "superseded_rounds": [round_obj.to_dict() for round_obj in stale_rounds],
}
```

- [ ] **Step 6: Run correction tests**

Run:

```powershell
python -m pytest tests/unit/test_application_service.py tests/unit/test_cli.py tests/integration/test_tournament_workflows.py -q
```

Expected: PASS.

- [ ] **Step 7: Commit**

```powershell
git add src/pairing/domain src/pairing/application tests/unit/test_application_service.py tests/unit/test_cli.py tests/integration/test_tournament_workflows.py
git commit -m "Preserve result correction and regeneration history"
```

## Task 9: Rehabilitate Simplified McMahon

**Files:**

- Modify: `src/pairing/engine/mcmahon.py`
- Modify: `src/pairing/engine/explanations.py`
- Modify: `src/pairing/domain/config.py`
- Modify: `tests/unit/test_mcmahon_config.py`
- Modify: `tests/unit/test_mcmahon_pairing.py`
- Modify: `docs/superpowers/specs/2026-06-24-stage-3-mcmahon-design.md`

- [ ] **Step 1: Add failing McMahon edge tests**

Cover `1d` bar edge, below bar, unranked, odd field, later round, repeat pressure, and explanation text.

- [ ] **Step 2: Run tests to verify RED**

Run:

```powershell
python -m pytest tests/unit/test_mcmahon_config.py tests/unit/test_mcmahon_pairing.py -q
```

Expected: FAIL on explanation and edge-case contracts.

- [ ] **Step 3: Validate bar rank**

Parse `mcmahon_bar_rank` during config validation. Reject unranked bar values.

- [ ] **Step 4: Make explanations truthful**

Include the configured bar and each player's starting score in round/game explanation data. Use score-based wording for later-round byes.

- [ ] **Step 5: Correct Stage 3 documentation**

State explicitly that the MVP uses one binary bar, not rank bands, upper/lower bars, SODOS, or handicap.

- [ ] **Step 6: Run McMahon and full engine tests**

Run:

```powershell
python -m pytest tests/unit/test_mcmahon_config.py tests/unit/test_mcmahon_pairing.py tests/unit/test_swiss_pairing.py tests/unit/test_standings.py -q
```

Expected: PASS.

- [ ] **Step 7: Commit**

```powershell
git add src/pairing/domain/config.py src/pairing/engine/mcmahon.py src/pairing/engine/explanations.py tests/unit/test_mcmahon_config.py tests/unit/test_mcmahon_pairing.py docs/superpowers/specs/2026-06-24-stage-3-mcmahon-design.md
git commit -m "Define and test simplified McMahon policy"
```

## Task 10: Migrate and Split the Web Application

**Files:**

- Create: `src/pairing/web/forms.py`
- Create: `src/pairing/web/responses.py`
- Create: `src/pairing/web/routes.py`
- Create: `src/pairing/web/views.py`
- Modify: `src/pairing/web/app.py`
- Modify: `tests/unit/test_web_app.py`
- Create: `tests/unit/test_web_routing.py`

- [ ] **Step 1: Write failing web route tests**

Test:

- unknown GET returns 404
- unsupported method returns 405 and `Allow`
- mutation persists via services
- invalid form returns 400 and unchanged bytes
- unexpected service failure returns 500 and unchanged bytes

- [ ] **Step 2: Run tests to verify RED**

Run:

```powershell
python -m pytest tests/unit/test_web_app.py tests/unit/test_web_routing.py -q
```

Expected: FAIL on 404/405/500 and service-backed behavior.

- [ ] **Step 3: Extract response and form helpers**

`responses.py` defines `html_response`, `csv_response`, `redirect_response`, and `error_response`. `forms.py` defines `parse_urlencoded_form`.

- [ ] **Step 4: Extract views without visual redesign**

Move all HTML rendering to `views.py`. Preserve existing CSS and page labels, correcting encoding artifacts to the UTF-8 bullet `•`.

- [ ] **Step 5: Add explicit route table**

Use a small immutable mapping from `(method, path)` to handlers. Derive allowed methods for 405 responses.

- [ ] **Step 6: Keep `app.py` as assembly**

`create_web_app(path)` creates `TournamentService` and delegates each request to `dispatch_request`.

- [ ] **Step 7: Run web and full tests**

Run:

```powershell
python -m pytest tests/unit/test_web_app.py tests/unit/test_web_routing.py -q
python -m pytest -q
```

Expected: PASS.

- [ ] **Step 8: Commit**

```powershell
git add src/pairing/web tests/unit/test_web_app.py tests/unit/test_web_routing.py
git commit -m "Split and harden the local web application"
```

## Task 11: Reliable Server and Demo Workflow

**Files:**

- Modify: `src/pairing/web/server.py`
- Modify: `src/pairing/cli/main.py`
- Modify: `src/pairing/application/service.py`
- Modify: `tests/unit/test_cli.py`
- Create: `tests/integration/test_live_server.py`

- [ ] **Step 1: Write failing server and demo tests**

Test:

- `pairing demo <path>` creates a deterministic eight-player sample.
- `web --open-browser` calls `webbrowser.open` only after bind succeeds.
- an occupied port yields an actionable error.
- a server created with port `0` reports the actual bound port and serves `/display`.

- [ ] **Step 2: Run tests to verify RED**

Run:

```powershell
python -m pytest tests/unit/test_cli.py tests/integration/test_live_server.py -q
```

Expected: FAIL because demo and startup APIs do not exist.

- [ ] **Step 3: Add deterministic demo creation**

Create players Aya, Ben, Cheng, Dina, Eli, Fiona, Gao, and Hana with fixed ranks and seeds. Do not hard-code UUIDs.

- [ ] **Step 4: Make server startup testable**

Add `create_server(...)` returning the WSGI server and URL. `serve_tournament` prints the resolved path and actual URL, optionally opens the browser, then calls `serve_forever`.

- [ ] **Step 5: Translate bind failures**

Wrap `OSError` as:

```text
Cannot start local web server on 127.0.0.1:8000: the port is already in use.
```

- [ ] **Step 6: Run server tests**

Run:

```powershell
python -m pytest tests/unit/test_cli.py tests/integration/test_live_server.py -q
```

Expected: PASS.

- [ ] **Step 7: Commit**

```powershell
git add src/pairing/application/service.py src/pairing/cli/main.py src/pairing/web/server.py tests/unit/test_cli.py tests/integration/test_live_server.py
git commit -m "Add reliable local demo and server startup"
```

## Task 12: Property and End-to-End Workflow Tests

**Files:**

- Create: `tests/property/test_pairing_invariants.py`
- Modify: `tests/integration/test_tournament_workflows.py`

- [ ] **Step 1: Add generated player fields**

Use ranks sampled from `["5d", "3d", "1d", "1k", "5k", "unranked"]` and unique names/seeds for fields of 1–20 players.

- [ ] **Step 2: Add round-one invariants**

For both formats assert:

- all active players appear exactly once
- no inactive player appears
- odd count has exactly one bye
- even count has no bye
- generation is deterministic after normalizing generated timestamps and UUIDs

- [ ] **Step 3: Add save/load generated-state property**

Generate a valid tournament, round-trip through JSON, and compare normalized dictionaries.

- [ ] **Step 4: Add complete Swiss and McMahon integration workflows**

Run two or three rounds by entering deterministic winners for all normal games, then reload and assert standings, round completion, and audit sequence.

- [ ] **Step 5: Run property and integration tests**

Run:

```powershell
python -m pytest tests/property tests/integration -q
```

Expected: PASS.

- [ ] **Step 6: Commit**

```powershell
git add tests/property tests/integration
git commit -m "Add pairing properties and full workflow tests"
```

## Task 13: Development Tooling and Quality Gates

**Files:**

- Modify: `pyproject.toml`
- Modify: production modules as required by tool findings

- [ ] **Step 1: Add development dependencies**

Add:

```toml
dev = [
  "pytest>=8.0",
  "hypothesis>=6.0",
  "pytest-cov>=5.0",
  "ruff>=0.6",
  "mypy>=1.11",
]
```

- [ ] **Step 2: Add Ruff and mypy configuration**

Use line length 100, Python 3.12, lint rules `E`, `F`, `I`, `B`, and type-check `src/pairing`.

- [ ] **Step 3: Install the project in editable mode**

Run:

```powershell
python -m pip install -e ".[dev]"
```

Expected: exit 0.

- [ ] **Step 4: Run formatting/lint/type checks**

Run:

```powershell
python -m ruff format --check .
python -m ruff check .
python -m mypy src/pairing
```

Expected: exit non-zero with actionable formatting, import-order, or type findings; no configuration or parser crash.

- [ ] **Step 5: Fix only reported production issues**

Apply formatting mechanically, remove unused imports, add return/protocol types, and eliminate existing `type: ignore` casts by validating collection shapes before construction.

- [ ] **Step 6: Run quality and test gates**

Run:

```powershell
python -m ruff format --check .
python -m ruff check .
python -m mypy src/pairing
python -m pytest --cov=pairing --cov-report=term-missing -q
```

Expected: all commands exit 0; core production coverage at least 90%.

- [ ] **Step 7: Commit**

```powershell
git add pyproject.toml src tests
git commit -m "Add repository quality gates"
```

## Task 14: Architecture, Roadmap, and Operations Documentation

**Files:**

- Create: `docs/architecture.md`
- Create: `docs/roadmap.md`
- Modify: `README.md`
- Modify: `PROJECT_CONTEXT.md`
- Modify: `MAINTENANCE.md`

- [ ] **Step 1: Document the implemented architecture**

Describe each package, allowed dependency direction, schema boundary, workflow services, pairing contracts, and supported/reserved behavior.

- [ ] **Step 2: Rewrite README around current operation**

Include:

```powershell
python -m pip install -e ".[dev]"
pairing demo demo.tgo.json
pairing web demo.tgo.json --port 8000 --open-browser
```

Also include CLI create/import/pair/result/standings examples and explain that the server remains attached to the managing terminal.

- [ ] **Step 3: Publish the revised roadmap**

Use Milestones A–E from the repository rehabilitation design and mark Milestone A complete only after final verification.

- [ ] **Step 4: Update project context and maintenance log**

Record all rehabilitation commits, quality commands, known reserved fields, and the recommended integration path from `codex/stage-4-web`.

- [ ] **Step 5: Verify documentation commands**

Run every README command against a temporary tournament path.

- [ ] **Step 6: Commit**

```powershell
git add README.md PROJECT_CONTEXT.md MAINTENANCE.md docs/architecture.md docs/roadmap.md
git commit -m "Document rehabilitated repository and roadmap"
```

## Task 15: Final Verification and Sample UI

**Files:**

- Modify only files required by verification findings.

- [ ] **Step 1: Run the complete automated matrix**

Run:

```powershell
python -m ruff format --check .
python -m ruff check .
python -m mypy src/pairing
python -m compileall -q src
python -m pytest --cov=pairing --cov-report=term-missing -q
```

Expected: all commands exit 0.

- [ ] **Step 2: Run installed-command smoke tests**

Run:

```powershell
pairing --help
pairing demo .tmp/final-demo/demo.tgo.json
```

Expected: help lists all commands; demo file is created.

- [ ] **Step 3: Start the final UI**

Run the installed command in a hidden background process:

```powershell
pairing web .tmp/final-demo/demo.tgo.json --host 127.0.0.1 --port 8123
```

If 8123 is occupied by the old server, stop only that known demo process or use the next free documented port and report the exact URL.

- [ ] **Step 4: Verify HTTP and browser routes**

Verify:

- `/`
- `/players`
- `/pairings`
- `/results`
- `/standings`
- `/exports`
- `/display`

Exercise one safe sample mutation and reload the saved file.

- [ ] **Step 5: Review requirements line by line**

Check every success criterion in the repository rehabilitation design and append final evidence to `MAINTENANCE.md`.

- [ ] **Step 6: Commit final verification documentation**

```powershell
git add MAINTENANCE.md
git commit -m "Record repository rehabilitation verification"
```

- [ ] **Step 7: Finish the development branch**

Use `superpowers:finishing-a-development-branch`, present integration choices, and do not merge or delete worktrees without user direction.
