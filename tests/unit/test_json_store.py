import json
import os

import pytest

from pairing.domain.player import Player
from pairing.domain.tournament import Tournament
from pairing.storage.json_store import TournamentStoreError, load_tournament, save_tournament


def test_save_and_load_tournament_round_trip(tmp_path):
    path = tmp_path / "example.tgo.json"
    tournament = Tournament.create("Example Weiqi Open", round_count=5)
    tournament.add_players(
        [
            Player.create("Alice", rank="3d"),
            Player.create("Bob", rank="5k"),
        ]
    )

    save_tournament(tournament, path)
    loaded = load_tournament(path)

    assert loaded.name == "Example Weiqi Open"
    assert loaded.config.round_count == 5
    assert loaded.schema_version == 1
    assert loaded.audit_log[0].event_type == "tournament_created"
    assert [player.display_name for player in loaded.players] == ["Alice", "Bob"]
    assert [player.seed_number for player in loaded.players] == [1, 2]


def test_save_rejects_invalid_aggregate_without_writing_file(tmp_path) -> None:
    path = tmp_path / "invalid.tgo.json"
    tournament = Tournament.create("Invalid Open")
    tournament.players.append(Player.create("Alice", rank="1d"))

    with pytest.raises(ValueError, match="seed number must be positive"):
        save_tournament(tournament, path)

    assert not path.exists()


def test_failed_atomic_replace_preserves_existing_file(tmp_path, monkeypatch) -> None:
    path = tmp_path / "event.tgo.json"
    original = Tournament.create("Original")
    save_tournament(original, path)
    original_bytes = path.read_bytes()

    replacement = Tournament.create("Replacement")

    def fail_replace(source, target):
        raise OSError("simulated replace failure")

    monkeypatch.setattr(os, "replace", fail_replace)

    with pytest.raises(OSError, match="simulated replace failure"):
        save_tournament(replacement, path)

    assert path.read_bytes() == original_bytes
    assert not path.with_name(f".{path.name}.tmp").exists()


def test_load_rejects_unknown_schema_version(tmp_path):
    path = tmp_path / "bad.tgo.json"
    path.write_text(json.dumps({"schema_version": 999, "tournament": {}}), encoding="utf-8")

    with pytest.raises(TournamentStoreError, match="Unsupported schema version"):
        load_tournament(path)


def test_load_rejects_malformed_json(tmp_path):
    path = tmp_path / "malformed.tgo.json"
    path.write_text("{not json", encoding="utf-8")

    with pytest.raises(TournamentStoreError, match="Invalid tournament JSON"):
        load_tournament(path)


def test_load_rejects_array_json_as_invalid_structure(tmp_path):
    path = tmp_path / "array.tgo.json"
    path.write_text(json.dumps([]), encoding="utf-8")

    with pytest.raises(TournamentStoreError, match="Invalid tournament file structure"):
        load_tournament(path)


def test_load_rejects_missing_tournament_data_as_invalid_structure(tmp_path):
    path = tmp_path / "missing-tournament.tgo.json"
    path.write_text(json.dumps({"schema_version": 1}), encoding="utf-8")

    with pytest.raises(TournamentStoreError, match="Invalid tournament file structure"):
        load_tournament(path)


def test_load_rejects_non_numeric_schema_version_as_invalid_structure(tmp_path):
    path = tmp_path / "bad-schema.tgo.json"
    path.write_text(json.dumps({"schema_version": "one"}), encoding="utf-8")

    with pytest.raises(TournamentStoreError, match="Invalid tournament file structure"):
        load_tournament(path)


def test_load_rejects_missing_file(tmp_path):
    with pytest.raises(TournamentStoreError, match="Tournament file not found"):
        load_tournament(tmp_path / "missing.tgo.json")


@pytest.mark.parametrize(
    ("round_payload", "error_message"),
    [
        (
            {
                "number": 1,
                "games": [],
            },
            "Invalid tournament file structure",
        ),
        (
            {
                "number": 1,
                "generated_at": "2026-06-23T00:00:00+00:00",
                "pairing_method": "swiss",
                "pairing_seed": 1,
                "games": [],
            },
            "Invalid tournament file structure",
        ),
        (
            {
                "number": 1,
                "status": "draft",
                "generated_at": "2026-06-23T00:00:00+00:00",
                "pairing_seed": 1,
                "games": [],
            },
            "Invalid tournament file structure",
        ),
        (
            {
                "number": 1,
                "status": "draft",
                "generated_at": "2026-06-23T00:00:00+00:00",
                "pairing_method": "swiss",
                "games": [],
            },
            "Invalid tournament file structure",
        ),
        (
            {
                "number": 1,
                "status": "draft",
                "generated_at": "2026-06-23T00:00:00+00:00",
                "pairing_method": "swiss",
                "pairing_seed": 1,
                "games": [
                    {
                        "id": "game-1",
                        "round_number": 1,
                        "board_number": 1,
                        "black_player_id": "player-a",
                        "white_player_id": "player-b",
                    }
                ],
            },
            "Invalid tournament file structure",
        ),
        (
            {
                "number": 1,
                "status": "draft",
                "generated_at": "2026-06-23T00:00:00+00:00",
                "pairing_method": "swiss",
                "pairing_seed": 1,
                "games": [
                    {
                        "id": "game-1",
                        "round_number": 1,
                        "board_number": 1,
                        "black_player_id": "player-a",
                        "white_player_id": "player-b",
                        "result": {"result_type": "pending"},
                    }
                ],
            },
            "Invalid tournament file structure",
        ),
        (
            {
                "number": 1,
                "status": "draft",
                "generated_at": "2026-06-23T00:00:00+00:00",
                "pairing_method": "swiss",
                "pairing_seed": 1,
                "games": [
                    {
                        "id": "game-1",
                        "round_number": 1,
                        "board_number": 1,
                        "black_player_id": "player-a",
                        "white_player_id": "player-b",
                        "result": {"status": "pending"},
                    }
                ],
            },
            "Invalid tournament file structure",
        ),
        (
            {
                "number": 1,
                "status": "draft",
                "generated_at": "2026-06-23T00:00:00+00:00",
                "pairing_method": "swiss",
                "pairing_seed": 1,
                "is_regenerated": "false",
                "games": [],
            },
            "Invalid tournament file structure",
        ),
    ],
)
def test_load_rejects_malformed_round_payloads(tmp_path, round_payload, error_message):
    path = tmp_path / "bad-round.tgo.json"
    tournament = Tournament.create("Example Weiqi Open")
    payload = tournament.to_dict()
    payload["rounds"] = [round_payload]
    path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(TournamentStoreError, match=error_message):
        load_tournament(path)
