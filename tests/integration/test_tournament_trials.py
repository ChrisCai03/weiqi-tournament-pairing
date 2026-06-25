from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path

from pairing.application import TournamentService
from pairing.storage import load_tournament


def test_realistic_open_fixture_import_survives_reload(tmp_path) -> None:
    tournament_path = tmp_path / "realistic-open.tgo.json"
    fixture_path = (
        Path(__file__).resolve().parents[1] / "fixtures" / "players" / "realistic-open.csv"
    )

    TournamentService.create(
        tournament_path,
        name="Realistic Open",
        round_count=5,
        format="swiss",
        actor="test",
    )

    import_outcome = TournamentService(tournament_path).import_players_file(
        fixture_path,
        actor="test",
    )
    assert import_outcome.imported_count == 32
    assert import_outcome.warnings == ()

    reloaded = load_tournament(tournament_path)
    assert len(reloaded.players) == 32

    seed_numbers = [player.seed_number for player in reloaded.players]
    assert sorted(seed_numbers) == list(range(1, 33))
    assert len(set(seed_numbers)) == 32

    ranks = [player.rank for player in reloaded.players]
    assert any(rank.endswith("d") for rank in ranks)
    assert any(rank.endswith("k") for rank in ranks)
    assert ranks.count("unranked") == 2

    by_name = {player.display_name: player for player in reloaded.players}
    assert by_name["Aiko Tan"].country == "Japan"
    assert by_name["Aiko Tan"].club == "Tokyo Go Club"
    assert by_name["Aiko Tan"].school == "Seishin High"

    assert by_name["Ben Liu"].country == "United States"
    assert by_name["Ben Liu"].club == "Bay Area Go Club"
    assert by_name["Ben Liu"].school == "Stanford University"

    assert by_name["Mina Okada"].country == "Canada"
    assert by_name["Mina Okada"].club == "Toronto Go Club"
    assert by_name["Mina Okada"].school == "University of Toronto"

    assert by_name["Carlos Mendes"].club == "São Paulo Go Club"
    assert by_name["Carlos Mendes"].school == "University of São Paulo"
    assert by_name["Carlos Mendes"].team_id == "Team South"
    assert by_name["Carlos Mendes"].notes == "Strong tesuji"

    assert by_name["Noah Carter"].school == "University of California, Berkeley"
    assert "Liam O'Connor" in by_name


def test_complete_five_round_swiss_realistic_open_trial(tmp_path) -> None:
    tournament_path, service = _create_imported_tournament(
        tmp_path,
        name="Realistic Swiss Trial",
        format="swiss",
    )

    _play_complete_trial(service, rounds=5)

    loaded = load_tournament(tournament_path)
    standings = service.standings()

    assert len(loaded.rounds) == 5
    assert all(round_obj.pairing_method == "swiss" for round_obj in loaded.rounds)
    assert all(round_obj.status == "completed" for round_obj in loaded.rounds)
    assert all(len(round_obj.games) == 16 for round_obj in loaded.rounds)
    assert len(standings) == 32
    assert sum(event.event_type == "round_pairings_generated" for event in loaded.audit_log) == 5
    assert sum(event.event_type == "result_entered" for event in loaded.audit_log) == 80
    assert service.load().to_dict() == load_tournament(tournament_path).to_dict()

    _assert_csv_report(
        service,
        "players",
        expected_header=["Name", "Rank", "Country", "Club", "School", "Team", "Seed", "Status"],
        expected_rows=32,
    )
    _assert_csv_report(
        service,
        "pairings",
        expected_header=["Round", "Board", "Black", "White", "Result", "Pairing Method"],
        expected_rows=80,
    )
    _assert_csv_report(
        service,
        "results",
        expected_header=["Round", "Board", "Winner", "Result Type", "Entered At"],
        expected_rows=80,
    )
    _assert_csv_report(
        service,
        "standings",
        expected_header=[
            "Pos",
            "Player",
            "Starting Score",
            "Game Score",
            "Total Score",
            "Wins",
            "Losses",
            "SOS",
            "SOSOS",
        ],
        expected_rows=32,
    )


def test_complete_five_round_mcmahon_realistic_open_trial(tmp_path) -> None:
    tournament_path, service = _create_imported_tournament(
        tmp_path,
        name="Realistic McMahon Trial",
        format="mcmahon",
    )

    _play_complete_trial(service, rounds=5)

    loaded = load_tournament(tournament_path)
    standings = service.standings()

    assert len(loaded.rounds) == 5
    assert all(round_obj.pairing_method == "mcmahon" for round_obj in loaded.rounds)
    assert all(round_obj.status == "completed" for round_obj in loaded.rounds)
    assert len(standings) == 32

    _assert_mcmahon_starting_and_game_scores(loaded, standings)
    _assert_csv_report(
        service,
        "players",
        expected_header=["Name", "Rank", "Country", "Club", "School", "Team", "Seed", "Status"],
        expected_rows=32,
    )
    _assert_csv_report(
        service,
        "pairings",
        expected_header=["Round", "Board", "Black", "White", "Result", "Pairing Method"],
        expected_rows=80,
    )
    _assert_csv_report(
        service,
        "results",
        expected_header=["Round", "Board", "Winner", "Result Type", "Entered At"],
        expected_rows=80,
    )
    _assert_csv_report(
        service,
        "standings",
        expected_header=[
            "Pos",
            "Player",
            "Starting Score",
            "Game Score",
            "Total Score",
            "Wins",
            "Losses",
            "SOS",
            "SOSOS",
        ],
        expected_rows=32,
    )


def _fixture_path() -> Path:
    return Path(__file__).resolve().parents[1] / "fixtures" / "players" / "realistic-open.csv"


def _create_imported_tournament(
    tmp_path,
    *,
    name: str,
    format: str,
) -> tuple[Path, TournamentService]:
    tournament_path = tmp_path / f"{format}-realistic-open.tgo.json"
    TournamentService.create(
        tournament_path,
        name=name,
        round_count=5,
        format=format,
        actor="test",
    )
    service = TournamentService(tournament_path)
    import_outcome = service.import_players_file(_fixture_path(), actor="test")
    assert import_outcome.imported_count == 32
    assert import_outcome.warnings == ()
    return tournament_path, service


def _play_complete_trial(service: TournamentService, *, rounds: int) -> None:
    bye_counts: Counter[str] = Counter()
    next_winner = "black"

    for round_number in range(1, rounds + 1):
        outcome = service.generate_next_round(actor="test")
        assert outcome.round_number == round_number

        tournament = _reload_canonical(service)
        round_obj = tournament.get_round(round_number)
        _assert_round_invariants(tournament, round_obj, bye_counts)

        for game in round_obj.games:
            if game.result.result_type == "bye":
                assert game.result.status == "completed"
                continue

            service.record_result(
                round_number=round_number,
                board_number=game.board_number,
                winner=next_winner,
                actor="test",
            )
            next_winner = "white" if next_winner == "black" else "black"

            tournament = _reload_canonical(service)
            persisted_game = tournament.get_game(round_number, game.board_number)
            assert persisted_game.result.status == "completed"

        assert _reload_canonical(service).get_round(round_number).status == "completed"


def _reload_canonical(service: TournamentService):
    return load_tournament(service.path)


def _assert_round_invariants(tournament, round_obj, bye_counts: Counter[str]) -> None:
    assert [game.board_number for game in round_obj.games] == list(
        range(1, len(round_obj.games) + 1)
    )

    player_ids = [
        player_id
        for game in round_obj.games
        for player_id in (game.black_player_id, game.white_player_id)
        if player_id is not None
    ]
    assert len(player_ids) == len(set(player_ids))
    assert set(player_ids) == {player.id for player in tournament.players}
    assert len(player_ids) == len(tournament.players)

    bye_games = [game for game in round_obj.games if game.result.result_type == "bye"]
    assert len(bye_games) <= 1
    for game in bye_games:
        bye_counts[game.result.winner_player_id] += 1
        assert bye_counts[game.result.winner_player_id] == 1


def _assert_csv_report(
    service: TournamentService,
    report: str,
    *,
    expected_header: list[str],
    expected_rows: int,
) -> None:
    rows = list(csv.reader(service.export_csv(report).splitlines()))
    assert rows[0] == expected_header
    assert len(rows) == expected_rows + 1


def _assert_mcmahon_starting_and_game_scores(tournament, standings) -> None:
    entry_by_player_id = {entry.player.id: entry for entry in standings}
    strongest_player = max(tournament.players, key=lambda player: player.rank_sort_value)
    weakest_player = min(tournament.players, key=lambda player: player.rank_sort_value)

    assert any(entry.starting_score > 0 for entry in standings)
    assert any(entry.starting_score == 0 for entry in standings)
    assert all(entry.score == entry.starting_score + entry.game_score for entry in standings)
    assert (
        entry_by_player_id[strongest_player.id].starting_score
        >= entry_by_player_id[weakest_player.id].starting_score
    )
