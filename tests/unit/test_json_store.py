import json

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


def test_load_rejects_unknown_schema_version(tmp_path):
    path = tmp_path / "bad.tgo.json"
    path.write_text(json.dumps({"schema_version": 999, "tournament": {}}), encoding="utf-8")

    with pytest.raises(TournamentStoreError, match="Unsupported schema version"):
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
