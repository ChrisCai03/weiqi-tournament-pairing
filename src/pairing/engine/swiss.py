from __future__ import annotations

from pairing.domain.game import Game
from pairing.domain.player import Player
from pairing.domain.result import Result
from pairing.domain.round import Round
from pairing.domain.tournament import Tournament
from pairing.engine.bye import select_bye_player
from pairing.engine.colours import assign_colours
from pairing.engine.explanations import bye_explanation, round_pairing_explanation, round_summary


def generate_next_round(tournament: Tournament) -> Round:
    active_players = _sorted_active_players(tournament.players)
    if not active_players:
        raise ValueError("Tournament must have at least one active player.")

    round_number = tournament.next_round_number()
    if round_number > tournament.config.round_count:
        raise ValueError(
            f"Cannot pair round {round_number} beyond configured number of rounds "
            f"({tournament.config.round_count})."
        )
    paired_players = list(active_players)
    games: list[Game] = []

    if len(paired_players) % 2 == 1:
        bye_player = select_bye_player(paired_players)
        paired_players.remove(bye_player)
        bye_game = Game.create(
            round_number=round_number,
            board_number=1,
            black_player_id=bye_player.id,
            white_player_id=None,
            pairing_explanation=bye_explanation(round_number=round_number, player=bye_player),
        )
        bye_game.result = Result.completed(result_type="bye", winner_player_id=bye_player.id)
        games.append(bye_game)

    half_size = len(paired_players) // 2
    top_half = paired_players[:half_size]
    bottom_half = paired_players[half_size:]

    for top_player, bottom_player in zip(top_half, bottom_half, strict=True):
        board_number = len(games) + 1
        black_player_id, white_player_id = assign_colours(
            top_player,
            bottom_player,
            board_number=board_number,
        )
        games.append(
            Game.create(
                round_number=round_number,
                board_number=board_number,
                black_player_id=black_player_id,
                white_player_id=white_player_id,
                pairing_explanation=round_pairing_explanation(
                    round_number=round_number,
                    top_player=top_player,
                    bottom_player=bottom_player,
                ),
            )
        )

    games.sort(key=lambda game: game.board_number)
    return Round.create(
        number=round_number,
        games=games,
        pairing_method="swiss",
        pairing_seed=tournament.config.random_seed,
        explanation_summary=round_summary(round_number=round_number),
    )


def _sorted_active_players(players: list[Player]) -> list[Player]:
    return sorted(
        (player for player in players if player.status == "active"),
        key=lambda player: (-player.rank_sort_value, player.seed_number, player.id),
    )
