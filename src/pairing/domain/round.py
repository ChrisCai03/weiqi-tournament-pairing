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
        _validate_unique_board_numbers(number, games)
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
        games = [Game.from_dict(dict(game)) for game in data.get("games", [])]
        number = int(data["number"])
        _validate_unique_board_numbers(number, games)
        return cls(
            number=number,
            status=str(data.get("status", "draft")),
            generated_at=str(data.get("generated_at", _utc_now_iso())),
            completed_at=_optional_str(data.get("completed_at")),
            pairing_method=str(data.get("pairing_method", "swiss")),
            pairing_seed=int(data.get("pairing_seed", 1)),
            games=games,
            is_regenerated=bool(data.get("is_regenerated", False)),
            supersedes_round_version=_optional_int(data.get("supersedes_round_version")),
            explanation_summary=[str(item) for item in data.get("explanation_summary", [])],
        )


def _optional_int(value: object) -> int | None:
    if value is None:
        return None
    return int(value)


def _optional_str(value: object) -> str | None:
    if value is None:
        return None
    return str(value)


def _validate_unique_board_numbers(number: int, games: list[Game]) -> None:
    board_numbers = [game.board_number for game in games]
    if len(board_numbers) != len(set(board_numbers)):
        raise ValueError(f"Duplicate board number in round {number}.")
