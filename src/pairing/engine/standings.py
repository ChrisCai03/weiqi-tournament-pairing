from __future__ import annotations

from dataclasses import dataclass, field

from pairing.domain.player import Player
from pairing.domain.tournament import Tournament
from pairing.engine.history import colour_history_by_player, opponent_ids_by_player


@dataclass(slots=True)
class StandingEntry:
    player: Player
    score: float = 0.0
    wins: int = 0
    losses: int = 0
    byes: int = 0
    opponents: list[str] = field(default_factory=list)
    colours: list[str] = field(default_factory=list)
    sos: float = 0.0
    sosos: float = 0.0


def calculate_standings(tournament: Tournament) -> list[StandingEntry]:
    entries = {player.id: StandingEntry(player=player) for player in tournament.players}

    opponent_history = opponent_ids_by_player(tournament)
    colour_history = colour_history_by_player(tournament)
    for player_id, entry in entries.items():
        entry.opponents.extend(opponent_history.get(player_id, []))
        entry.colours.extend(colour_history.get(player_id, []))

    for round_obj in tournament.rounds:
        for game in round_obj.games:
            result = game.result
            if result.status != "completed":
                continue

            if result.result_type == "bye" and result.winner_player_id is not None:
                bye_entry = entries[result.winner_player_id]
                bye_entry.score += tournament.config.score_bye
                bye_entry.wins += 1
                bye_entry.byes += 1
                continue

            if game.black_player_id is None or game.white_player_id is None:
                continue

            black_entry = entries[game.black_player_id]
            white_entry = entries[game.white_player_id]

            if result.winner_player_id == game.black_player_id:
                black_entry.score += tournament.config.score_win
                black_entry.wins += 1
                white_entry.score += tournament.config.score_loss
                white_entry.losses += 1
            elif result.winner_player_id == game.white_player_id:
                white_entry.score += tournament.config.score_win
                white_entry.wins += 1
                black_entry.score += tournament.config.score_loss
                black_entry.losses += 1
            elif result.result_type == "draw":
                black_entry.score += tournament.config.score_draw
                white_entry.score += tournament.config.score_draw

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
