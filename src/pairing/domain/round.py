from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

from pairing.domain.game import Game
from pairing.domain.validation import (
    PAIRING_METHODS,
    ROUND_STATUSES,
    require_choice,
    require_positive,
    require_unique,
)


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
        _validate_games(number, games)
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

    def validate(self) -> None:
        require_positive(self.number, "Round number")
        require_choice(self.status, ROUND_STATUSES, "round status")
        require_choice(self.pairing_method, PAIRING_METHODS, "pairing method")
        require_unique((game.id for game in self.games), "game id")
        _validate_games(self.number, self.games)
        for game in self.games:
            game.validate()

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "Round":
        games = [Game.from_dict(dict(game)) for game in data.get("games", [])]
        number = int(data["number"])
        _validate_games(number, games)
        round_obj = cls(
            number=number,
            status=str(data["status"]),
            generated_at=str(data["generated_at"]),
            completed_at=_optional_str(data.get("completed_at")),
            pairing_method=str(data["pairing_method"]),
            pairing_seed=int(data["pairing_seed"]),
            games=games,
            is_regenerated=_parse_bool(data.get("is_regenerated", False)),
            supersedes_round_version=_optional_int(data.get("supersedes_round_version")),
            explanation_summary=[str(item) for item in data.get("explanation_summary", [])],
        )
        round_obj.validate()
        return round_obj


def _optional_int(value: object) -> int | None:
    if value is None:
        return None
    return int(value)


def _optional_str(value: object) -> str | None:
    if value is None:
        return None
    return str(value)


def _parse_bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    raise ValueError(f"Invalid boolean value: {value!r}")


def _validate_games(number: int, games: list[Game]) -> None:
    require_positive(number, "Round number")
    board_numbers = [game.board_number for game in games]
    if len(board_numbers) != len(set(board_numbers)):
        raise ValueError(f"Duplicate board number in round {number}.")
    for game in games:
        if game.round_number != number:
            raise ValueError(
                f"Game round number {game.round_number} does not match round {number}."
            )
