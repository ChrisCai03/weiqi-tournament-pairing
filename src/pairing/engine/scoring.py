from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from pairing.domain.config import TournamentConfig
from pairing.domain.game import Game
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


def result_contribution(
    result: Result,
    *,
    side: PlayerSide,
    config: TournamentConfig | None = None,
) -> ScoreContribution:
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
        return ScoreContribution(score=score or 0.0, losses=1, no_shows=1)
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


def player_game_contribution(
    game: Game,
    player_id: str,
    config: TournamentConfig,
) -> ScoreContribution:
    if game.black_player_id == player_id:
        if game.result.outcome_code is None and game.result.status == "completed":
            return _legacy_game_contribution(game=game, player_id=player_id, config=config)
        return result_contribution(game.result, side="black", config=config)
    if game.white_player_id == player_id:
        if game.result.outcome_code is None and game.result.status == "completed":
            return _legacy_game_contribution(game=game, player_id=player_id, config=config)
        return result_contribution(game.result, side="white", config=config)
    return ScoreContribution()


def counts_as_played(result: Result, config: TournamentConfig) -> bool:
    if result.status != "completed":
        return False
    if result.outcome_code is None and result.result_type == "void":
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


def _legacy_game_contribution(
    *,
    game: Game,
    player_id: str,
    config: TournamentConfig,
) -> ScoreContribution:
    result = game.result
    if result.result_type == "draw":
        return ScoreContribution(score=config.score_draw, draws=1)
    if result.result_type == "bye":
        return ScoreContribution(score=config.score_bye, wins=1, byes=1)
    if result.result_type == "both_win":
        return ScoreContribution(score=config.score_both_win, wins=1)
    if result.result_type == "both_loss":
        return ScoreContribution(score=config.score_both_loss, losses=1)
    if result.result_type == "void":
        return ScoreContribution()
    if result.result_type == "forfeit":
        if result.winner_player_id is None:
            return ScoreContribution()
        winner_side: PlayerSide = (
            "black" if result.winner_player_id == game.black_player_id else "white"
        )
        side: PlayerSide = "black" if player_id == game.black_player_id else "white"
        contribution = _win_loss_contribution(
            score=(
                config.score_forfeit_win
                if side == winner_side
                else config.score_forfeit_loss
            ),
            winner_side=winner_side,
            side=side,
        )
        if side != winner_side:
            return ScoreContribution(
                score=contribution.score,
                wins=contribution.wins,
                losses=contribution.losses,
                forfeits=1,
            )
        return contribution
    if result.result_type == "no_show":
        if result.winner_player_id is None:
            return ScoreContribution(score=config.score_no_show, losses=1, no_shows=1)
        if result.winner_player_id == player_id:
            return ScoreContribution(score=config.score_forfeit_win, wins=1)
        return ScoreContribution(score=config.score_no_show, losses=1, no_shows=1)
    if result.winner_player_id == player_id:
        return ScoreContribution(score=config.score_win, wins=1)
    return ScoreContribution(score=config.score_loss, losses=1)
