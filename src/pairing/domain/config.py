from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Final

from pairing.domain.player import parse_rank
from pairing.domain.validation import (
    AFFILIATION_POLICIES,
    BYE_POLICIES,
    COLOUR_POLICIES,
    HANDICAP_POLICIES,
    PAIRING_METHODS,
    RANK_SYSTEMS,
    TIEBREAKS,
    require_choice,
    require_finite_number,
    require_positive,
)

_DEFAULT_TIEBREAK_ORDER: Final[list[str]] = ["score", "wins", "sos", "sosos"]
_SCORE_FIELD_LABELS: Final[tuple[tuple[str, str], ...]] = (
    ("score_win", "Win score"),
    ("score_loss", "Loss score"),
    ("score_draw", "Draw score"),
    ("score_bye", "Bye score"),
    ("score_both_win", "Both-win score"),
    ("score_both_loss", "Both-loss score"),
    ("score_forfeit_win", "Forfeit win score"),
    ("score_forfeit_loss", "Forfeit loss score"),
    ("score_no_show", "No-show score"),
    ("late_entry_missed_round_score", "Late-entry missed-round score"),
)


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


def _parse_round_count(value: object) -> int:
    round_count = int(value)
    if round_count <= 0:
        raise ValueError("Round count must be positive.")
    return round_count


@dataclass(slots=True)
class TournamentConfig:
    round_count: int = 5
    pairing_method: str = "swiss"
    mcmahon_bar_rank: str = "1d"
    score_win: float = 1.0
    score_loss: float = 0.0
    score_draw: float = 0.5
    score_bye: float = 1.0
    score_both_win: float = 1.0
    score_both_loss: float = 0.0
    score_forfeit_win: float = 1.0
    score_forfeit_loss: float = 0.0
    score_no_show: float = 0.0
    late_entry_missed_round_score: float = 0.0
    allow_draws: bool = False
    count_both_win_as_played: bool = True
    count_both_loss_as_played: bool = True
    count_void_as_played: bool = False
    automatic_backup_before_destructive_change: bool = True
    backup_retention_count: int = 10
    rank_system: str = "dan_kyu"
    colour_policy: str = "balanced"
    bye_policy: str = "lowest_score_no_previous_bye"
    handicap_policy: str = "none"
    affiliation_policy: str = "avoid_when_possible"
    tiebreak_order: list[str] = field(default_factory=lambda: list(_DEFAULT_TIEBREAK_ORDER))
    random_seed: int = 1

    def to_dict(self) -> dict[str, object]:
        return asdict(self)

    def validate(self) -> None:
        _parse_round_count(self.round_count)
        require_choice(self.pairing_method, PAIRING_METHODS, "pairing method")
        require_choice(self.rank_system, RANK_SYSTEMS, "rank system")
        require_choice(self.colour_policy, COLOUR_POLICIES, "colour policy")
        require_choice(self.bye_policy, BYE_POLICIES, "bye policy")
        require_choice(self.handicap_policy, HANDICAP_POLICIES, "handicap policy")
        require_choice(
            self.affiliation_policy,
            AFFILIATION_POLICIES,
            "affiliation policy",
        )
        bar_rank = parse_rank(self.mcmahon_bar_rank)
        if bar_rank.label == "unranked":
            raise ValueError("McMahon bar rank must be ranked.")
        for field_name, label in _SCORE_FIELD_LABELS:
            require_finite_number(float(getattr(self, field_name)), label)
        require_positive(self.backup_retention_count, "Backup retention count")
        if not self.tiebreak_order:
            raise ValueError("tiebreak_order must not be empty")
        for tiebreak in self.tiebreak_order:
            require_choice(tiebreak, TIEBREAKS, "tiebreak")

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "TournamentConfig":
        config = cls(
            round_count=_parse_round_count(data.get("round_count", 5)),
            pairing_method=str(data.get("pairing_method", "swiss")),
            mcmahon_bar_rank=str(data.get("mcmahon_bar_rank", "1d")),
            score_win=float(data.get("score_win", 1.0)),
            score_loss=float(data.get("score_loss", 0.0)),
            score_draw=float(data.get("score_draw", 0.5)),
            score_bye=float(data.get("score_bye", 1.0)),
            score_both_win=float(data.get("score_both_win", 1.0)),
            score_both_loss=float(data.get("score_both_loss", 0.0)),
            score_forfeit_win=float(data.get("score_forfeit_win", 1.0)),
            score_forfeit_loss=float(data.get("score_forfeit_loss", 0.0)),
            score_no_show=float(data.get("score_no_show", 0.0)),
            late_entry_missed_round_score=float(data.get("late_entry_missed_round_score", 0.0)),
            allow_draws=_parse_bool(data.get("allow_draws", False)),
            count_both_win_as_played=_parse_bool(data.get("count_both_win_as_played", True)),
            count_both_loss_as_played=_parse_bool(data.get("count_both_loss_as_played", True)),
            count_void_as_played=_parse_bool(data.get("count_void_as_played", False)),
            automatic_backup_before_destructive_change=_parse_bool(
                data.get("automatic_backup_before_destructive_change", True)
            ),
            backup_retention_count=int(data.get("backup_retention_count", 10)),
            rank_system=str(data.get("rank_system", "dan_kyu")),
            colour_policy=str(data.get("colour_policy", "balanced")),
            bye_policy=str(data.get("bye_policy", "lowest_score_no_previous_bye")),
            handicap_policy=str(data.get("handicap_policy", "none")),
            affiliation_policy=str(data.get("affiliation_policy", "avoid_when_possible")),
            tiebreak_order=_parse_tiebreak_order(
                data.get("tiebreak_order", list(_DEFAULT_TIEBREAK_ORDER))
            ),
            random_seed=int(data.get("random_seed", 1)),
        )
        config.validate()
        return config
