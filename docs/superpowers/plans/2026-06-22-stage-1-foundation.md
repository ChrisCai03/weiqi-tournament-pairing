# Stage 1 Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the first working Python foundation for the Weiqi tournament pairing app: package skeleton, domain models, JSON tournament files, dan/kyu rank parsing, CSV player import, and basic CLI commands.

**Architecture:** Keep domain objects pure and dependency-light. Store tournaments as schema-versioned `.tgo.json` files through a small storage boundary. Keep CLI commands thin: parse input, call domain/import/storage functions, and print concise results.

**Tech Stack:** Python 3.12+, standard-library dataclasses/json/csv/argparse, pytest, hypothesis for later property tests.

---

## Scope

This plan implements Stage 1 from the design spec. It intentionally does not implement Swiss pairings, standings, PDF export, manual overrides, or result correction. Those belong in later plans after the core file format and player import path are stable.

## File Structure

Create these files:

- `pyproject.toml`: package metadata, pytest configuration, console script.
- `README.md`: short project overview and first CLI examples.
- `src/pairing/__init__.py`: package marker.
- `src/pairing/domain/__init__.py`: domain exports.
- `src/pairing/domain/audit.py`: audit event dataclass and event factory.
- `src/pairing/domain/config.py`: tournament configuration dataclass.
- `src/pairing/domain/player.py`: player dataclass, statuses, rank parser.
- `src/pairing/domain/tournament.py`: tournament aggregate and serialization helpers.
- `src/pairing/storage/__init__.py`: storage exports.
- `src/pairing/storage/json_store.py`: atomic JSON save/load and schema checks.
- `src/pairing/import_export/__init__.py`: import/export package marker.
- `src/pairing/import_export/csv_import.py`: player CSV parser and validation report.
- `src/pairing/cli/__init__.py`: CLI package marker.
- `src/pairing/cli/main.py`: `create` and `import-players` commands.
- `tests/unit/test_rank_parser.py`: rank parser tests.
- `tests/unit/test_json_store.py`: JSON save/load tests.
- `tests/unit/test_csv_import.py`: CSV import validation tests.
- `tests/unit/test_cli.py`: CLI smoke tests.

Modify these files:

- `docs/superpowers/specs/2026-06-22-weiqi-tournament-design.md`: no change expected during Stage 1 unless implementation reveals an unavoidable design correction.

## Task 1: Project Skeleton and Test Harness

**Files:**
- Create: `pyproject.toml`
- Create: `README.md`
- Create: `src/pairing/__init__.py`
- Create: `src/pairing/domain/__init__.py`
- Create: `src/pairing/storage/__init__.py`
- Create: `src/pairing/import_export/__init__.py`
- Create: `src/pairing/cli/__init__.py`

- [ ] **Step 1: Create `pyproject.toml`**

```toml
[build-system]
requires = ["setuptools>=69"]
build-backend = "setuptools.build_meta"

[project]
name = "weiqi-tournament-pairing"
version = "0.1.0"
description = "Open-source Weiqi/Go tournament pairing software."
readme = "README.md"
requires-python = ">=3.12"
authors = [{ name = "ChrisCai03" }]
dependencies = []

[project.optional-dependencies]
dev = [
  "pytest>=8.0",
  "hypothesis>=6.0",
]

[project.scripts]
pairing = "pairing.cli.main:main"

[tool.setuptools.packages.find]
where = ["src"]

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["src"]
addopts = "-q"
```

- [ ] **Step 2: Create `README.md`**

```markdown
# Weiqi Tournament Pairing

Open-source tournament pairing software for Weiqi/Go and related board games.

The first prototype is a correctness-first Python CLI that stores tournaments as `.tgo.json` files and imports players from CSV.

## Stage 1 Commands

Create a tournament:

```powershell
python -m pairing.cli.main create example.tgo.json --name "Example Weiqi Open" --rounds 5
```

Import players:

```powershell
python -m pairing.cli.main import-players example.tgo.json players.csv
```
```

- [ ] **Step 3: Create package marker files**

Create each marker file with this content:

```python
"""Weiqi tournament pairing package."""
```

Files:

```text
src/pairing/__init__.py
src/pairing/domain/__init__.py
src/pairing/storage/__init__.py
src/pairing/import_export/__init__.py
src/pairing/cli/__init__.py
```

- [ ] **Step 4: Run test discovery**

Run:

```powershell
python -m pytest
```

Expected: pytest runs successfully and reports that no tests were collected, or it reports success once later tests exist.

- [ ] **Step 5: Commit**

```powershell
git add pyproject.toml README.md src/pairing
git commit -m "Add Python project skeleton"
```

## Task 2: Domain Models and Serialization

**Files:**
- Create: `src/pairing/domain/audit.py`
- Create: `src/pairing/domain/config.py`
- Create: `src/pairing/domain/player.py`
- Create: `src/pairing/domain/tournament.py`
- Modify: `src/pairing/domain/__init__.py`
- Test: `tests/unit/test_rank_parser.py`

- [ ] **Step 1: Write failing rank parser tests**

Create `tests/unit/test_rank_parser.py`:

```python
import pytest

from pairing.domain.player import RankParseError, parse_rank


@pytest.mark.parametrize(
    ("raw", "expected_label", "expected_sort"),
    [
        ("7d", "7d", 7),
        ("1 dan", "1d", 1),
        ("1d", "1d", 1),
        ("1k", "1k", -1),
        ("5 kyu", "5k", -5),
        ("30k", "30k", -30),
        ("unranked", "unranked", -999),
        ("", "unranked", -999),
        (None, "unranked", -999),
    ],
)
def test_parse_rank(raw, expected_label, expected_sort):
    rank = parse_rank(raw)
    assert rank.label == expected_label
    assert rank.sort_value == expected_sort


@pytest.mark.parametrize("raw", ["0d", "10d", "0k", "31k", "abc", "3x"])
def test_parse_rank_rejects_invalid_values(raw):
    with pytest.raises(RankParseError):
        parse_rank(raw)
```

- [ ] **Step 2: Run rank parser tests to verify failure**

Run:

```powershell
python -m pytest tests/unit/test_rank_parser.py -q
```

Expected: FAIL with `ModuleNotFoundError` or `ImportError` because `pairing.domain.player` does not exist yet.

- [ ] **Step 3: Implement `audit.py`**

```python
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from uuid import uuid4


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(slots=True)
class AuditLogEntry:
    id: str
    timestamp: str
    event_type: str
    actor: str
    summary: str
    round_number: int | None = None
    details: dict[str, object] = field(default_factory=dict)
    state_hash_before: str | None = None
    state_hash_after: str | None = None

    @classmethod
    def create(
        cls,
        event_type: str,
        summary: str,
        *,
        actor: str = "cli",
        round_number: int | None = None,
        details: dict[str, object] | None = None,
    ) -> "AuditLogEntry":
        return cls(
            id=str(uuid4()),
            timestamp=utc_now_iso(),
            event_type=event_type,
            actor=actor,
            summary=summary,
            round_number=round_number,
            details=details or {},
        )

    def to_dict(self) -> dict[str, object]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "AuditLogEntry":
        return cls(
            id=str(data["id"]),
            timestamp=str(data["timestamp"]),
            event_type=str(data["event_type"]),
            actor=str(data["actor"]),
            summary=str(data["summary"]),
            round_number=data.get("round_number"),  # type: ignore[arg-type]
            details=dict(data.get("details", {})),
            state_hash_before=data.get("state_hash_before"),  # type: ignore[arg-type]
            state_hash_after=data.get("state_hash_after"),  # type: ignore[arg-type]
        )
```

- [ ] **Step 4: Implement `config.py`**

```python
from __future__ import annotations

from dataclasses import asdict, dataclass, field


@dataclass(slots=True)
class TournamentConfig:
    round_count: int = 5
    pairing_method: str = "swiss"
    score_win: float = 1.0
    score_loss: float = 0.0
    score_draw: float = 0.5
    score_bye: float = 1.0
    allow_draws: bool = False
    rank_system: str = "dan_kyu"
    colour_policy: str = "balanced"
    bye_policy: str = "lowest_score_no_previous_bye"
    handicap_policy: str = "none"
    affiliation_policy: str = "avoid_when_possible"
    tiebreak_order: list[str] = field(default_factory=lambda: ["score", "wins", "sos", "sosos"])
    random_seed: int = 1

    def to_dict(self) -> dict[str, object]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "TournamentConfig":
        return cls(
            round_count=int(data.get("round_count", 5)),
            pairing_method=str(data.get("pairing_method", "swiss")),
            score_win=float(data.get("score_win", 1.0)),
            score_loss=float(data.get("score_loss", 0.0)),
            score_draw=float(data.get("score_draw", 0.5)),
            score_bye=float(data.get("score_bye", 1.0)),
            allow_draws=bool(data.get("allow_draws", False)),
            rank_system=str(data.get("rank_system", "dan_kyu")),
            colour_policy=str(data.get("colour_policy", "balanced")),
            bye_policy=str(data.get("bye_policy", "lowest_score_no_previous_bye")),
            handicap_policy=str(data.get("handicap_policy", "none")),
            affiliation_policy=str(data.get("affiliation_policy", "avoid_when_possible")),
            tiebreak_order=[str(item) for item in data.get("tiebreak_order", ["score", "wins", "sos", "sosos"])],
            random_seed=int(data.get("random_seed", 1)),
        )
```

- [ ] **Step 5: Implement `player.py`**

```python
from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from uuid import uuid4


class RankParseError(ValueError):
    """Raised when a dan/kyu rank cannot be parsed."""


@dataclass(frozen=True, slots=True)
class Rank:
    label: str
    sort_value: int


def parse_rank(raw: str | None) -> Rank:
    if raw is None or raw.strip() == "":
        return Rank(label="unranked", sort_value=-999)

    value = raw.strip().lower()
    if value in {"unranked", "unknown", "nr"}:
        return Rank(label="unranked", sort_value=-999)

    dan_match = re.fullmatch(r"(\d+)\s*d(?:an)?", value)
    if dan_match:
        number = int(dan_match.group(1))
        if 1 <= number <= 9:
            return Rank(label=f"{number}d", sort_value=number)
        raise RankParseError(f"Invalid dan rank: {raw}")

    kyu_match = re.fullmatch(r"(\d+)\s*k(?:yu)?", value)
    if kyu_match:
        number = int(kyu_match.group(1))
        if 1 <= number <= 30:
            return Rank(label=f"{number}k", sort_value=-number)
        raise RankParseError(f"Invalid kyu rank: {raw}")

    raise RankParseError(f"Invalid rank: {raw}")


@dataclass(slots=True)
class Player:
    id: str
    display_name: str
    rank: str
    rank_sort_value: int
    country: str = ""
    club: str = ""
    school: str = ""
    team_id: str = ""
    status: str = "active"
    seed_number: int = 0
    notes: str = ""

    @classmethod
    def create(
        cls,
        display_name: str,
        *,
        rank: str | None = None,
        country: str = "",
        club: str = "",
        school: str = "",
        team_id: str = "",
        seed_number: int = 0,
        notes: str = "",
    ) -> "Player":
        parsed_rank = parse_rank(rank)
        return cls(
            id=str(uuid4()),
            display_name=display_name.strip(),
            rank=parsed_rank.label,
            rank_sort_value=parsed_rank.sort_value,
            country=country.strip(),
            club=club.strip(),
            school=school.strip(),
            team_id=team_id.strip(),
            seed_number=seed_number,
            notes=notes.strip(),
        )

    def to_dict(self) -> dict[str, object]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "Player":
        return cls(
            id=str(data["id"]),
            display_name=str(data["display_name"]),
            rank=str(data["rank"]),
            rank_sort_value=int(data["rank_sort_value"]),
            country=str(data.get("country", "")),
            club=str(data.get("club", "")),
            school=str(data.get("school", "")),
            team_id=str(data.get("team_id", "")),
            status=str(data.get("status", "active")),
            seed_number=int(data.get("seed_number", 0)),
            notes=str(data.get("notes", "")),
        )
```

- [ ] **Step 6: Implement `tournament.py`**

```python
from __future__ import annotations

from dataclasses import dataclass, field
from uuid import uuid4

from pairing.domain.audit import AuditLogEntry
from pairing.domain.config import TournamentConfig
from pairing.domain.player import Player


SCHEMA_VERSION = 1


@dataclass(slots=True)
class Tournament:
    id: str
    name: str
    game_type: str
    format: str
    status: str
    schema_version: int
    config: TournamentConfig
    players: list[Player] = field(default_factory=list)
    teams: list[dict[str, object]] = field(default_factory=list)
    rounds: list[dict[str, object]] = field(default_factory=list)
    manual_overrides: list[dict[str, object]] = field(default_factory=list)
    audit_log: list[AuditLogEntry] = field(default_factory=list)

    @classmethod
    def create(cls, name: str, *, round_count: int = 5) -> "Tournament":
        config = TournamentConfig(round_count=round_count)
        tournament = cls(
            id=str(uuid4()),
            name=name.strip(),
            game_type="go",
            format="swiss",
            status="draft",
            schema_version=SCHEMA_VERSION,
            config=config,
        )
        tournament.audit_log.append(
            AuditLogEntry.create(
                "tournament_created",
                f"Created tournament '{tournament.name}' with {round_count} rounds.",
            )
        )
        return tournament

    def add_players(self, players: list[Player]) -> None:
        next_seed = len(self.players) + 1
        for index, player in enumerate(players):
            if player.seed_number == 0:
                player.seed_number = next_seed + index
            self.players.append(player)
        self.audit_log.append(
            AuditLogEntry.create(
                "players_imported",
                f"Imported {len(players)} players.",
                details={"count": len(players)},
            )
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "tournament": {
                "id": self.id,
                "name": self.name,
                "game_type": self.game_type,
                "format": self.format,
                "status": self.status,
            },
            "config": self.config.to_dict(),
            "players": [player.to_dict() for player in self.players],
            "teams": self.teams,
            "rounds": self.rounds,
            "manual_overrides": self.manual_overrides,
            "audit_log": [entry.to_dict() for entry in self.audit_log],
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "Tournament":
        tournament_data = dict(data["tournament"])  # type: ignore[arg-type]
        return cls(
            id=str(tournament_data["id"]),
            name=str(tournament_data["name"]),
            game_type=str(tournament_data.get("game_type", "go")),
            format=str(tournament_data.get("format", "swiss")),
            status=str(tournament_data.get("status", "draft")),
            schema_version=int(data.get("schema_version", SCHEMA_VERSION)),
            config=TournamentConfig.from_dict(dict(data.get("config", {}))),
            players=[Player.from_dict(dict(player)) for player in data.get("players", [])],  # type: ignore[arg-type]
            teams=[dict(team) for team in data.get("teams", [])],  # type: ignore[arg-type]
            rounds=[dict(round_data) for round_data in data.get("rounds", [])],  # type: ignore[arg-type]
            manual_overrides=[dict(item) for item in data.get("manual_overrides", [])],  # type: ignore[arg-type]
            audit_log=[AuditLogEntry.from_dict(dict(entry)) for entry in data.get("audit_log", [])],  # type: ignore[arg-type]
        )
```

- [ ] **Step 7: Export domain symbols**

Replace `src/pairing/domain/__init__.py` with:

```python
"""Domain models for Weiqi tournament pairing."""

from pairing.domain.audit import AuditLogEntry
from pairing.domain.config import TournamentConfig
from pairing.domain.player import Player, Rank, RankParseError, parse_rank
from pairing.domain.tournament import SCHEMA_VERSION, Tournament

__all__ = [
    "AuditLogEntry",
    "Player",
    "Rank",
    "RankParseError",
    "SCHEMA_VERSION",
    "Tournament",
    "TournamentConfig",
    "parse_rank",
]
```

- [ ] **Step 8: Run rank parser tests**

Run:

```powershell
python -m pytest tests/unit/test_rank_parser.py -q
```

Expected: PASS.

- [ ] **Step 9: Commit**

```powershell
git add src/pairing/domain tests/unit/test_rank_parser.py
git commit -m "Add tournament domain models"
```

## Task 3: JSON Tournament Store

**Files:**
- Create: `src/pairing/storage/json_store.py`
- Modify: `src/pairing/storage/__init__.py`
- Test: `tests/unit/test_json_store.py`

- [ ] **Step 1: Write failing JSON store tests**

Create `tests/unit/test_json_store.py`:

```python
import json

import pytest

from pairing.domain.tournament import Tournament
from pairing.storage.json_store import TournamentStoreError, load_tournament, save_tournament


def test_save_and_load_tournament_round_trip(tmp_path):
    path = tmp_path / "example.tgo.json"
    tournament = Tournament.create("Example Weiqi Open", round_count=5)

    save_tournament(tournament, path)
    loaded = load_tournament(path)

    assert loaded.name == "Example Weiqi Open"
    assert loaded.config.round_count == 5
    assert loaded.schema_version == 1
    assert loaded.audit_log[0].event_type == "tournament_created"


def test_load_rejects_unknown_schema_version(tmp_path):
    path = tmp_path / "bad.tgo.json"
    path.write_text(json.dumps({"schema_version": 999, "tournament": {}}), encoding="utf-8")

    with pytest.raises(TournamentStoreError, match="Unsupported schema version"):
        load_tournament(path)


def test_load_rejects_missing_file(tmp_path):
    with pytest.raises(TournamentStoreError, match="Tournament file not found"):
        load_tournament(tmp_path / "missing.tgo.json")
```

- [ ] **Step 2: Run JSON store tests to verify failure**

Run:

```powershell
python -m pytest tests/unit/test_json_store.py -q
```

Expected: FAIL because `pairing.storage.json_store` does not exist yet.

- [ ] **Step 3: Implement `json_store.py`**

```python
from __future__ import annotations

import json
import os
from pathlib import Path

from pairing.domain.tournament import SCHEMA_VERSION, Tournament


class TournamentStoreError(RuntimeError):
    """Raised when a tournament file cannot be loaded or saved."""


def save_tournament(tournament: Tournament, path: str | Path) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    temp_path = target.with_name(f".{target.name}.tmp")
    payload = json.dumps(tournament.to_dict(), indent=2, sort_keys=True)
    temp_path.write_text(payload + "\n", encoding="utf-8")
    os.replace(temp_path, target)


def load_tournament(path: str | Path) -> Tournament:
    source = Path(path)
    if not source.exists():
        raise TournamentStoreError(f"Tournament file not found: {source}")

    try:
        data = json.loads(source.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise TournamentStoreError(f"Invalid tournament JSON: {source}") from exc

    schema_version = int(data.get("schema_version", 0))
    if schema_version != SCHEMA_VERSION:
        raise TournamentStoreError(f"Unsupported schema version: {schema_version}")

    return Tournament.from_dict(data)
```

- [ ] **Step 4: Export storage symbols**

Replace `src/pairing/storage/__init__.py` with:

```python
"""Storage adapters for tournament files."""

from pairing.storage.json_store import TournamentStoreError, load_tournament, save_tournament

__all__ = ["TournamentStoreError", "load_tournament", "save_tournament"]
```

- [ ] **Step 5: Run JSON store tests**

Run:

```powershell
python -m pytest tests/unit/test_json_store.py -q
```

Expected: PASS.

- [ ] **Step 6: Run all current tests**

Run:

```powershell
python -m pytest
```

Expected: PASS.

- [ ] **Step 7: Commit**

```powershell
git add src/pairing/storage tests/unit/test_json_store.py
git commit -m "Add JSON tournament storage"
```

## Task 4: CSV Player Import

**Files:**
- Create: `src/pairing/import_export/csv_import.py`
- Modify: `src/pairing/import_export/__init__.py`
- Test: `tests/unit/test_csv_import.py`

- [ ] **Step 1: Write failing CSV import tests**

Create `tests/unit/test_csv_import.py`:

```python
from pairing.import_export.csv_import import import_players_from_csv_text


def test_import_players_from_csv_text():
    csv_text = "name,rank,country,club,school,team,notes\nAlice,3d,SG,Club A,School A,,Captain\nBob,5k,SG,Club B,School B,,\n"

    report = import_players_from_csv_text(csv_text)

    assert report.valid
    assert len(report.players) == 2
    assert report.players[0].display_name == "Alice"
    assert report.players[0].rank == "3d"
    assert report.players[1].rank_sort_value == -5
    assert report.warnings == []


def test_import_reports_missing_name_and_invalid_rank():
    csv_text = "name,rank\n,3d\nCharlie,35k\n"

    report = import_players_from_csv_text(csv_text)

    assert not report.valid
    assert len(report.players) == 0
    assert "Row 2: missing player name." in report.errors
    assert "Row 3: Invalid kyu rank: 35k" in report.errors


def test_import_warns_about_unknown_columns_and_duplicate_names():
    csv_text = "name,rank,extra\nAlice,1d,ignored\nAlice,2d,ignored\n"

    report = import_players_from_csv_text(csv_text)

    assert report.valid
    assert len(report.players) == 2
    assert "Unknown columns ignored: extra." in report.warnings
    assert "Duplicate player name imported: Alice." in report.warnings
```

- [ ] **Step 2: Run CSV import tests to verify failure**

Run:

```powershell
python -m pytest tests/unit/test_csv_import.py -q
```

Expected: FAIL because `pairing.import_export.csv_import` does not exist yet.

- [ ] **Step 3: Implement `csv_import.py`**

```python
from __future__ import annotations

import csv
from dataclasses import dataclass, field
from io import StringIO
from pathlib import Path

from pairing.domain.player import Player, RankParseError


EXPECTED_COLUMNS = {"name", "rank", "country", "club", "school", "team", "notes"}


@dataclass(slots=True)
class PlayerImportReport:
    players: list[Player] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def valid(self) -> bool:
        return not self.errors


def import_players_from_csv(path: str | Path) -> PlayerImportReport:
    return import_players_from_csv_text(Path(path).read_text(encoding="utf-8-sig"))


def import_players_from_csv_text(csv_text: str) -> PlayerImportReport:
    report = PlayerImportReport()
    reader = csv.DictReader(StringIO(csv_text))

    if reader.fieldnames is None:
        report.errors.append("CSV is missing a header row.")
        return report

    normalized_fields = [field.strip().lower() for field in reader.fieldnames]
    unknown_columns = sorted(set(normalized_fields) - EXPECTED_COLUMNS)
    if unknown_columns:
        report.warnings.append(f"Unknown columns ignored: {', '.join(unknown_columns)}.")

    seen_names: set[str] = set()
    pending_players: list[Player] = []

    for row_number, row in enumerate(reader, start=2):
        normalized_row = {
            (key.strip().lower() if key is not None else ""): (value or "").strip()
            for key, value in row.items()
        }
        name = normalized_row.get("name", "")
        if not name:
            report.errors.append(f"Row {row_number}: missing player name.")
            continue

        if name.lower() in seen_names:
            report.warnings.append(f"Duplicate player name imported: {name}.")
        seen_names.add(name.lower())

        try:
            pending_players.append(
                Player.create(
                    name,
                    rank=normalized_row.get("rank", ""),
                    country=normalized_row.get("country", ""),
                    club=normalized_row.get("club", ""),
                    school=normalized_row.get("school", ""),
                    team_id=normalized_row.get("team", ""),
                    notes=normalized_row.get("notes", ""),
                )
            )
        except RankParseError as exc:
            report.errors.append(f"Row {row_number}: {exc}")

    if report.errors:
        report.players = []
    else:
        report.players = pending_players
    return report
```

- [ ] **Step 4: Export import symbols**

Replace `src/pairing/import_export/__init__.py` with:

```python
"""Import and export utilities."""

from pairing.import_export.csv_import import (
    PlayerImportReport,
    import_players_from_csv,
    import_players_from_csv_text,
)

__all__ = ["PlayerImportReport", "import_players_from_csv", "import_players_from_csv_text"]
```

- [ ] **Step 5: Run CSV import tests**

Run:

```powershell
python -m pytest tests/unit/test_csv_import.py -q
```

Expected: PASS.

- [ ] **Step 6: Run all current tests**

Run:

```powershell
python -m pytest
```

Expected: PASS.

- [ ] **Step 7: Commit**

```powershell
git add src/pairing/import_export tests/unit/test_csv_import.py
git commit -m "Add CSV player import"
```

## Task 5: CLI Create and Import Commands

**Files:**
- Create: `src/pairing/cli/main.py`
- Test: `tests/unit/test_cli.py`
- Modify: `README.md`

- [ ] **Step 1: Write failing CLI tests**

Create `tests/unit/test_cli.py`:

```python
import csv

from pairing.cli.main import main
from pairing.storage.json_store import load_tournament


def test_cli_create_command(tmp_path):
    tournament_path = tmp_path / "example.tgo.json"

    exit_code = main(["create", str(tournament_path), "--name", "Example Weiqi Open", "--rounds", "5"])

    assert exit_code == 0
    tournament = load_tournament(tournament_path)
    assert tournament.name == "Example Weiqi Open"
    assert tournament.config.round_count == 5


def test_cli_import_players_command(tmp_path):
    tournament_path = tmp_path / "example.tgo.json"
    players_path = tmp_path / "players.csv"
    with players_path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=["name", "rank"])
        writer.writeheader()
        writer.writerow({"name": "Alice", "rank": "3d"})
        writer.writerow({"name": "Bob", "rank": "5k"})

    assert main(["create", str(tournament_path), "--name", "Example Weiqi Open"]) == 0
    assert main(["import-players", str(tournament_path), str(players_path)]) == 0

    tournament = load_tournament(tournament_path)
    assert [player.display_name for player in tournament.players] == ["Alice", "Bob"]
    assert [player.seed_number for player in tournament.players] == [1, 2]
```

- [ ] **Step 2: Run CLI tests to verify failure**

Run:

```powershell
python -m pytest tests/unit/test_cli.py -q
```

Expected: FAIL because `pairing.cli.main` does not exist yet.

- [ ] **Step 3: Implement `main.py`**

```python
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from pairing.domain.tournament import Tournament
from pairing.import_export.csv_import import import_players_from_csv
from pairing.storage.json_store import load_tournament, save_tournament


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="pairing")
    subparsers = parser.add_subparsers(dest="command", required=True)

    create_parser = subparsers.add_parser("create", help="Create a tournament file.")
    create_parser.add_argument("path", help="Output .tgo.json path.")
    create_parser.add_argument("--name", required=True, help="Tournament name.")
    create_parser.add_argument("--rounds", type=int, default=5, help="Number of rounds.")

    import_parser = subparsers.add_parser("import-players", help="Import players from CSV.")
    import_parser.add_argument("tournament_path", help="Existing .tgo.json tournament file.")
    import_parser.add_argument("csv_path", help="Player CSV file.")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "create":
        tournament = Tournament.create(args.name, round_count=args.rounds)
        save_tournament(tournament, Path(args.path))
        print(f"Created tournament: {args.path}")
        return 0

    if args.command == "import-players":
        tournament = load_tournament(Path(args.tournament_path))
        report = import_players_from_csv(Path(args.csv_path))
        for warning in report.warnings:
            print(f"Warning: {warning}", file=sys.stderr)
        if not report.valid:
            for error in report.errors:
                print(f"Error: {error}", file=sys.stderr)
            return 1
        tournament.add_players(report.players)
        save_tournament(tournament, Path(args.tournament_path))
        print(f"Imported {len(report.players)} players.")
        return 0

    parser.error(f"Unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run CLI tests**

Run:

```powershell
python -m pytest tests/unit/test_cli.py -q
```

Expected: PASS.

- [ ] **Step 5: Run a manual CLI smoke test**

Run:

```powershell
python -m pairing.cli.main create .tmp-example.tgo.json --name "Example Weiqi Open" --rounds 5
```

Expected output:

```text
Created tournament: .tmp-example.tgo.json
```

Then run:

```powershell
Remove-Item .tmp-example.tgo.json
```

Expected: file removed.

- [ ] **Step 6: Update `README.md` command section if actual command output differs**

Only change the examples if the implemented CLI syntax differs from the README examples created in Task 1. Keep the README focused on Stage 1 usage.

- [ ] **Step 7: Run all tests**

Run:

```powershell
python -m pytest
```

Expected: PASS.

- [ ] **Step 8: Commit**

```powershell
git add src/pairing/cli tests/unit/test_cli.py README.md
git commit -m "Add tournament CLI foundation"
```

## Task 6: Documentation for Stage 1 Data Formats

**Files:**
- Create: `docs/csv-format.md`
- Create: `docs/tournament-file-format.md`
- Modify: `README.md`

- [ ] **Step 1: Create `docs/csv-format.md`**

```markdown
# CSV Player Import Format

The Stage 1 player import command accepts UTF-8 CSV files with a header row.

## Columns

Required:

- `name`
- `rank`

Optional:

- `country`
- `club`
- `school`
- `team`
- `notes`

Unknown columns are ignored with a warning.

## Rank Values

Accepted rank examples:

- `7d`
- `1d`
- `1 dan`
- `1k`
- `5k`
- `5 kyu`
- `unranked`

Dan ranks must be `1d` through `9d`. Kyu ranks must be `1k` through `30k`.
```

- [ ] **Step 2: Create `docs/tournament-file-format.md`**

```markdown
# Tournament File Format

The MVP stores tournaments as a single JSON file with the extension `.tgo.json`.

## Schema Version

Stage 1 uses `schema_version: 1`.

## Top-Level Shape

```json
{
  "schema_version": 1,
  "tournament": {
    "id": "uuid",
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

The file is designed to be inspectable and versioned. Users may read it directly, but app commands should be preferred for editing.
```

- [ ] **Step 3: Update `README.md` with documentation links**

Append:

```markdown
## Documentation

- [Design spec](docs/superpowers/specs/2026-06-22-weiqi-tournament-design.md)
- [CSV player import format](docs/csv-format.md)
- [Tournament file format](docs/tournament-file-format.md)
```

- [ ] **Step 4: Run all tests**

Run:

```powershell
python -m pytest
```

Expected: PASS.

- [ ] **Step 5: Commit**

```powershell
git add README.md docs/csv-format.md docs/tournament-file-format.md
git commit -m "Document Stage 1 file formats"
```

## Task 7: Final Stage 1 Verification

**Files:**
- Modify only if verification exposes a concrete issue in files created by Tasks 1-6.

- [ ] **Step 1: Run full test suite**

Run:

```powershell
python -m pytest
```

Expected: PASS.

- [ ] **Step 2: Run CLI end-to-end smoke test**

Create `sample-players.csv`:

```csv
name,rank,country,club,school,team,notes
Alice,3d,SG,Club A,School A,,Captain
Bob,5k,SG,Club B,School B,,
Charlie,1k,SG,Club C,School C,,
```

Run:

```powershell
python -m pairing.cli.main create sample.tgo.json --name "Sample Weiqi Open" --rounds 5
python -m pairing.cli.main import-players sample.tgo.json sample-players.csv
```

Expected output includes:

```text
Created tournament: sample.tgo.json
Imported 3 players.
```

- [ ] **Step 3: Inspect saved tournament**

Run:

```powershell
Get-Content sample.tgo.json
```

Expected: JSON includes `schema_version`, `tournament`, `config`, three `players`, and audit events for creation and import.

- [ ] **Step 4: Remove smoke-test files**

Run:

```powershell
Remove-Item sample.tgo.json
Remove-Item sample-players.csv
```

Expected: files removed.

- [ ] **Step 5: Confirm clean working tree**

Run:

```powershell
git status -sb
```

Expected:

```text
## main...origin/main
```

- [ ] **Step 6: Push commits**

Run:

```powershell
git push
```

Expected: all Stage 1 commits are pushed to `origin/main`.

## Self-Review Checklist

- Spec coverage: This plan covers Stage 1 data model, CLI prototype, JSON save/load, rank parsing, CSV import, and documentation. Swiss pairing, standings, exports, and UI are intentionally outside this plan and should receive separate plans.
- Placeholder scan: The plan uses concrete paths, code, commands, and expected outcomes.
- Type consistency: `Tournament`, `TournamentConfig`, `Player`, `AuditLogEntry`, `load_tournament`, `save_tournament`, and `import_players_from_csv_text` are introduced before later tasks use them.
