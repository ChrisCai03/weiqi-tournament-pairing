from __future__ import annotations

from pairing.domain.game import Game
from pairing.domain.player import Player
from pairing.domain.result import Result
from pairing.domain.round import Round
from pairing.domain.tournament import Tournament
from pairing.engine.bye import ordered_later_round_bye_candidates, select_bye_player
from pairing.engine.colours import assign_colours
from pairing.engine.explanations import bye_explanation, round_pairing_explanation, round_summary
from pairing.engine.history import colour_history_by_player, opponent_ids_by_player
from pairing.engine.pairing_core import pair_score_groups, pair_score_groups_with_fallback
from pairing.engine.pairing_result import PairingWarning
from pairing.engine.progression import validate_next_round_allowed
from pairing.engine.standings import StandingEntry, calculate_standings


def generate_next_round(tournament: Tournament) -> Round:
    validate_next_round_allowed(tournament)
    active_players = _sorted_active_players(tournament.players)
    if not active_players:
        raise ValueError("Tournament must have at least one active player.")
    round_number = tournament.next_round_number()
    if round_number > tournament.config.round_count:
        raise ValueError(
            f"Cannot pair round {round_number} beyond configured number of rounds "
            f"({tournament.config.round_count})."
        )
    if round_number == 1:
        games = _generate_first_round(
            tournament=tournament, active_players=active_players, round_number=round_number
        )
        warnings: list[PairingWarning] = []
    else:
        games, warnings = _generate_later_round(
            tournament=tournament,
            round_number=round_number,
        )

    return Round.create(
        number=round_number,
        games=games,
        pairing_method="swiss",
        pairing_seed=tournament.config.random_seed,
        explanation_summary=round_summary(round_number=round_number)
        + [warning.message for warning in warnings],
    )


def _generate_first_round(
    *, tournament: Tournament, active_players: list[Player], round_number: int
) -> list[Game]:
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
        bye_game.result = Result.completed_outcome(
            outcome_code="bye",
            black_player_id=bye_player.id,
            white_player_id=None,
            config=tournament.config,
        )
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
    return games


def _generate_later_round(
    *,
    tournament: Tournament,
    round_number: int,
) -> tuple[list[Game], list[PairingWarning]]:
    standings = calculate_standings(tournament)
    active_entries = [entry for entry in standings if entry.player.status == "active"]
    opponent_history = opponent_ids_by_player(tournament)
    colour_history = colour_history_by_player(tournament)
    games: list[Game] = []
    pairings: list[tuple[StandingEntry, StandingEntry]] | None = None
    warnings: list[PairingWarning] = []

    if len(active_entries) % 2 == 1:
        for bye_entry in ordered_later_round_bye_candidates(active_entries):
            remaining_entries = [
                entry for entry in active_entries if entry.player.id != bye_entry.player.id
            ]
            pairings = pair_score_groups(remaining_entries, opponent_history)
            if pairings is None:
                continue

            active_entries = remaining_entries
            bye_game = Game.create(
                round_number=round_number,
                board_number=1,
                black_player_id=bye_entry.player.id,
                white_player_id=None,
                pairing_explanation=bye_explanation(
                    round_number=round_number, player=bye_entry.player
                ),
            )
            bye_game.result = Result.completed_outcome(
                outcome_code="bye",
                black_player_id=bye_entry.player.id,
                white_player_id=None,
                config=tournament.config,
            )
            games.append(bye_game)
            break

        if pairings is None:
            bye_entry = ordered_later_round_bye_candidates(active_entries)[0]
            remaining_entries = [
                entry for entry in active_entries if entry.player.id != bye_entry.player.id
            ]
            pairings, warnings = pair_score_groups_with_fallback(
                remaining_entries,
                opponent_history,
            )
            games.append(
                _bye_game(
                    round_number=round_number,
                    player=bye_entry.player,
                    config=tournament.config,
                )
            )
    else:
        pairings, warnings = pair_score_groups_with_fallback(
            active_entries,
            opponent_history,
        )

    for board_number, (top_entry, bottom_entry) in enumerate(pairings, start=len(games) + 1):
        black_player_id, white_player_id = assign_colours(
            top_entry.player,
            bottom_entry.player,
            board_number=board_number,
            colour_history=colour_history,
        )
        warning_messages = [
            warning.message
            for warning in warnings
            if set(warning.player_ids) == {top_entry.player.id, bottom_entry.player.id}
        ]
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
                )
                + warning_messages,
            )
        )

    games.sort(key=lambda game: game.board_number)
    return games, warnings


def _bye_game(*, round_number: int, player: Player, config) -> Game:
    bye_game = Game.create(
        round_number=round_number,
        board_number=1,
        black_player_id=player.id,
        white_player_id=None,
        pairing_explanation=bye_explanation(round_number=round_number, player=player),
    )
    bye_game.result = Result.completed_outcome(
        outcome_code="bye",
        black_player_id=player.id,
        white_player_id=None,
        config=config,
    )
    return bye_game


def _sorted_active_players(players: list[Player]) -> list[Player]:
    return sorted(
        (player for player in players if player.status == "active"),
        key=lambda player: (-player.rank_sort_value, player.seed_number, player.id),
    )
