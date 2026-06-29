from __future__ import annotations

from dataclasses import dataclass

from pairing.domain.validation import (
    require_choice,
    require_finite_number,
    require_non_blank,
    require_positive_integer,
)

PARTICIPATION_RECORD_STATUSES = frozenset({"absent", "withdrawn", "reentered", "late_entry"})


@dataclass(slots=True)
class ParticipationRecord:
    player_id: str
    round_number: int
    status: str
    reason: str = ""
    score_adjustment: float | None = None

    def validate(self, *, late_entry_missed_round_score: float = 0.0) -> None:
        self.player_id = require_non_blank(self.player_id, "Participation player id")
        self.round_number = require_positive_integer(self.round_number, "Participation round number")
        require_choice(self.status, PARTICIPATION_RECORD_STATUSES, "participation status")
        self.reason = self.reason.strip()
        if self.score_adjustment is None:
            self.score_adjustment = (
                late_entry_missed_round_score if self.status == "late_entry" else 0.0
            )
        self.score_adjustment = require_finite_number(
            float(self.score_adjustment),
            "Participation score adjustment",
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "player_id": self.player_id,
            "round_number": self.round_number,
            "status": self.status,
            "reason": self.reason,
            "score_adjustment": self.score_adjustment,
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "ParticipationRecord":
        score_adjustment = data.get("score_adjustment")
        return cls(
            player_id=str(data["player_id"]),
            round_number=_parse_positive_integer(data["round_number"], "Participation round number"),
            status=str(data["status"]),
            reason=str(data.get("reason", "")),
            score_adjustment=None if score_adjustment is None else float(score_adjustment),
        )


def _parse_positive_integer(value: object, label: str) -> int:
    if isinstance(value, bool):
        raise ValueError(f"{label} must be a positive integer.")
    if isinstance(value, int):
        return require_positive_integer(value, label)
    if isinstance(value, str):
        try:
            parsed = int(value.strip())
        except ValueError as exc:
            raise ValueError(f"{label} must be a positive integer.") from exc
        return require_positive_integer(parsed, label)
    raise ValueError(f"{label} must be a positive integer.")
