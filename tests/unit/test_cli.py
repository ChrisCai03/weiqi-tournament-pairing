import csv

from pairing.cli.main import main
from pairing.domain.player import Player
from pairing.domain.tournament import Tournament
from pairing.storage.json_store import load_tournament
from pairing.storage.json_store import save_tournament


def test_cli_create_command(tmp_path):
    tournament_path = tmp_path / "example.tgo.json"

    exit_code = main(["create", str(tournament_path), "--name", "Example Weiqi Open", "--rounds", "5"])

    assert exit_code == 0
    tournament = load_tournament(tournament_path)
    assert tournament.name == "Example Weiqi Open"
    assert tournament.config.round_count == 5


def test_cli_create_command_rejects_non_positive_rounds(tmp_path, capsys):
    tournament_path = tmp_path / "example.tgo.json"

    exit_code = main(["create", str(tournament_path), "--name", "Example Weiqi Open", "--rounds", "0"])

    captured = capsys.readouterr()
    assert exit_code == 1
    assert captured.err == "Error: Round count must be positive.\n"
    assert not tournament_path.exists()


def test_cli_import_players_command(tmp_path):
    tournament_path = tmp_path / "example.tgo.json"
    players_path = tmp_path / "players.csv"
    with players_path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=["name", "rank"])
        writer.writeheader()
        writer.writerow({"name": "Alice", "rank": "3d"})
        writer.writerow({"name": "Bob", "rank": "5k"})

    assert main(["create", str(tournament_path), "--name", "Example Weiqi Open"]) == 0
    assert main(["import-players", str(tournament_path), str(players_path)]) == 0

    tournament = load_tournament(tournament_path)
    assert [player.display_name for player in tournament.players] == ["Alice", "Bob"]
    assert [player.seed_number for player in tournament.players] == [1, 2]


def test_cli_import_players_command_uses_max_existing_seed(tmp_path):
    tournament_path = tmp_path / "example.tgo.json"
    players_path = tmp_path / "players.csv"
    with players_path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=["name", "rank"])
        writer.writeheader()
        writer.writerow({"name": "Charlie", "rank": "2d"})
        writer.writerow({"name": "Dana", "rank": "4k"})

    tournament = Tournament.create("Example Weiqi Open")
    tournament.players.extend(
        [
            Player.create("Alice", rank="3d", seed_number=2),
            Player.create("Bob", rank="5k", seed_number=10),
        ]
    )
    save_tournament(tournament, tournament_path)

    assert main(["import-players", str(tournament_path), str(players_path)]) == 0

    loaded_tournament = load_tournament(tournament_path)
    assert [player.seed_number for player in loaded_tournament.players] == [2, 10, 11, 12]


def test_cli_import_players_missing_tournament_returns_error(tmp_path, capsys):
    tournament_path = tmp_path / "missing.tgo.json"
    players_path = tmp_path / "missing.csv"

    exit_code = main(["import-players", str(tournament_path), str(players_path)])

    captured = capsys.readouterr()
    assert exit_code == 1
    assert captured.err == f"Error: Tournament file not found: {tournament_path}\n"


def test_cli_import_players_missing_csv_returns_error(tmp_path, capsys):
    tournament_path = tmp_path / "example.tgo.json"
    players_path = tmp_path / "missing.csv"

    assert main(["create", str(tournament_path), "--name", "Example Weiqi Open"]) == 0
    capsys.readouterr()

    exit_code = main(["import-players", str(tournament_path), str(players_path)])

    captured = capsys.readouterr()
    assert exit_code == 1
    assert captured.err.startswith("Error:")
    assert players_path.name in captured.err


def test_cli_pair_round_creates_first_round(tmp_path, capsys):
    tournament_path = tmp_path / "example.tgo.json"
    tournament = Tournament.create("Example Weiqi Open")
    tournament.players.extend(
        [
            Player.create("Alice", rank="4d", seed_number=1),
            Player.create("Bob", rank="3d", seed_number=2),
            Player.create("Charlie", rank="1d", seed_number=3),
            Player.create("Diana", rank="1k", seed_number=4),
            Player.create("Eve", rank="5k", seed_number=5),
        ]
    )
    save_tournament(tournament, tournament_path)

    exit_code = main(["pair-round", str(tournament_path)])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.out == "Paired round 1 with 3 games.\n"

    loaded_tournament = load_tournament(tournament_path)
    assert [round_obj.number for round_obj in loaded_tournament.rounds] == [1]
    assert [game.board_number for game in loaded_tournament.rounds[0].games] == [1, 2, 3]
    assert sum(
        1
        for game in loaded_tournament.rounds[0].games
        if game.result.result_type == "bye"
    ) == 1


def test_cli_pair_round_refuses_to_exceed_configured_round_count(tmp_path, capsys):
    tournament_path = tmp_path / "example.tgo.json"
    tournament = Tournament.create("Example Weiqi Open", round_count=1)
    tournament.players.extend(
        [
            Player.create("Alice", rank="4d", seed_number=1),
            Player.create("Bob", rank="3d", seed_number=2),
        ]
    )
    save_tournament(tournament, tournament_path)
    assert main(["pair-round", str(tournament_path)]) == 0
    capsys.readouterr()

    exit_code = main(["pair-round", str(tournament_path)])

    captured = capsys.readouterr()
    assert exit_code == 1
    assert captured.err == "Error: Cannot pair round 2 beyond configured number of rounds (1).\n"


def test_cli_regenerate_from_rebuilds_the_next_round_after_result_correction(tmp_path, capsys):
    tournament_path = tmp_path / "example.tgo.json"
    tournament = Tournament.create("Example Weiqi Open", round_count=3)
    tournament.players.extend(
        [
            Player.create("Alice", rank="4d", seed_number=1),
            Player.create("Bob", rank="3d", seed_number=2),
            Player.create("Charlie", rank="1d", seed_number=3),
            Player.create("Diana", rank="1k", seed_number=4),
        ]
    )
    save_tournament(tournament, tournament_path)

    assert main(["pair-round", str(tournament_path)]) == 0
    assert main(
        [
            "enter-result",
            str(tournament_path),
            "--round",
            "1",
            "--board",
            "1",
            "--winner",
            "black",
        ]
    ) == 0
    capsys.readouterr()

    exit_code = main(
        [
            "regenerate-from",
            str(tournament_path),
            "--round",
            "1",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.out == "Generated round 2.\n"

    loaded_tournament = load_tournament(tournament_path)
    assert [round_obj.number for round_obj in loaded_tournament.rounds] == [1, 2]
    assert all(round_obj.status != "stale" for round_obj in loaded_tournament.rounds)


def test_cli_enter_result_records_black_win_and_completes_round(tmp_path, capsys):
    tournament_path = tmp_path / "example.tgo.json"
    tournament = Tournament.create("Example Weiqi Open")
    tournament.players.extend(
        [
            Player.create("Alice", rank="4d", seed_number=1),
            Player.create("Bob", rank="3d", seed_number=2),
        ]
    )
    save_tournament(tournament, tournament_path)
    assert main(["pair-round", str(tournament_path)]) == 0
    capsys.readouterr()

    exit_code = main(
        [
            "enter-result",
            str(tournament_path),
            "--round",
            "1",
            "--board",
            "1",
            "--winner",
            "black",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.out == "Recorded black win for round 1 board 1.\n"

    loaded_tournament = load_tournament(tournament_path)
    game = loaded_tournament.rounds[0].games[0]
    assert game.result.status == "completed"
    assert game.result.result_type == "normal"
    assert game.result.winner_player_id == game.black_player_id
    assert loaded_tournament.rounds[0].status == "completed"
    assert loaded_tournament.rounds[0].completed_at is not None
    assert loaded_tournament.audit_log[-1].event_type == "result_entered"
    assert loaded_tournament.audit_log[-1].round_number == 1
    assert loaded_tournament.audit_log[-1].details == {
        "board_number": 1,
        "winner": "black",
        "winner_player_id": game.black_player_id,
    }


def test_cli_enter_result_rejects_unknown_round_or_board(tmp_path, capsys):
    tournament_path = tmp_path / "example.tgo.json"
    tournament = Tournament.create("Example Weiqi Open")
    tournament.players.extend(
        [
            Player.create("Alice", rank="4d", seed_number=1),
            Player.create("Bob", rank="3d", seed_number=2),
        ]
    )
    save_tournament(tournament, tournament_path)
    assert main(["pair-round", str(tournament_path)]) == 0
    capsys.readouterr()

    exit_code = main(
        [
            "enter-result",
            str(tournament_path),
            "--round",
            "9",
            "--board",
            "1",
            "--winner",
            "black",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 1
    assert captured.err == "Error: Round 9 not found.\n"


def test_cli_enter_result_marks_future_rounds_stale_when_correction_breaks_history(tmp_path, capsys):
    tournament_path = tmp_path / "example.tgo.json"
    tournament = Tournament.create("Example Weiqi Open", round_count=3)
    tournament.players.extend(
        [
            Player.create("Alice", rank="4d", seed_number=1),
            Player.create("Bob", rank="3d", seed_number=2),
            Player.create("Charlie", rank="1d", seed_number=3),
            Player.create("Diana", rank="1k", seed_number=4),
        ]
    )
    save_tournament(tournament, tournament_path)
    assert main(["pair-round", str(tournament_path)]) == 0
    assert main(["pair-round", str(tournament_path)]) == 0
    capsys.readouterr()

    exit_code = main(
        [
            "enter-result",
            str(tournament_path),
            "--round",
            "1",
            "--board",
            "1",
            "--winner",
            "black",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.out == "Recorded black win for round 1 board 1.\n"

    loaded_tournament = load_tournament(tournament_path)
    assert loaded_tournament.rounds[1].status == "stale"
    assert loaded_tournament.audit_log[-1].event_type == "future_rounds_invalidated"
