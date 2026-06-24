from __future__ import annotations

from pairing.domain.game import Game
from pairing.domain.player import Player
from pairing.domain.result import Result
from pairing.domain.round import Round
from pairing.domain.tournament import Tournament
from pairing.engine.bye import select_bye_player
from pairing.engine.colours import assign_colours
from pairing.engine.history import colour_history_by_player, opponent_ids_by_player, players_have_met
from pairing.engine.standings import StandingEntry, calculate_standings
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
    if round_number == 1:
        games = _generate_first_round(tournament=tournament, active_players=active_players, round_number=round_number)
    else:
        games = _generate_later_round(tournament=tournament, round_number=round_number)

    return Round.create(
        number=round_number,
        games=games,
        pairing_method="swiss",
        pairing_seed=tournament.config.random_seed,
        explanation_summary=round_summary(round_number=round_number),
    )


def _generate_first_round(*, tournament: Tournament, active_players: list[Player], round_number: int) -> list[Game]:
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
    return games


def _generate_later_round(*, tournament: Tournament, round_number: int) -> list[Game]:
    standings = calculate_standings(tournament)
    active_entries = [entry for entry in standings if entry.player.status == "active"]
    opponent_history = opponent_ids_by_player(tournament)
    colour_history = colour_history_by_player(tournament)
    games: list[Game] = []

    if len(active_entries) % 2 == 1:
        bye_entry = select_bye_player(active_entries)
        active_entries = [entry for entry in active_entries if entry.player.id != bye_entry.player.id]
        bye_game = Game.create(
            round_number=round_number,
            board_number=1,
            black_player_id=bye_entry.player.id,
            white_player_id=None,
            pairing_explanation=bye_explanation(round_number=round_number, player=bye_entry.player),
        )
        bye_game.result = Result.completed(result_type="bye", winner_player_id=bye_entry.player.id)
        games.append(bye_game)

    pairings = _pair_score_groups(active_entries, opponent_history)
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
                ),
            )
        )

    games.sort(key=lambda game: game.board_number)
    return games


def _pair_score_groups(
    entries: list[StandingEntry],
    opponent_history: dict[str, list[str]],
) -> list[tuple[StandingEntry, StandingEntry]]:
    score_groups = _group_entries_by_score(entries)
    pairings = _pair_score_group_recursive(score_groups, opponent_history, carry=())
    if pairings is None:
        raise ValueError("Unable to generate Swiss pairings without repeated opponents.")
    return pairings


def _pair_score_group_recursive(
    score_groups: list[list[StandingEntry]],
    opponent_history: dict[str, list[str]],
    *,
    carry: tuple[StandingEntry, ...],
) -> list[tuple[StandingEntry, StandingEntry]] | None:
    if not score_groups:
        return [] if not carry else None

    current_group = score_groups[0]
    available = list(carry) + list(current_group)

    full_pairing = _pair_entries_without_floats(available, opponent_history)
    if full_pairing is not None:
        rest = _pair_score_group_recursive(score_groups[1:], opponent_history, carry=())
        if rest is not None:
            return full_pairing + rest

    for float_index in range(len(available) - 1, -1, -1):
        floated_entry = available[float_index]
        remaining = available[:float_index] + available[float_index + 1 :]
        pairings = _pair_entries_without_floats(remaining, opponent_history)
        if pairings is None:
            continue

        rest = _pair_score_group_recursive(score_groups[1:], opponent_history, carry=(floated_entry,))
        if rest is not None:
            return pairings + rest

    return None


def _pair_entries_without_floats(
    entries: list[StandingEntry],
    opponent_history: dict[str, list[str]],
) -> list[tuple[StandingEntry, StandingEntry]] | None:
    if not entries:
        return []

    first_entry = entries[0]
    for index in range(1, len(entries)):
        partner = entries[index]
        if players_have_met(opponent_history, first_entry.player.id, partner.player.id):
            continue
        remainder = entries[1:index] + entries[index + 1 :]
        paired_remainder = _pair_entries_without_floats(remainder, opponent_history)
        if paired_remainder is not None:
            return [(first_entry, partner)] + paired_remainder

    return None


def _group_entries_by_score(entries: list[StandingEntry]) -> list[list[StandingEntry]]:
    grouped: list[list[StandingEntry]] = []
    for entry in entries:
        if grouped and entry.score == grouped[-1][0].score:
            grouped[-1].append(entry)
        else:
            grouped.append([entry])
    return grouped


def _sorted_active_players(players: list[Player]) -> list[Player]:
    return sorted(
        (player for player in players if player.status == "active"),
        key=lambda player: (-player.rank_sort_value, player.seed_number, player.id),
    )
