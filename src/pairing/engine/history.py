from __future__ import annotations

from pairing.domain.tournament import Tournament
from pairing.engine.scoring import counts_as_played


def opponent_ids_by_player(tournament: Tournament) -> dict[str, list[str]]:
    history: dict[str, list[str]] = {player.id: [] for player in tournament.players}
    for round_obj in tournament.rounds:
        if round_obj.status == "stale":
            continue
        for game in round_obj.games:
            if game.black_player_id is None or game.white_player_id is None:
                continue
            if not counts_as_played(game.result, tournament.config):
                continue
            history.setdefault(game.black_player_id, []).append(game.white_player_id)
            history.setdefault(game.white_player_id, []).append(game.black_player_id)
    return history


def players_have_met(
    opponent_history: dict[str, list[str]],
    player_one_id: str,
    player_two_id: str,
) -> bool:
    return player_two_id in opponent_history.get(player_one_id, [])


def colour_history_by_player(tournament: Tournament) -> dict[str, list[str]]:
    history: dict[str, list[str]] = {player.id: [] for player in tournament.players}
    for round_obj in tournament.rounds:
        if round_obj.status == "stale":
            continue
        for game in round_obj.games:
            if game.black_player_id is None or game.white_player_id is None:
                continue
            if not counts_as_played(game.result, tournament.config):
                continue
            history.setdefault(game.black_player_id, []).append("black")
            history.setdefault(game.white_player_id, []).append("white")
    return history
