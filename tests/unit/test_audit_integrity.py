import json

from pairing.application.audit_integrity import (
    load_or_create_local_audit_key,
    sign_audit_log,
    state_hash,
    verify_audit_log,
)
from pairing.domain.audit import AuditLogEntry
from pairing.domain.player import Player
from pairing.domain.tournament import Tournament
from pairing.storage.json_store import save_tournament


def test_state_hash_is_deterministic_across_dict_ordering() -> None:
    left = {
        "schema_version": 1,
        "tournament": {
            "id": "t-1",
            "name": "Order Test",
            "game_type": "go",
            "format": "swiss",
            "status": "draft",
        },
        "config": {"round_count": 5, "pairing_method": "swiss"},
        "players": [{"id": "p-1", "display_name": "Alice", "rank": "1d", "seed_number": 1}],
        "participation": [],
        "teams": [],
        "rounds": [],
        "manual_overrides": [],
        "audit_log": [
            {
                "id": "a-1",
                "timestamp": "2026-07-01T00:00:00+00:00",
                "event_type": "tournament_created",
                "actor": "cli",
                "summary": "Created tournament.",
                "details": {"z": 1, "a": 2},
                "state_hash_before": "ignored-before",
                "state_hash_after": "ignored-after",
                "signature": "ignored-signature",
            }
        ],
    }
    right = {
        "manual_overrides": [],
        "audit_log": [
            {
                "signature": "different-signature",
                "details": {"a": 2, "z": 1},
                "summary": "Created tournament.",
                "actor": "cli",
                "event_type": "tournament_created",
                "timestamp": "2026-07-01T00:00:00+00:00",
                "id": "a-1",
                "state_hash_after": "different-after",
                "state_hash_before": "different-before",
            }
        ],
        "teams": [],
        "schema_version": 1,
        "players": [{"seed_number": 1, "rank": "1d", "display_name": "Alice", "id": "p-1"}],
        "rounds": [],
        "participation": [],
        "config": {"pairing_method": "swiss", "round_count": 5},
        "tournament": {
            "status": "draft",
            "format": "swiss",
            "game_type": "go",
            "name": "Order Test",
            "id": "t-1",
        },
    }

    assert state_hash(left) == state_hash(right)


def test_load_or_create_local_audit_key_creates_and_reuses_key(tmp_path) -> None:
    key_path = tmp_path / ".pairing_audit_key"

    created = load_or_create_local_audit_key(key_path)
    reused = load_or_create_local_audit_key(key_path)

    assert len(created) == 32
    assert reused == created
    assert key_path.read_text(encoding="utf-8").strip()


def test_verify_audit_log_rejects_unsigned_tournament() -> None:
    tournament = Tournament.create("Unsigned Open")

    report = verify_audit_log(tournament, key=b"0" * 32)

    assert report.valid is False
    assert "unsigned" in report.errors[0].lower()


def test_sign_then_verify_audit_log_is_valid() -> None:
    tournament = Tournament.create("Signed Open")
    tournament.add_players([Player.create("Alice", rank="1d"), Player.create("Bob", rank="1k")])

    sign_audit_log(tournament, key=b"1" * 32)
    report = verify_audit_log(tournament, key=b"1" * 32)

    assert report.valid is True
    assert report.errors == ()
    assert report.current_state_hash == tournament.audit_log[-1].state_hash_after
    assert all(entry.signature for entry in tournament.audit_log)


def test_verify_audit_log_detects_manual_payload_tampering(tmp_path) -> None:
    path = tmp_path / "signed.tgo.json"
    tournament = Tournament.create("Tamper Test Open")
    tournament.add_players([Player.create("Alice", rank="1d"), Player.create("Bob", rank="1k")])
    sign_audit_log(tournament, key=b"2" * 32)
    save_tournament(tournament, path)

    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["players"][0]["display_name"] = "Mallory"
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    report = verify_audit_log(path, key=b"2" * 32)

    assert report.valid is False
    assert any("state hash" in error.lower() for error in report.errors)


def test_audit_log_entry_signature_round_trips_via_dict_serialization() -> None:
    entry = AuditLogEntry.from_dict(
        {
            "id": "entry-1",
            "timestamp": "2026-07-01T00:00:00+00:00",
            "event_type": "tournament_created",
            "actor": "cli",
            "summary": "Created tournament.",
            "details": {"count": 1},
            "state_hash_before": "before",
            "state_hash_after": "after",
            "signature": "signed",
        }
    )

    restored = AuditLogEntry.from_dict(entry.to_dict())

    assert restored.signature == "signed"
