import pytest

from pairing.domain.audit import AuditLogEntry
from pairing.domain.config import TournamentConfig


def test_tournament_config_from_dict_parses_bool_values() -> None:
    assert TournamentConfig.from_dict({"allow_draws": False}).allow_draws is False
    assert TournamentConfig.from_dict({"allow_draws": True}).allow_draws is True
    assert TournamentConfig.from_dict({"allow_draws": "false"}).allow_draws is False
    assert TournamentConfig.from_dict({"allow_draws": "0"}).allow_draws is False
    assert TournamentConfig.from_dict({"allow_draws": "true"}).allow_draws is True


def test_tournament_config_from_dict_rejects_invalid_bool_strings() -> None:
    with pytest.raises(ValueError):
        TournamentConfig.from_dict({"allow_draws": "sometimes"})


def test_tournament_config_from_dict_requires_tiebreak_order_sequence() -> None:
    config = TournamentConfig.from_dict({"tiebreak_order": ["score", "wins"]})

    assert config.tiebreak_order == ["score", "wins"]

    with pytest.raises(ValueError):
        TournamentConfig.from_dict({"tiebreak_order": "score"})


def test_audit_log_entry_from_dict_coerces_round_number_and_hashes() -> None:
    entry = AuditLogEntry.from_dict(
        {
            "id": 123,
            "timestamp": "2026-06-22T00:00:00+00:00",
            "event_type": "pairing",
            "actor": "cli",
            "summary": "Round paired",
            "round_number": "2",
            "details": {},
            "state_hash_before": 987,
            "state_hash_after": None,
        }
    )

    assert entry.id == "123"
    assert entry.round_number == 2
    assert entry.state_hash_before == "987"
    assert entry.state_hash_after is None
