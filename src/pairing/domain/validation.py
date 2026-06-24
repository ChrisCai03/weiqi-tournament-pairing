from __future__ import annotations

from collections.abc import Hashable, Iterable

TOURNAMENT_FORMATS = frozenset({"swiss", "mcmahon"})
TOURNAMENT_STATUSES = frozenset({"draft", "active", "completed"})
PLAYER_STATUSES = frozenset({"active", "withdrawn"})
ROUND_STATUSES = frozenset({"draft", "published", "completed", "stale"})
RESULT_STATUSES = frozenset({"pending", "completed"})
RESULT_TYPES = frozenset({"pending", "normal", "bye"})
PAIRING_METHODS = frozenset({"swiss", "mcmahon"})
RANK_SYSTEMS = frozenset({"dan_kyu"})
COLOUR_POLICIES = frozenset({"balanced"})
BYE_POLICIES = frozenset({"lowest_score_no_previous_bye"})
HANDICAP_POLICIES = frozenset({"none"})
AFFILIATION_POLICIES = frozenset({"avoid_when_possible"})
TIEBREAKS = frozenset({"score", "wins", "sos", "sosos"})


def require_non_blank(value: str, label: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{label} must not be blank.")
    return normalized


def require_choice(value: str, choices: frozenset[str], label: str) -> str:
    if value not in choices:
        raise ValueError(f"Unsupported {label}: {value!r}.")
    return value


def require_positive(value: int, label: str) -> int:
    if value <= 0:
        raise ValueError(f"{label} must be positive.")
    return value


def require_unique(values: Iterable[Hashable], label: str) -> None:
    seen: set[Hashable] = set()
    for value in values:
        if value in seen:
            raise ValueError(f"Duplicate {label}: {value}.")
        seen.add(value)
