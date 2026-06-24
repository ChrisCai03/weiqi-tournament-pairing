from pairing.cli.main import main
from pairing.domain import Player, Tournament
from pairing.storage import load_tournament, save_tournament


def test_swiss_file_survives_create_pair_result_and_reload(tmp_path) -> None:
    path = tmp_path / "event.tgo.json"
    tournament = Tournament.create("Characterization Open", round_count=2)
    tournament.players.extend(
        [
            Player.create("Alice", rank="4d", seed_number=1),
            Player.create("Bob", rank="3d", seed_number=2),
            Player.create("Cara", rank="2d", seed_number=3),
            Player.create("Devin", rank="1d", seed_number=4),
        ]
    )
    save_tournament(tournament, path)

    assert main(["pair-round", str(path)]) == 0
    assert main(
        ["enter-result", str(path), "--round", "1", "--board", "1", "--winner", "black"]
    ) == 0

    loaded = load_tournament(path)
    assert loaded.rounds[0].games[0].result.status == "completed"
    assert loaded.audit_log[-1].event_type == "result_entered"
