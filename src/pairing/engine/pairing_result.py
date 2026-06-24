from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PairingWarning:
    code: str
    message: str
    player_ids: tuple[str, ...] = ()
