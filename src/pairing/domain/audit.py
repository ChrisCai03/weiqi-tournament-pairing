from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from uuid import uuid4


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _optional_int(value: object) -> int | None:
    if value is None:
        return None
    return int(value)


def _optional_str(value: object) -> str | None:
    if value is None:
        return None
    return str(value)


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
    signature: str | None = None

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
            round_number=_optional_int(data.get("round_number")),
            details=dict(data.get("details", {})),
            state_hash_before=_optional_str(data.get("state_hash_before")),
            state_hash_after=_optional_str(data.get("state_hash_after")),
            signature=_optional_str(data.get("signature")),
        )
