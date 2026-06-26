from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

from pairing.domain.player import Player
from pairing.domain.tournament import Tournament
from pairing.engine.history import colour_history_by_player, opponent_ids_by_player
from pairing.engine.scoring import player_game_contribution


@dataclass(slots=True)
class StandingEntry:
    player: Player
    starting_score: float = 0.0
    game_score: float = 0.0
    score: float = 0.0
    wins: int = 0
    losses: int = 0
    draws: int = 0
    byes: int = 0
    opponents: list[str] = field(default_factory=list)
    colours: list[str] = field(default_factory=list)
    sos: float = 0.0
    sosos: float = 0.0


def calculate_standings(
    tournament: Tournament,
    *,
    starting_score_provider: Callable[[Player], float] | None = None,
) -> list[StandingEntry]:
    entries = {}
    for player in tournament.players:
        starting_score = (
            starting_score_provider(player) if starting_score_provider is not None else 0.0
        )
        entries[player.id] = StandingEntry(
            player=player,
            starting_score=starting_score,
            score=starting_score,
        )

    opponent_history = opponent_ids_by_player(tournament)
    colour_history = colour_history_by_player(tournament)
    for player_id, entry in entries.items():
        entry.opponents.extend(opponent_history.get(player_id, []))
        entry.colours.extend(colour_history.get(player_id, []))

    for round_obj in tournament.rounds:
        if round_obj.status == "stale":
            continue
        for game in round_obj.games:
            for player_id in (game.black_player_id, game.white_player_id):
                if player_id is None:
                    continue
                entry = entries[player_id]
                contribution = player_game_contribution(game, player_id, tournament.config)
                entry.game_score += contribution.score
                entry.score += contribution.score
                entry.wins += contribution.wins
                entry.losses += contribution.losses
                entry.draws += contribution.draws
                entry.byes += contribution.byes

    for entry in entries.values():
        entry.sos = sum(entries[opponent_id].score for opponent_id in entry.opponents)
    for entry in entries.values():
        entry.sosos = sum(entries[opponent_id].sos for opponent_id in entry.opponents)

    return sorted(
        entries.values(),
        key=lambda entry: (
            -entry.score,
            -entry.wins,
            -entry.sos,
            -entry.sosos,
            -entry.player.rank_sort_value,
            entry.player.seed_number,
            entry.player.id,
        ),
    )
