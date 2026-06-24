# Stage 3 McMahon Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a usable McMahon tournament workflow on top of the Stage 2 Swiss foundation, with minimal CLI support and deterministic, explainable round generation.

**Architecture:** Keep one shared pairing pipeline and route by tournament format. Swiss remains the existing implementation path, while McMahon adds a starting-score policy, bar-aware score grouping, and format-aware standings. The CLI stays thin and only selects format plus renders output.

**Tech Stack:** Python 3.12, `pytest`, standard library dataclasses, JSON persistence already in the repo, CLI via `argparse`.

---

### Task 1: Make tournament format and McMahon settings first-class

**Files:**
- Modify: `src/pairing/domain/tournament.py`
- Modify: `src/pairing/domain/config.py`
- Test: `tests/unit/test_mcmahon_config.py`
- Test: `tests/unit/test_round_models.py`

- [ ] **Step 1: Write the failing test**

```python
from pairing.domain.tournament import Tournament


def test_mcmahon_format_round_trips_through_save_model() -> None:
    tournament = Tournament.create("McMahon Open", round_count=5, format="mcmahon")

    payload = tournament.to_dict()
    restored = Tournament.from_dict(payload)

    assert restored.format == "mcmahon"
    assert restored.config.pairing_method == "mcmahon"
    assert restored.config.mcmahon_bar_rank == tournament.config.mcmahon_bar_rank
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/unit/test_mcmahon_config.py -q`

Expected: fail with `TypeError` from `Tournament.create()` or `AttributeError` for missing McMahon config fields.

- [ ] **Step 3: Write minimal implementation**

Add a `format` keyword to `Tournament.create()` and default it to `"swiss"`.

```python
@classmethod
def create(cls, name: str, *, round_count: int = 5, format: str = "swiss") -> "Tournament":
    ...
    tournament = cls(
        ...
        format=format,
    )
    tournament.config.pairing_method = format
```

Add a small McMahon config block that can be serialized cleanly, starting with a single explicit bar field.

```python
@dataclass(slots=True)
class TournamentConfig:
    ...
    mcmahon_bar_rank: str = "1d"
```

Wire the new field through `to_dict()` and `from_dict()`.

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/unit/test_mcmahon_config.py tests/unit/test_round_models.py -q`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/pairing/domain/tournament.py src/pairing/domain/config.py tests/unit/test_mcmahon_config.py tests/unit/test_round_models.py
git commit -m "Add McMahon format config and serialization"
```

### Task 2: Add a shared round-generation dispatcher and McMahon score policy

**Files:**
- Create: `src/pairing/engine/round_generation.py`
- Create: `src/pairing/engine/mcmahon.py`
- Modify: `src/pairing/engine/standings.py`
- Modify: `src/pairing/engine/__init__.py`
- Test: `tests/unit/test_mcmahon_pairing.py`
- Test: `tests/unit/test_standings.py`

- [ ] **Step 1: Write the failing test**

```python
from pairing.domain.player import Player
from pairing.domain.tournament import Tournament
from pairing.engine.round_generation import generate_next_round


def test_generate_next_round_uses_mcmahon_generator() -> None:
    tournament = Tournament.create("McMahon Open", format="mcmahon")
    tournament.players.extend(
        [
            Player.create("Alice", rank="4d", seed_number=1),
            Player.create("Bob", rank="3d", seed_number=2),
            Player.create("Charlie", rank="1d", seed_number=3),
            Player.create("Diana", rank="1k", seed_number=4),
        ]
    )

    round_obj = generate_next_round(tournament)

    assert round_obj.pairing_method == "mcmahon"
    assert round_obj.number == 1
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/unit/test_mcmahon_pairing.py -q`

Expected: fail because `pairing.round_generation` and `pairing.mcmahon` do not exist yet.

- [ ] **Step 3: Write minimal implementation**

Create a tiny dispatcher that selects Swiss or McMahon by `tournament.format`.

```python
from pairing.engine.swiss import generate_next_round as generate_swiss_round
from pairing.engine.mcmahon import generate_next_round as generate_mcmahon_round


def generate_next_round(tournament: Tournament) -> Round:
    if tournament.format == "mcmahon":
        return generate_mcmahon_round(tournament)
    return generate_swiss_round(tournament)
```

In `src/pairing/engine/mcmahon.py`, add a pure helper for the McMahon starting score and use the existing score-group pairing search from Swiss rather than duplicating it.

```python
def mcmahon_starting_score(player: Player, tournament: Tournament) -> float:
    ...
```

Extend `StandingEntry` so McMahon standings can expose both the raw game score and the starting score used to seed the round groups.

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/unit/test_mcmahon_pairing.py tests/unit/test_standings.py -q`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/pairing/engine/round_generation.py src/pairing/engine/mcmahon.py src/pairing/engine/standings.py src/pairing/engine/__init__.py tests/unit/test_mcmahon_pairing.py tests/unit/test_standings.py
git commit -m "Add McMahon round generation"
```

### Task 3: Wire McMahon into the CLI and make standings format-aware

**Files:**
- Modify: `src/pairing/cli/main.py`
- Modify: `src/pairing/engine/explanations.py`
- Modify: `tests/unit/test_cli.py`
- Modify: `PROJECT_CONTEXT.md`

- [ ] **Step 1: Write the failing test**

```python
def test_cli_create_mcmahon_tournament_and_show_standings(tmp_path, capsys) -> None:
    tournament_path = tmp_path / "mcmahon.tgo.json"

    assert main(["create", str(tournament_path), "--name", "McMahon Open", "--format", "mcmahon"]) == 0
    assert main(["standings", str(tournament_path)]) == 0

    captured = capsys.readouterr()
    assert "McMahon Open" in captured.out
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/unit/test_cli.py -q`

Expected: fail because `--format` and `standings` are not implemented yet.

- [ ] **Step 3: Write minimal implementation**

Add `--format swiss|mcmahon` to `create`, route round generation through the shared dispatcher, and add a small `standings` command that prints the current format-aware table.

```python
create_parser.add_argument("--format", default="swiss", choices=("swiss", "mcmahon"))
```

Update the standings output so McMahon shows the starting-score column alongside the normal score columns.

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/unit/test_cli.py -q`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/pairing/cli/main.py src/pairing/engine/explanations.py tests/unit/test_cli.py PROJECT_CONTEXT.md
git commit -m "Expose McMahon workflow in the CLI"
```

### Task 4: Refresh the branch handoff note and verify the full suite

**Files:**
- Modify: `PROJECT_CONTEXT.md`
- Modify: `docs/superpowers/specs/2026-06-24-stage-3-mcmahon-design.md` if any wording needs tightening after implementation

- [ ] **Step 1: Update the handoff note**

Make sure `PROJECT_CONTEXT.md` records:

```markdown
- Stage 3 branch: `codex/stage-3-mcmahon`
- Stage 2 Swiss foundation merged into the worktree
- McMahon work still in progress or complete, depending on the current checkpoint
- The latest verified test count
- The next resumable slice
```

- [ ] **Step 2: Run the full test suite**

Run: `python -m pytest`

Expected: PASS with the updated Stage 3 count.

- [ ] **Step 3: Inspect branch cleanliness**

Run: `git status -sb`

Expected: clean working tree before handoff or commit.

- [ ] **Step 4: Commit**

```bash
git add PROJECT_CONTEXT.md docs/superpowers/specs/2026-06-24-stage-3-mcmahon-design.md
git commit -m "Document Stage 3 McMahon workflow"
```

## Coverage Notes

- The format/config task covers persisted tournament format selection.
- The dispatcher task covers shared Swiss/McMahon round generation.
- The CLI task covers the minimum usable workflow.
- The handoff task keeps the branch resumable after interruptions.
