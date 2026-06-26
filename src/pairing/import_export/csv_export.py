from __future__ import annotations

import csv
from io import StringIO

from pairing.domain.tournament import Tournament
from pairing.engine.mcmahon import mcmahon_starting_score
from pairing.engine.standings import calculate_standings


def players_to_csv(tournament: Tournament) -> str:
    buffer = StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["Name", "Rank", "Country", "Club", "School", "Team", "Seed", "Status"])
    for player in tournament.players:
        writer.writerow(
            [
                player.display_name,
                player.rank,
                player.country,
                player.club,
                player.school,
                player.team_id,
                player.seed_number,
                player.status,
            ]
        )
    return buffer.getvalue()


def standings_to_csv(tournament: Tournament) -> str:
    buffer = StringIO()
    writer = csv.writer(buffer)
    writer.writerow(
        [
            "Pos",
            "Player",
            "Starting Score",
            "Game Score",
            "Total Score",
            "Wins",
            "Losses",
            "SOS",
            "SOSOS",
        ]
    )
    standings = calculate_standings(
        tournament,
        starting_score_provider=(
            lambda player: (
                mcmahon_starting_score(player, tournament)
                if tournament.format == "mcmahon"
                else 0.0
            )
        ),
    )
    for index, entry in enumerate(standings, start=1):
        writer.writerow(
            [
                index,
                entry.player.display_name,
                f"{entry.starting_score:.1f}",
                f"{entry.game_score:.1f}",
                f"{entry.score:.1f}",
                entry.wins,
                entry.losses,
                f"{entry.sos:.1f}",
                f"{entry.sosos:.1f}",
            ]
        )
    return buffer.getvalue()


def pairings_to_csv(tournament: Tournament) -> str:
    buffer = StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["Round", "Board", "Black", "White", "Result", "Pairing Method"])
    for round_obj in tournament.rounds:
        for game in round_obj.games:
            writer.writerow(
                [
                    round_obj.number,
                    game.board_number,
                    _player_name(tournament, game.black_player_id),
                    _player_name(tournament, game.white_player_id),
                    _result_summary(game),
                    round_obj.pairing_method,
                ]
            )
    return buffer.getvalue()


def results_to_csv(tournament: Tournament) -> str:
    buffer = StringIO()
    writer = csv.writer(buffer)
    writer.writerow(
        [
            "Round",
            "Board",
            "Winner",
            "Result Type",
            "outcome_code",
            "black_score",
            "white_score",
            "Entered At",
        ]
    )
    for round_obj in tournament.rounds:
        for game in round_obj.games:
            result = game.result
            writer.writerow(
                [
                    round_obj.number,
                    game.board_number,
                    _player_name(tournament, result.winner_player_id),
                    result.result_type,
                    result.outcome_code or "",
                    "" if result.black_score is None else result.black_score,
                    "" if result.white_score is None else result.white_score,
                    result.entered_at or "",
                ]
            )
    return buffer.getvalue()


def _player_name(tournament: Tournament, player_id: str | None) -> str:
    if player_id is None:
        return ""
    for player in tournament.players:
        if player.id == player_id:
            return player.display_name
    return player_id


def _result_summary(game) -> str:
    result = game.result
    if result.result_type == "bye":
        return "bye"
    if result.status != "completed":
        return "pending"
    return result.result_type
