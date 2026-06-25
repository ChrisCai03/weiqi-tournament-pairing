from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from pairing.domain.config import TournamentConfig
from pairing.domain.result import Result

PlayerSide = Literal["black", "white"]


@dataclass(frozen=True, slots=True)
class ScoreContribution:
    score: float = 0.0
    wins: int = 0
    losses: int = 0
    draws: int = 0
    byes: int = 0
    forfeits: int = 0
    no_shows: int = 0


def result_contribution(result: Result, *, side: PlayerSide) -> ScoreContribution:
    score = result.black_score if side == "black" else result.white_score
    outcome_code = result.outcome_code
    if result.status != "completed" or outcome_code is None:
        return ScoreContribution(score=score or 0.0)
    if outcome_code == "draw":
        return ScoreContribution(score=score or 0.0, draws=1)
    if outcome_code == "bye":
        if side == "black":
            return ScoreContribution(score=score or 0.0, wins=1, byes=1)
        return ScoreContribution(score=score or 0.0)
    if outcome_code == "both_win":
        return ScoreContribution(score=score or 0.0, wins=1)
    if outcome_code == "both_loss":
        return ScoreContribution(score=score or 0.0, losses=1)
    if outcome_code == "both_no_show":
        return ScoreContribution(score=score or 0.0, no_shows=1)
    if outcome_code == "black_win":
        return _win_loss_contribution(score=score or 0.0, winner_side="black", side=side)
    if outcome_code == "white_win":
        return _win_loss_contribution(score=score or 0.0, winner_side="white", side=side)
    if outcome_code == "black_forfeit":
        contribution = _win_loss_contribution(score=score or 0.0, winner_side="black", side=side)
        if side == "white":
            return ScoreContribution(
                score=contribution.score,
                wins=contribution.wins,
                losses=contribution.losses,
                forfeits=1,
            )
        return contribution
    if outcome_code == "white_forfeit":
        contribution = _win_loss_contribution(score=score or 0.0, winner_side="white", side=side)
        if side == "black":
            return ScoreContribution(
                score=contribution.score,
                wins=contribution.wins,
                losses=contribution.losses,
                forfeits=1,
            )
        return contribution
    if outcome_code == "black_no_show":
        if side == "black":
            return ScoreContribution(score=score or 0.0, losses=1, no_shows=1)
        return ScoreContribution(score=score or 0.0, wins=1)
    if outcome_code == "white_no_show":
        if side == "white":
            return ScoreContribution(score=score or 0.0, losses=1, no_shows=1)
        return ScoreContribution(score=score or 0.0, wins=1)
    return ScoreContribution(score=score or 0.0)


def counts_as_played(result: Result, config: TournamentConfig) -> bool:
    if result.status != "completed":
        return False
    if result.outcome_code == "both_win":
        return config.count_both_win_as_played
    if result.outcome_code == "both_loss":
        return config.count_both_loss_as_played
    if result.outcome_code == "void":
        return config.count_void_as_played
    return result.result_type != "pending"


def _win_loss_contribution(
    *, score: float, winner_side: PlayerSide, side: PlayerSide
) -> ScoreContribution:
    if side == winner_side:
        return ScoreContribution(score=score, wins=1)
    return ScoreContribution(score=score, losses=1)
