from __future__ import annotations

from pairing.domain.game import Game
from pairing.domain.player import Player
from pairing.domain.player import parse_rank
from pairing.domain.result import Result
from pairing.domain.round import Round
from pairing.domain.tournament import Tournament
from pairing.engine.bye import ordered_later_round_bye_candidates
from pairing.engine.colours import assign_colours
from pairing.engine.explanations import bye_explanation, round_pairing_explanation, round_summary
from pairing.engine.history import colour_history_by_player, opponent_ids_by_player
from pairing.engine.pairing_core import pair_score_groups
from pairing.engine.standings import StandingEntry, calculate_standings


def mcmahon_starting_score(player: Player, tournament: Tournament) -> float:
    bar_sort_value = parse_rank(tournament.config.mcmahon_bar_rank).sort_value
    return 1.0 if player.rank_sort_value >= bar_sort_value else 0.0


def generate_next_round(tournament: Tournament) -> Round:
    active_players = [player for player in tournament.players if player.status == "active"]
    if not active_players:
        raise ValueError("Tournament must have at least one active player.")
    if any(round_obj.status == "stale" for round_obj in tournament.rounds):
        raise ValueError("Tournament has stale rounds that must be regenerated first.")

    round_number = tournament.next_round_number()
    if round_number > tournament.config.round_count:
        raise ValueError(
            f"Cannot pair round {round_number} beyond configured number of rounds "
            f"({tournament.config.round_count})."
        )

    games = _generate_round(
        tournament=tournament,
        round_number=round_number,
    )

    return Round.create(
        number=round_number,
        games=games,
        pairing_method="mcmahon",
        pairing_seed=tournament.config.random_seed,
        explanation_summary=round_summary(round_number=round_number, pairing_method="mcmahon"),
    )


def _generate_round(*, tournament: Tournament, round_number: int) -> list[Game]:
    standings = calculate_standings(
        tournament,
        starting_score_provider=lambda player: mcmahon_starting_score(player, tournament),
    )
    active_entries = [entry for entry in standings if entry.player.status == "active"]
    opponent_history = opponent_ids_by_player(tournament)
    colour_history = colour_history_by_player(tournament)
    games: list[Game] = []
    pairings: list[tuple[StandingEntry, StandingEntry]] | None = None

    if len(active_entries) % 2 == 1:
        for bye_entry in ordered_later_round_bye_candidates(active_entries):
            remaining_entries = [
                entry for entry in active_entries if entry.player.id != bye_entry.player.id
            ]
            pairings = pair_score_groups(remaining_entries, opponent_history)
            if pairings is None:
                continue

            games.append(
                _bye_game(round_number=round_number, player=bye_entry.player)
            )
            active_entries = remaining_entries
            break

        if pairings is None:
            raise ValueError("Unable to generate McMahon pairings without repeated opponents.")
    else:
        pairings = pair_score_groups(active_entries, opponent_history)
        if pairings is None:
            raise ValueError("Unable to generate McMahon pairings without repeated opponents.")

    for board_number, (top_entry, bottom_entry) in enumerate(pairings, start=len(games) + 1):
        black_player_id, white_player_id = assign_colours(
            top_entry.player,
            bottom_entry.player,
            board_number=board_number,
            colour_history=colour_history,
        )
        games.append(
            Game.create(
                round_number=round_number,
                board_number=board_number,
                black_player_id=black_player_id,
                white_player_id=white_player_id,
                pairing_explanation=round_pairing_explanation(
                    round_number=round_number,
                    top_player=top_entry.player,
                    bottom_player=bottom_entry.player,
                    pairing_method="mcmahon",
                ),
            )
        )

    games.sort(key=lambda game: game.board_number)
    return games


def _bye_game(*, round_number: int, player: Player) -> Game:
    bye_game = Game.create(
        round_number=round_number,
        board_number=1,
        black_player_id=player.id,
        white_player_id=None,
        pairing_explanation=bye_explanation(
            round_number=round_number,
            player=player,
            pairing_method="mcmahon",
        ),
    )
    bye_game.result = Result.completed(result_type="bye", winner_player_id=player.id)
    return bye_game
