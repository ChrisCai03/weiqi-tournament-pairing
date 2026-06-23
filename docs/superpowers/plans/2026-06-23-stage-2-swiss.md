# Stage 2 Swiss Workflow Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extend the Stage 1 tournament foundation into a working Swiss workflow with structured rounds, standings, pairing generation, result entry, and safe regeneration.

**Architecture:** Keep all Swiss behavior in small engine modules and preserve the current CLI-first shape. Introduce typed round/game/result domain objects first, then layer standings and Swiss workflow commands on top in vertical slices that are individually testable and commit-safe.

**Tech Stack:** Python 3.12+, dataclasses, argparse, standard library JSON/CSV, pytest.

---

## Scope

This plan implements Stage 2 from the approved spec:

- typed `Round`, `Game`, and `Result` domain state
- standings and tie-break baseline
- round 1 Swiss pairing
- result entry
- later-round Swiss pairing
- stale-round marking and regeneration

This plan intentionally does not implement:

- McMahon pairing
- PDF export
- manual pairing override editing
- web UI

## File Structure

Create these files:

- `src/pairing/domain/result.py`: typed game result model.
- `src/pairing/domain/game.py`: typed game model and serialization.
- `src/pairing/domain/round.py`: typed round model and serialization.
- `src/pairing/engine/__init__.py`: engine exports.
- `src/pairing/engine/history.py`: pairing history and colour history helpers.
- `src/pairing/engine/standings.py`: standings and tie-break baseline.
- `src/pairing/engine/bye.py`: bye candidate selection.
- `src/pairing/engine/colours.py`: colour preference and assignment helpers.
- `src/pairing/engine/explanations.py`: pairing explanation helpers.
- `src/pairing/engine/swiss.py`: Swiss pairing service.
- `tests/unit/test_round_models.py`: round/game/result serialization and validation.
- `tests/unit/test_standings.py`: standings and tie-break tests.
- `tests/unit/test_swiss_pairing.py`: round 1 and later-round Swiss tests.

Modify these files:

- `README.md`: add Stage 2 commands once the actual CLI surface exists.
- `docs/tournament-file-format.md`: update example structure when rounds and games become structured.
- `src/pairing/domain/__init__.py`: export new domain models.
- `src/pairing/domain/tournament.py`: replace raw round dictionaries with typed round objects and add Stage 2 workflow methods.
- `src/pairing/storage/json_store.py`: rely on the tighter round/game/result validation during load.
- `src/pairing/cli/main.py`: add `standings`, `pair-round`, `enter-result`, and `regenerate-from` commands.
- `tests/unit/test_cli.py`: Stage 2 workflow CLI tests.
- `tests/unit/test_domain_serialization.py`: add Stage 2 deserialization guards as needed.

## Task 1: Structured Round, Game, and Result Domain Models

**Files:**
- Create: `src/pairing/domain/result.py`
- Create: `src/pairing/domain/game.py`
- Create: `src/pairing/domain/round.py`
- Modify: `src/pairing/domain/__init__.py`
- Modify: `src/pairing/domain/tournament.py`
- Test: `tests/unit/test_round_models.py`

- [ ] **Step 1: Write failing round model tests**

Create `tests/unit/test_round_models.py` with:

```python
import pytest

from pairing.domain.game import Game
from pairing.domain.result import Result
from pairing.domain.round import Round
from pairing.domain.tournament import Tournament


def test_result_round_trip() -> None:
    result = Result.pending()

    restored = Result.from_dict(result.to_dict())

    assert restored.status == "pending"
    assert restored.result_type == "pending"
    assert restored.winner_player_id is None


def test_round_round_trip() -> None:
    game = Game.create(
        round_number=1,
        board_number=1,
        black_player_id="player-a",
        white_player_id="player-b",
        pairing_explanation=["Top-half vs bottom-half opening pairing."],
    )
    round_obj = Round.create(number=1, games=[game], pairing_method="swiss", pairing_seed=1)

    restored = Round.from_dict(round_obj.to_dict())

    assert restored.number == 1
    assert restored.games[0].board_number == 1
    assert restored.games[0].black_player_id == "player-a"


def test_tournament_rounds_round_trip() -> None:
    tournament = Tournament.create("Example Weiqi Open")
    game = Game.create(
        round_number=1,
        board_number=1,
        black_player_id="player-a",
        white_player_id="player-b",
        pairing_explanation=["Seeded opening pairing."],
    )
    tournament.rounds.append(
        Round.create(number=1, games=[game], pairing_method="swiss", pairing_seed=1)
    )

    restored = Tournament.from_dict(tournament.to_dict())

    assert restored.rounds[0].number == 1
    assert restored.rounds[0].games[0].board_number == 1


def test_round_rejects_duplicate_board_numbers() -> None:
    game_one = Game.create(
        round_number=1,
        board_number=1,
        black_player_id="player-a",
        white_player_id="player-b",
        pairing_explanation=[],
    )
    game_two = Game.create(
        round_number=1,
        board_number=1,
        black_player_id="player-c",
        white_player_id="player-d",
        pairing_explanation=[],
    )

    with pytest.raises(ValueError, match="Duplicate board number"):
        Round.create(number=1, games=[game_one, game_two], pairing_method="swiss", pairing_seed=1)
```

- [ ] **Step 2: Run round model tests to verify failure**

Run:

```powershell
python -m pytest tests/unit/test_round_models.py -q
```

Expected: FAIL because the new domain modules do not exist yet.

- [ ] **Step 3: Implement `result.py`**

Create `src/pairing/domain/result.py`:

```python
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(slots=True)
class Result:
    status: str
    result_type: str
    winner_player_id: str | None = None
    entered_at: str | None = None
    entered_by: str = "cli"
    notes: str = ""
    correction_of: str | None = None

    @classmethod
    def pending(cls) -> "Result":
        return cls(status="pending", result_type="pending")

    def to_dict(self) -> dict[str, object]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "Result":
        return cls(
            status=str(data.get("status", "pending")),
            result_type=str(data.get("result_type", "pending")),
            winner_player_id=(str(data["winner_player_id"]) if data.get("winner_player_id") is not None else None),
            entered_at=(str(data["entered_at"]) if data.get("entered_at") is not None else None),
            entered_by=str(data.get("entered_by", "cli")),
            notes=str(data.get("notes", "")),
            correction_of=(str(data["correction_of"]) if data.get("correction_of") is not None else None),
        )

    @classmethod
    def completed(
        cls,
        *,
        result_type: str,
        winner_player_id: str | None,
        entered_by: str = "cli",
        notes: str = "",
        correction_of: str | None = None,
    ) -> "Result":
        return cls(
            status="completed",
            result_type=result_type,
            winner_player_id=winner_player_id,
            entered_at=_utc_now_iso(),
            entered_by=entered_by,
            notes=notes,
            correction_of=correction_of,
        )
```

- [ ] **Step 4: Implement `game.py`**

Create `src/pairing/domain/game.py`:

```python
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from uuid import uuid4

from pairing.domain.result import Result


@dataclass(slots=True)
class Game:
    id: str
    round_number: int
    board_number: int
    black_player_id: str | None
    white_player_id: str | None
    handicap: int = 0
    komi: float = 0.0
    result: Result = field(default_factory=Result.pending)
    pairing_explanation: list[str] = field(default_factory=list)
    override_origin: str = "engine"

    @classmethod
    def create(
        cls,
        *,
        round_number: int,
        board_number: int,
        black_player_id: str | None,
        white_player_id: str | None,
        pairing_explanation: list[str],
        handicap: int = 0,
        komi: float = 0.0,
        override_origin: str = "engine",
    ) -> "Game":
        return cls(
            id=str(uuid4()),
            round_number=round_number,
            board_number=board_number,
            black_player_id=black_player_id,
            white_player_id=white_player_id,
            handicap=handicap,
            komi=komi,
            pairing_explanation=list(pairing_explanation),
            override_origin=override_origin,
        )

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["result"] = self.result.to_dict()
        return payload

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "Game":
        return cls(
            id=str(data["id"]),
            round_number=int(data["round_number"]),
            board_number=int(data["board_number"]),
            black_player_id=(str(data["black_player_id"]) if data.get("black_player_id") is not None else None),
            white_player_id=(str(data["white_player_id"]) if data.get("white_player_id") is not None else None),
            handicap=int(data.get("handicap", 0)),
            komi=float(data.get("komi", 0.0)),
            result=Result.from_dict(dict(data.get("result", {}))),
            pairing_explanation=[str(item) for item in data.get("pairing_explanation", [])],
            override_origin=str(data.get("override_origin", "engine")),
        )
```

- [ ] **Step 5: Implement `round.py`**

Create `src/pairing/domain/round.py`:

```python
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

from pairing.domain.game import Game


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(slots=True)
class Round:
    number: int
    status: str
    generated_at: str
    completed_at: str | None
    pairing_method: str
    pairing_seed: int
    games: list[Game] = field(default_factory=list)
    is_regenerated: bool = False
    supersedes_round_version: int | None = None
    explanation_summary: list[str] = field(default_factory=list)

    @classmethod
    def create(
        cls,
        *,
        number: int,
        games: list[Game],
        pairing_method: str,
        pairing_seed: int,
        explanation_summary: list[str] | None = None,
    ) -> "Round":
        board_numbers = [game.board_number for game in games]
        if len(board_numbers) != len(set(board_numbers)):
            raise ValueError(f"Duplicate board number in round {number}.")
        return cls(
            number=number,
            status="draft",
            generated_at=_utc_now_iso(),
            completed_at=None,
            pairing_method=pairing_method,
            pairing_seed=pairing_seed,
            games=list(games),
            explanation_summary=list(explanation_summary or []),
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "number": self.number,
            "status": self.status,
            "generated_at": self.generated_at,
            "completed_at": self.completed_at,
            "pairing_method": self.pairing_method,
            "pairing_seed": self.pairing_seed,
            "games": [game.to_dict() for game in self.games],
            "is_regenerated": self.is_regenerated,
            "supersedes_round_version": self.supersedes_round_version,
            "explanation_summary": list(self.explanation_summary),
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "Round":
        games = [Game.from_dict(dict(game)) for game in data.get("games", [])]  # type: ignore[arg-type]
        board_numbers = [game.board_number for game in games]
        if len(board_numbers) != len(set(board_numbers)):
            raise ValueError(f"Duplicate board number in round {data.get('number', '?')}.")
        return cls(
            number=int(data["number"]),
            status=str(data.get("status", "draft")),
            generated_at=str(data.get("generated_at", _utc_now_iso())),
            completed_at=(str(data["completed_at"]) if data.get("completed_at") is not None else None),
            pairing_method=str(data.get("pairing_method", "swiss")),
            pairing_seed=int(data.get("pairing_seed", 1)),
            games=games,
            is_regenerated=bool(data.get("is_regenerated", False)),
            supersedes_round_version=(
                int(data["supersedes_round_version"]) if data.get("supersedes_round_version") is not None else None
            ),
            explanation_summary=[str(item) for item in data.get("explanation_summary", [])],
        )
```

- [ ] **Step 6: Update domain exports and tournament serialization**

Replace `src/pairing/domain/__init__.py` exports to include:

```python
from pairing.domain.game import Game
from pairing.domain.result import Result
from pairing.domain.round import Round
```

Update `src/pairing/domain/tournament.py` so:

- `rounds` is typed as `list[Round]`
- `to_dict()` serializes rounds with `round_obj.to_dict()`
- `from_dict()` deserializes rounds with `Round.from_dict(...)`

Use:

```python
rounds=[Round.from_dict(dict(round_data)) for round_data in data.get("rounds", [])]
```

- [ ] **Step 7: Run focused tests**

Run:

```powershell
python -m pytest tests/unit/test_round_models.py tests/unit/test_json_store.py -q
```

Expected: PASS.

- [ ] **Step 8: Run full test suite**

Run:

```powershell
python -m pytest
```

Expected: PASS.

- [ ] **Step 9: Commit**

```powershell
git add src/pairing/domain tests/unit/test_round_models.py
git commit -m "Add structured round domain models"
```

## Task 2: Standings and Pairing History Baseline

**Files:**
- Create: `src/pairing/engine/__init__.py`
- Create: `src/pairing/engine/history.py`
- Create: `src/pairing/engine/standings.py`
- Test: `tests/unit/test_standings.py`

- [ ] **Step 1: Write failing standings tests**

Create `tests/unit/test_standings.py`:

```python
from pairing.domain.game import Game
from pairing.domain.player import Player
from pairing.domain.result import Result
from pairing.domain.round import Round
from pairing.domain.tournament import Tournament
from pairing.engine.standings import calculate_standings


def test_calculate_standings_orders_by_score_then_tiebreaks() -> None:
    tournament = Tournament.create("Example Weiqi Open")
    alice = Player.create("Alice", rank="3d", seed_number=1)
    bob = Player.create("Bob", rank="2d", seed_number=2)
    charlie = Player.create("Charlie", rank="1d", seed_number=3)
    diana = Player.create("Diana", rank="1k", seed_number=4)
    tournament.players.extend([alice, bob, charlie, diana])

    game_one = Game.create(
        round_number=1,
        board_number=1,
        black_player_id=alice.id,
        white_player_id=bob.id,
        pairing_explanation=[],
    )
    game_one.result = Result.completed(result_type="normal", winner_player_id=alice.id)
    game_two = Game.create(
        round_number=1,
        board_number=2,
        black_player_id=charlie.id,
        white_player_id=diana.id,
        pairing_explanation=[],
    )
    game_two.result = Result.completed(result_type="normal", winner_player_id=charlie.id)
    tournament.rounds.append(Round.create(number=1, games=[game_one, game_two], pairing_method="swiss", pairing_seed=1))
    tournament.rounds[0].status = "completed"

    standings = calculate_standings(tournament)

    assert [entry.player.display_name for entry in standings] == ["Alice", "Charlie", "Bob", "Diana"]
    assert standings[0].score == 1.0
    assert standings[2].score == 0.0
```

- [ ] **Step 2: Run standings tests to verify failure**

Run:

```powershell
python -m pytest tests/unit/test_standings.py -q
```

Expected: FAIL because `pairing.engine.standings` does not exist yet.

- [ ] **Step 3: Implement `history.py`**

Create `src/pairing/engine/history.py` with helpers:

```python
from __future__ import annotations

from pairing.domain.tournament import Tournament


def opponent_ids_by_player(tournament: Tournament) -> dict[str, list[str]]:
    history: dict[str, list[str]] = {player.id: [] for player in tournament.players}
    for round_obj in tournament.rounds:
        for game in round_obj.games:
            if game.black_player_id and game.white_player_id:
                history.setdefault(game.black_player_id, []).append(game.white_player_id)
                history.setdefault(game.white_player_id, []).append(game.black_player_id)
    return history


def colour_history_by_player(tournament: Tournament) -> dict[str, list[str]]:
    history: dict[str, list[str]] = {player.id: [] for player in tournament.players}
    for round_obj in tournament.rounds:
        for game in round_obj.games:
            if game.black_player_id:
                history.setdefault(game.black_player_id, []).append("black")
            if game.white_player_id:
                history.setdefault(game.white_player_id, []).append("white")
    return history
```

- [ ] **Step 4: Implement `standings.py`**

Create `src/pairing/engine/standings.py` with:

```python
from __future__ import annotations

from dataclasses import dataclass, field

from pairing.domain.player import Player
from pairing.domain.tournament import Tournament
from pairing.engine.history import colour_history_by_player, opponent_ids_by_player


@dataclass(slots=True)
class StandingEntry:
    player: Player
    score: float = 0.0
    wins: int = 0
    losses: int = 0
    byes: int = 0
    opponents: list[str] = field(default_factory=list)
    colours: list[str] = field(default_factory=list)
    sos: float = 0.0
    sosos: float = 0.0


def calculate_standings(tournament: Tournament) -> list[StandingEntry]:
    entries = {
        player.id: StandingEntry(player=player)
        for player in tournament.players
    }

    for round_obj in tournament.rounds:
        for game in round_obj.games:
            result = game.result
            if result.status != "completed":
                continue

            if game.black_player_id and game.white_player_id:
                black_entry = entries[game.black_player_id]
                white_entry = entries[game.white_player_id]
                black_entry.opponents.append(game.white_player_id)
                white_entry.opponents.append(game.black_player_id)
                black_entry.colours.append("black")
                white_entry.colours.append("white")

                if result.winner_player_id == game.black_player_id:
                    black_entry.score += tournament.config.score_win
                    black_entry.wins += 1
                    white_entry.score += tournament.config.score_loss
                    white_entry.losses += 1
                elif result.winner_player_id == game.white_player_id:
                    white_entry.score += tournament.config.score_win
                    white_entry.wins += 1
                    black_entry.score += tournament.config.score_loss
                    black_entry.losses += 1

            elif result.result_type == "bye" and result.winner_player_id:
                bye_entry = entries[result.winner_player_id]
                bye_entry.score += tournament.config.score_bye
                bye_entry.wins += 1
                bye_entry.byes += 1

    for entry in entries.values():
        entry.sos = sum(entries[opponent_id].score for opponent_id in entry.opponents)
    for entry in entries.values():
        entry.sosos = sum(entries[opponent_id].sos for opponent_id in entry.opponents)

    return sorted(
        entries.values(),
        key=lambda entry: (
            -entry.score,
            -entry.wins,
            -entry.sos,
            -entry.sosos,
            -entry.player.rank_sort_value,
            entry.player.seed_number,
            entry.player.id,
        ),
    )
```

- [ ] **Step 5: Export engine symbols**

Create `src/pairing/engine/__init__.py`:

```python
"""Swiss engine services."""

from pairing.engine.standings import StandingEntry, calculate_standings

__all__ = ["StandingEntry", "calculate_standings"]
```

- [ ] **Step 6: Run focused tests**

Run:

```powershell
python -m pytest tests/unit/test_standings.py -q
```

Expected: PASS.

- [ ] **Step 7: Run full test suite**

Run:

```powershell
python -m pytest
```

Expected: PASS.

- [ ] **Step 8: Commit**

```powershell
git add src/pairing/engine tests/unit/test_standings.py
git commit -m "Add standings baseline"
```

## Task 3: Round 1 Swiss Pairing

**Files:**
- Create: `src/pairing/engine/bye.py`
- Create: `src/pairing/engine/colours.py`
- Create: `src/pairing/engine/explanations.py`
- Create: `src/pairing/engine/swiss.py`
- Modify: `src/pairing/domain/tournament.py`
- Modify: `src/pairing/cli/main.py`
- Test: `tests/unit/test_swiss_pairing.py`
- Test: `tests/unit/test_cli.py`

- [ ] **Step 1: Write failing round 1 Swiss tests**

Create `tests/unit/test_swiss_pairing.py` with:

```python
from pairing.domain.player import Player
from pairing.domain.tournament import Tournament
from pairing.engine.swiss import generate_next_round


def test_generate_first_round_pairs_top_half_vs_bottom_half() -> None:
    tournament = Tournament.create("Example Weiqi Open")
    tournament.players.extend(
        [
            Player.create("Alice", rank="4d", seed_number=1),
            Player.create("Bob", rank="3d", seed_number=2),
            Player.create("Charlie", rank="1d", seed_number=3),
            Player.create("Diana", rank="1k", seed_number=4),
        ]
    )

    round_obj = generate_next_round(tournament)

    assert round_obj.number == 1
    assert len(round_obj.games) == 2
    paired_ids = {
        frozenset((game.black_player_id, game.white_player_id))
        for game in round_obj.games
    }
    assert paired_ids == {
        frozenset((tournament.players[0].id, tournament.players[2].id)),
        frozenset((tournament.players[1].id, tournament.players[3].id)),
    }
```

- [ ] **Step 2: Run Swiss tests to verify failure**

Run:

```powershell
python -m pytest tests/unit/test_swiss_pairing.py -q
```

Expected: FAIL because `generate_next_round` does not exist yet.

- [ ] **Step 3: Implement bye, colour, and explanation helpers**

Create focused helpers:

- `bye.py`: select lowest-ranked eligible bye player
- `colours.py`: deterministic black/white assignment for a pair
- `explanations.py`: return short explanation lists per game

Keep each helper tiny and dependency-light.

- [ ] **Step 4: Implement `generate_next_round` in `swiss.py`**

Implement first-round behavior:

- reject empty player list
- sort active players by `rank_sort_value`, `seed_number`, `id`
- split into top and bottom halves
- assign a bye if the active count is odd
- pair matching indices across halves
- assign board numbers from `1..N`
- return a `Round`

- [ ] **Step 5: Add tournament and CLI wiring**

Add a `Tournament.next_round_number()` helper and append round generation through:

- `pair-round <tournament_path>`

CLI should:

- load tournament
- generate round
- append it
- save tournament
- emit a short success line

- [ ] **Step 6: Add CLI tests**

Extend `tests/unit/test_cli.py` with:

```python
def test_cli_pair_round_creates_first_round(tmp_path):
    ...
```

Assert:

- command returns `0`
- tournament now contains round `1`
- round contains expected number of games

- [ ] **Step 7: Run focused tests**

Run:

```powershell
python -m pytest tests/unit/test_swiss_pairing.py tests/unit/test_cli.py -q
```

Expected: PASS.

- [ ] **Step 8: Run full test suite**

Run:

```powershell
python -m pytest
```

Expected: PASS.

- [ ] **Step 9: Commit**

```powershell
git add src/pairing/engine src/pairing/cli src/pairing/domain tests/unit/test_swiss_pairing.py tests/unit/test_cli.py
git commit -m "Add first round Swiss pairing"
```

## Task 4: Result Entry

**Files:**
- Modify: `src/pairing/cli/main.py`
- Modify: `src/pairing/domain/tournament.py`
- Modify: `src/pairing/domain/result.py`
- Test: `tests/unit/test_cli.py`
- Test: `tests/unit/test_standings.py`

- [ ] **Step 1: Write failing result-entry CLI tests**

Add tests for:

- entering a black win
- standings updating after result entry
- invalid round/board selection returning error

- [ ] **Step 2: Run focused tests to verify failure**

Run:

```powershell
python -m pytest tests/unit/test_cli.py tests/unit/test_standings.py -q
```

Expected: FAIL for missing result-entry command.

- [ ] **Step 3: Implement tournament helpers**

Add small helpers on `Tournament`:

- `get_round(number: int) -> Round`
- `get_game(round_number: int, board_number: int) -> Game`

These should raise `ValueError` on bad lookup.

- [ ] **Step 4: Implement result entry command**

Add:

```text
enter-result <path> --round <n> --board <n> --winner black|white
```

Behavior:

- load tournament
- locate game
- write a completed result
- mark round completed if every game in that round is completed
- append audit event
- save tournament

- [ ] **Step 5: Run focused tests**

Run:

```powershell
python -m pytest tests/unit/test_cli.py tests/unit/test_standings.py -q
```

Expected: PASS.

- [ ] **Step 6: Run full suite**

Run:

```powershell
python -m pytest
```

Expected: PASS.

- [ ] **Step 7: Commit**

```powershell
git add src/pairing/cli src/pairing/domain tests/unit/test_cli.py tests/unit/test_standings.py
git commit -m "Add result entry workflow"
```

## Task 5: Later-Round Swiss Pairing

**Files:**
- Modify: `src/pairing/engine/history.py`
- Modify: `src/pairing/engine/bye.py`
- Modify: `src/pairing/engine/colours.py`
- Modify: `src/pairing/engine/swiss.py`
- Test: `tests/unit/test_swiss_pairing.py`

- [ ] **Step 1: Write failing later-round tests**

Add tests for:

- no repeated opponents when a legal alternative exists
- one bye for odd player count
- score-group ordering affects board order

- [ ] **Step 2: Run focused tests to verify failure**

Run:

```powershell
python -m pytest tests/unit/test_swiss_pairing.py -q
```

Expected: FAIL for later-round behavior.

- [ ] **Step 3: Implement history-aware later-round Swiss logic**

In `swiss.py`:

- use standings order after round 1
- group by score
- pair within each score group in deterministic order
- avoid repeated opponents with bounded swap/backtracking inside a group
- float one leftover player downward when necessary

- [ ] **Step 4: Implement bye and colour integration**

Use:

- bye helper to choose the eligible bye recipient
- colour helper to prefer better colour balance when assigning black/white

- [ ] **Step 5: Run focused tests**

Run:

```powershell
python -m pytest tests/unit/test_swiss_pairing.py -q
```

Expected: PASS.

- [ ] **Step 6: Run full suite**

Run:

```powershell
python -m pytest
```

Expected: PASS.

- [ ] **Step 7: Commit**

```powershell
git add src/pairing/engine tests/unit/test_swiss_pairing.py
git commit -m "Add later round Swiss pairing"
```

## Task 6: Regeneration and Explanations

**Files:**
- Modify: `src/pairing/domain/tournament.py`
- Modify: `src/pairing/engine/explanations.py`
- Modify: `src/pairing/engine/swiss.py`
- Modify: `src/pairing/cli/main.py`
- Modify: `README.md`
- Modify: `docs/tournament-file-format.md`
- Test: `tests/unit/test_cli.py`

- [ ] **Step 1: Write failing regeneration tests**

Add tests for:

- correcting an earlier result marks later rounds stale
- `regenerate-from --round N` rebuilds later rounds
- stale rounds block casual `pair-round`

- [ ] **Step 2: Run focused tests to verify failure**

Run:

```powershell
python -m pytest tests/unit/test_cli.py -q
```

Expected: FAIL for missing regeneration behavior.

- [ ] **Step 3: Add stale-round and regeneration helpers**

Add methods on `Tournament`:

- `mark_rounds_after_stale(round_number: int) -> None`
- `regenerate_from(round_number: int) -> None`

Use explicit, simple round deletion/rebuild rather than in-place mutation.

- [ ] **Step 4: Add CLI command**

Add:

```text
regenerate-from <path> --round <n>
```

Behavior:

- refuse if round `n` does not exist
- rebuild rounds after `n` using the current engine
- save and write audit event

- [ ] **Step 5: Update docs**

Update:

- `README.md` with Stage 2 command examples
- `docs/tournament-file-format.md` to show structured round/game/result objects

- [ ] **Step 6: Run focused tests**

Run:

```powershell
python -m pytest tests/unit/test_cli.py -q
```

Expected: PASS.

- [ ] **Step 7: Run full suite**

Run:

```powershell
python -m pytest
```

Expected: PASS.

- [ ] **Step 8: Commit**

```powershell
git add src/pairing/cli src/pairing/domain src/pairing/engine README.md docs/tournament-file-format.md tests/unit/test_cli.py
git commit -m "Add Swiss regeneration workflow"
```

## Self-Review Checklist

- Spec coverage: The plan covers all approved Stage 2 slices from the Stage 2 Swiss workflow spec.
- Placeholder scan: All tasks include exact file paths, concrete commands, and implementation direction sufficient for execution.
- Type consistency: `Round`, `Game`, `Result`, `StandingEntry`, and `generate_next_round` are introduced before later tasks depend on them.
