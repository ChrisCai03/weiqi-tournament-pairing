from __future__ import annotations

from dataclasses import asdict, dataclass, field


def _parse_bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"true", "1"}:
            return True
        if normalized in {"false", "0"}:
            return False
    raise ValueError(f"Invalid boolean value: {value!r}")


def _parse_tiebreak_order(value: object) -> list[str]:
    if not isinstance(value, list):
        raise ValueError("tiebreak_order must be a list")
    return [str(item) for item in value]


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
            allow_draws=_parse_bool(data.get("allow_draws", False)),
            rank_system=str(data.get("rank_system", "dan_kyu")),
            colour_policy=str(data.get("colour_policy", "balanced")),
            bye_policy=str(data.get("bye_policy", "lowest_score_no_previous_bye")),
            handicap_policy=str(data.get("handicap_policy", "none")),
            affiliation_policy=str(data.get("affiliation_policy", "avoid_when_possible")),
            tiebreak_order=_parse_tiebreak_order(data.get("tiebreak_order", ["score", "wins", "sos", "sosos"])),
            random_seed=int(data.get("random_seed", 1)),
        )
