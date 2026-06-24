import pytest

from pairing.application import TournamentService
from pairing.domain import Player, Tournament
from pairing.storage import load_tournament, save_tournament


def _write_four_player_tournament(path, *, format: str = "swiss") -> None:
    tournament = Tournament.create("Service Open", round_count=3, format=format)
    tournament.players.extend(
        [
            Player.create("Alice", rank="4d", seed_number=1),
            Player.create("Bob", rank="3d", seed_number=2),
            Player.create("Cara", rank="2d", seed_number=3),
            Player.create("Devin", rank="1d", seed_number=4),
        ]
    )
    save_tournament(tournament, path)


def test_service_creates_tournament_file(tmp_path) -> None:
    path = tmp_path / "event.tgo.json"

    outcome = TournamentService.create(
        path,
        name="Service Open",
        round_count=4,
        format="mcmahon",
        actor="web",
    )

    loaded = load_tournament(path)
    assert outcome.path == path
    assert loaded.name == "Service Open"
    assert loaded.format == "mcmahon"
    assert loaded.config.round_count == 4
    assert loaded.audit_log[-1].actor == "web"


def test_service_imports_players_and_records_actor(tmp_path) -> None:
    path = tmp_path / "event.tgo.json"
    TournamentService.create(path, name="Service Open")
    service = TournamentService(path)

    outcome = service.import_players_text(
        "name,rank\nAlice,3d\nBob,1k\n",
        actor="web",
    )

    loaded = load_tournament(path)
    assert outcome.imported_count == 2
    assert [player.seed_number for player in loaded.players] == [1, 2]
    assert loaded.audit_log[-1].event_type == "players_imported"
    assert loaded.audit_log[-1].actor == "web"


def test_service_generates_round_and_audit_event(tmp_path) -> None:
    path = tmp_path / "event.tgo.json"
    _write_four_player_tournament(path)

    outcome = TournamentService(path).generate_next_round(actor="web")

    loaded = load_tournament(path)
    assert outcome.round_number == 1
    assert outcome.game_count == 2
    assert loaded.audit_log[-1].event_type == "round_pairings_generated"
    assert loaded.audit_log[-1].actor == "web"
    assert loaded.audit_log[-1].round_number == 1


def test_service_records_result_and_reloads_state(tmp_path) -> None:
    path = tmp_path / "event.tgo.json"
    _write_four_player_tournament(path)
    service = TournamentService(path)
    service.generate_next_round()

    outcome = service.record_result(
        round_number=1,
        board_number=1,
        winner="black",
        actor="web",
    )

    loaded = load_tournament(path)
    assert outcome.round_number == 1
    assert outcome.board_number == 1
    assert not outcome.corrected
    assert loaded.rounds[0].games[0].result.status == "completed"
    assert loaded.audit_log[-1].actor == "web"


def test_service_failure_leaves_file_unchanged(tmp_path) -> None:
    path = tmp_path / "event.tgo.json"
    _write_four_player_tournament(path)
    service = TournamentService(path)
    before = path.read_bytes()

    with pytest.raises(ValueError, match="Round 9 not found"):
        service.record_result(round_number=9, board_number=1, winner="black")

    assert path.read_bytes() == before


def test_service_returns_standings_and_exports_without_mutating_file(tmp_path) -> None:
    path = tmp_path / "event.tgo.json"
    _write_four_player_tournament(path)
    service = TournamentService(path)
    before = path.read_bytes()

    standings = service.standings()
    players_csv = service.export_csv("players")

    assert [entry.player.display_name for entry in standings] == [
        "Alice",
        "Bob",
        "Cara",
        "Devin",
    ]
    assert "Name,Rank,Country" in players_csv
    assert path.read_bytes() == before


def test_service_surfaces_unavoidable_repeat_warning(tmp_path) -> None:
    path = tmp_path / "event.tgo.json"
    tournament = Tournament.create("Repeat Service", round_count=2)
    alice = Player.create("Alice", rank="1d", seed_number=1)
    bob = Player.create("Bob", rank="1k", seed_number=2)
    tournament.players.extend([alice, bob])
    save_tournament(tournament, path)
    service = TournamentService(path)
    service.generate_next_round()
    service.record_result(round_number=1, board_number=1, winner="black")

    outcome = service.generate_next_round(actor="web")

    loaded = load_tournament(path)
    assert outcome.warnings
    assert "already met" in outcome.warnings[0]
    assert loaded.audit_log[-1].details["warnings"] == list(outcome.warnings)


def test_service_requires_explicit_result_correction_and_preserves_previous_result(
    tmp_path,
) -> None:
    path = tmp_path / "event.tgo.json"
    _write_four_player_tournament(path)
    service = TournamentService(path)
    service.generate_next_round()
    service.record_result(round_number=1, board_number=1, winner="black")

    with pytest.raises(ValueError, match="already has a completed result"):
        service.record_result(round_number=1, board_number=1, winner="white")

    service.record_result(round_number=1, board_number=2, winner="black")
    service.generate_next_round()
    outcome = service.correct_result(
        round_number=1,
        board_number=1,
        winner="white",
        actor="web",
    )

    loaded = load_tournament(path)
    correction = next(item for item in loaded.audit_log if item.event_type == "result_corrected")
    game = loaded.get_game(1, 1)
    assert outcome.corrected
    assert outcome.invalidated_rounds == (2,)
    assert game.result.correction_of == correction.id
    assert correction.actor == "web"
    assert correction.details["previous_result"]["winner_player_id"] == game.black_player_id
    assert loaded.get_round(2).status == "stale"


def test_service_regeneration_audits_superseded_round_snapshots(tmp_path) -> None:
    path = tmp_path / "event.tgo.json"
    _write_four_player_tournament(path)
    service = TournamentService(path)
    service.generate_next_round()
    service.record_result(round_number=1, board_number=1, winner="black")
    service.record_result(round_number=1, board_number=2, winner="black")
    service.generate_next_round()
    service.correct_result(round_number=1, board_number=1, winner="white")

    outcome = service.regenerate_from(1, actor="web")

    loaded = load_tournament(path)
    regeneration = next(
        item for item in reversed(loaded.audit_log) if item.event_type == "rounds_regenerated"
    )
    assert outcome is not None
    assert [round_obj.number for round_obj in loaded.rounds] == [1, 2]
    assert regeneration.actor == "web"
    assert [item["number"] for item in regeneration.details["superseded_rounds"]] == [2]
