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


def _complete_current_round(service) -> None:
    tournament = service.load()
    current = tournament.rounds[-1]
    for game in current.games:
        if game.result.status == "pending":
            service.record_result(
                round_number=current.number,
                board_number=game.board_number,
                winner="black",
            )


def test_complete_two_round_swiss_workflow(tmp_path) -> None:
    path = tmp_path / "swiss.tgo.json"
    tournament = Tournament.create("Swiss Workflow", round_count=2)
    tournament.players.extend(
        [
            Player.create(f"Player {index}", rank=f"{5 - index}d", seed_number=index)
            for index in range(1, 5)
        ]
    )
    save_tournament(tournament, path)
    from pairing.application import TournamentService

    service = TournamentService(path)
    service.generate_next_round()
    _complete_current_round(service)
    service.generate_next_round()
    _complete_current_round(service)

    loaded = load_tournament(path)
    assert [round_obj.status for round_obj in loaded.rounds] == [
        "completed",
        "completed",
    ]
    assert len(service.standings()) == 4
    assert sum(
        event.event_type == "round_pairings_generated"
        for event in loaded.audit_log
    ) == 2


def test_complete_two_round_mcmahon_workflow(tmp_path) -> None:
    path = tmp_path / "mcmahon.tgo.json"
    tournament = Tournament.create(
        "McMahon Workflow",
        round_count=2,
        format="mcmahon",
    )
    tournament.players.extend(
        [
            Player.create("Aya", rank="3d", seed_number=1),
            Player.create("Ben", rank="1d", seed_number=2),
            Player.create("Cheng", rank="1k", seed_number=3),
            Player.create("Dina", rank="3k", seed_number=4),
        ]
    )
    save_tournament(tournament, path)
    from pairing.application import TournamentService

    service = TournamentService(path)
    service.generate_next_round()
    _complete_current_round(service)
    service.generate_next_round()
    _complete_current_round(service)

    loaded = load_tournament(path)
    assert [round_obj.pairing_method for round_obj in loaded.rounds] == [
        "mcmahon",
        "mcmahon",
    ]
    assert all(round_obj.status == "completed" for round_obj in loaded.rounds)
