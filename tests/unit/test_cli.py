import csv

from pairing.cli.main import main
from pairing.storage.json_store import load_tournament


def test_cli_create_command(tmp_path):
    tournament_path = tmp_path / "example.tgo.json"

    exit_code = main(["create", str(tournament_path), "--name", "Example Weiqi Open", "--rounds", "5"])

    assert exit_code == 0
    tournament = load_tournament(tournament_path)
    assert tournament.name == "Example Weiqi Open"
    assert tournament.config.round_count == 5


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
