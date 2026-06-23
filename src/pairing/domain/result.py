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

    def to_dict(self) -> dict[str, object]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "Result":
        return cls(
            status=str(data["status"]),
            result_type=str(data["result_type"]),
            winner_player_id=_optional_str(data.get("winner_player_id")),
            entered_at=_optional_str(data.get("entered_at")),
            entered_by=str(data.get("entered_by", "cli")),
            notes=str(data.get("notes", "")),
            correction_of=_optional_str(data.get("correction_of")),
        )


def _optional_str(value: object) -> str | None:
    if value is None:
        return None
    return str(value)
