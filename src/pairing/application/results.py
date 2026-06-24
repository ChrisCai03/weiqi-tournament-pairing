from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class CreateOutcome:
    path: Path


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
