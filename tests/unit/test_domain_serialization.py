import pytest

from pairing.domain.audit import AuditLogEntry
from pairing.domain.config import TournamentConfig
from pairing.domain.game import Game
from pairing.domain.participation import ParticipationRecord
from pairing.domain.player import Player
from pairing.domain.result import Result
from pairing.domain.round import Round
from pairing.domain.tournament import Tournament


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


@pytest.mark.parametrize("round_count", [0, -1])
def test_tournament_config_from_dict_rejects_non_positive_round_count(round_count: int) -> None:
    with pytest.raises(ValueError, match="Round count must be positive"):
        TournamentConfig.from_dict({"round_count": round_count})


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


def test_player_from_dict_rejects_inconsistent_rank_sort_value() -> None:
    with pytest.raises(ValueError, match="Inconsistent rank data"):
        Player.from_dict(
            {
                "id": "player-1",
                "display_name": "Alice",
                "rank": "3d",
                "rank_sort_value": -3,
            }
        )


def test_tournament_config_round_trip_preserves_result_outcome_defaults() -> None:
    restored = TournamentConfig.from_dict(TournamentConfig().to_dict())

    assert restored.score_both_win == 1.0
    assert restored.score_both_loss == 0.0
    assert restored.score_forfeit_win == 1.0
    assert restored.score_forfeit_loss == 0.0
    assert restored.score_no_show == 0.0
    assert restored.late_entry_missed_round_score == 0.0
    assert restored.count_both_win_as_played is True
    assert restored.count_both_loss_as_played is True
    assert restored.count_void_as_played is False
    assert restored.automatic_backup_before_destructive_change is True
    assert restored.backup_retention_count == 10


@pytest.mark.parametrize(
    ("field_name", "field_value"),
    [
        ("score_win", float("inf")),
        ("score_loss", float("-inf")),
        ("score_draw", float("nan")),
        ("score_bye", float("inf")),
        ("score_both_win", float("inf")),
        ("score_both_loss", float("inf")),
        ("score_forfeit_win", float("inf")),
        ("score_forfeit_loss", float("inf")),
        ("score_no_show", float("inf")),
        ("late_entry_missed_round_score", float("inf")),
    ],
)
def test_tournament_config_from_dict_rejects_non_finite_scores(
    field_name: str, field_value: float
) -> None:
    with pytest.raises(ValueError, match="must be finite"):
        TournamentConfig.from_dict({field_name: field_value})


@pytest.mark.parametrize("backup_retention_count", [0, -1])
def test_tournament_config_from_dict_rejects_non_positive_backup_retention_count(
    backup_retention_count: int,
) -> None:
    with pytest.raises(ValueError, match="positive"):
        TournamentConfig.from_dict({"backup_retention_count": backup_retention_count})


def test_result_from_dict_preserves_legacy_completed_shape_without_scores() -> None:
    result = Result.from_dict(
        {
            "status": "completed",
            "result_type": "normal",
            "winner_player_id": "player-black",
        }
    )

    assert result.outcome_code is None
    assert result.black_score is None
    assert result.white_score is None


def test_game_from_dict_normalizes_legacy_result_when_config_is_supplied() -> None:
    game = Game.from_dict(
        {
            "id": "game-1",
            "round_number": 1,
            "board_number": 1,
            "black_player_id": "player-black",
            "white_player_id": "player-white",
            "result": {
                "status": "completed",
                "result_type": "normal",
                "winner_player_id": "player-black",
            },
            "pairing_explanation": [],
        },
        config=TournamentConfig(),
    )

    assert game.result.outcome_code == "black_win"
    assert game.result.black_score == 1.0
    assert game.result.white_score == 0.0


def test_tournament_record_and_correct_result_persist_rich_result_shape() -> None:
    tournament = Tournament.create("Immediate Results Open")
    player_black = Player.create("Black", rank="1d", seed_number=1)
    player_white = Player.create("White", rank="1k", seed_number=2)
    tournament.players.extend([player_black, player_white])
    tournament.rounds.append(
        Round.create(
            number=1,
            games=[
                Game.create(
                    round_number=1,
                    board_number=1,
                    black_player_id=player_black.id,
                    white_player_id=player_white.id,
                    pairing_explanation=[],
                )
            ],
            pairing_method="swiss",
            pairing_seed=1,
        )
    )
    tournament.record_result(round_number=1, board_number=1, winner="black")

    recorded = tournament.rounds[0].games[0].result
    assert recorded.outcome_code == "black_win"
    assert recorded.black_score == 1.0
    assert recorded.white_score == 0.0

    tournament.correct_result(round_number=1, board_number=1, winner="white")

    corrected = tournament.rounds[0].games[0].result
    assert corrected.outcome_code == "white_win"
    assert corrected.black_score == 0.0
    assert corrected.white_score == 1.0
    assert corrected.correction_of is not None


def test_tournament_from_dict_loads_legacy_completed_results_without_scores() -> None:
    tournament = Tournament.create("Legacy Open")
    player_black = Player.create("Black", rank="1d", seed_number=1)
    player_white = Player.create("White", rank="1k", seed_number=2)
    player_bye = Player.create("Bye Player", rank="2k", seed_number=3)
    tournament.players.extend([player_black, player_white])
    tournament.players.append(player_bye)

    payload = tournament.to_dict()
    payload["rounds"] = [
        {
            "number": 1,
            "status": "completed",
            "generated_at": "2026-06-25T00:00:00+00:00",
            "completed_at": "2026-06-25T01:00:00+00:00",
            "pairing_method": "swiss",
            "pairing_seed": 1,
            "games": [
                {
                    "id": "legacy-game-1",
                    "round_number": 1,
                    "board_number": 1,
                    "black_player_id": player_black.id,
                    "white_player_id": player_white.id,
                    "handicap": 0,
                    "komi": 0.0,
                    "result": {
                        "status": "completed",
                        "result_type": "normal",
                        "winner_player_id": player_black.id,
                        "entered_by": "cli",
                        "notes": "",
                        "correction_of": None,
                    },
                    "pairing_explanation": [],
                    "override_origin": "engine",
                },
                {
                    "id": "legacy-game-2",
                    "round_number": 1,
                    "board_number": 2,
                    "black_player_id": player_bye.id,
                    "white_player_id": None,
                    "handicap": 0,
                    "komi": 0.0,
                    "result": {
                        "status": "completed",
                        "result_type": "bye",
                        "winner_player_id": player_bye.id,
                        "entered_by": "cli",
                        "notes": "",
                        "correction_of": None,
                    },
                    "pairing_explanation": [],
                    "override_origin": "engine",
                }
            ],
            "is_regenerated": False,
            "supersedes_round_version": None,
            "explanation_summary": [],
        }
    ]

    restored = Tournament.from_dict(payload)

    assert restored.rounds[0].games[0].result.result_type == "normal"
    assert restored.rounds[0].games[0].result.winner_player_id == player_black.id
    assert restored.rounds[0].games[0].result.black_score == 1.0
    assert restored.rounds[0].games[0].result.white_score == 0.0
    assert restored.rounds[0].games[0].result.outcome_code == "black_win"

    assert restored.rounds[0].games[1].result.result_type == "bye"
    assert restored.rounds[0].games[1].result.winner_player_id == player_bye.id
    assert restored.rounds[0].games[1].result.black_score == 1.0
    assert restored.rounds[0].games[1].result.white_score == 0.0
    assert restored.rounds[0].games[1].result.outcome_code == "bye"

    round_payload = restored.to_dict()["rounds"][0]
    assert round_payload["games"][0]["result"]["black_score"] == 1.0
    assert round_payload["games"][0]["result"]["white_score"] == 0.0
    assert round_payload["games"][0]["result"]["outcome_code"] == "black_win"
    assert round_payload["games"][1]["result"]["black_score"] == 1.0
    assert round_payload["games"][1]["result"]["white_score"] == 0.0
    assert round_payload["games"][1]["result"]["outcome_code"] == "bye"


def test_tournament_from_dict_normalizes_legacy_missing_participation_without_entries() -> None:
    tournament = Tournament.create("Legacy Participation Open")
    payload = tournament.to_dict()
    payload.pop("participation", None)

    restored = Tournament.from_dict(payload)

    assert restored.participation == []
    assert restored.to_dict()["participation"] == []


def test_tournament_participation_round_trip_preserves_status_reason_and_adjustment() -> None:
    tournament = Tournament.create("Participation Serialization Open")
    tournament.config.late_entry_missed_round_score = 0.5
    absent_player = Player.create("Absent", rank="1d", seed_number=1)
    late_player = Player.create("Late", rank="1k", seed_number=2)
    tournament.players.extend([absent_player, late_player])

    payload = tournament.to_dict()
    payload["players"] = [absent_player.to_dict(), late_player.to_dict()]
    payload["participation"] = [
        {
            "player_id": absent_player.id,
            "round_number": 2,
            "status": "absent",
            "reason": "travel",
            "score_adjustment": 0.0,
        },
        {
            "player_id": late_player.id,
            "round_number": 3,
            "status": "late_entry",
            "reason": "joined after round 2",
        },
    ]

    restored = Tournament.from_dict(payload)

    assert restored.participation == [
        ParticipationRecord(
            player_id=absent_player.id,
            round_number=2,
            status="absent",
            reason="travel",
            score_adjustment=0.0,
        ),
        ParticipationRecord(
            player_id=late_player.id,
            round_number=3,
            status="late_entry",
            reason="joined after round 2",
            score_adjustment=0.5,
        ),
    ]
    assert restored.to_dict()["participation"] == [
        {
            "player_id": absent_player.id,
            "round_number": 2,
            "status": "absent",
            "reason": "travel",
            "score_adjustment": 0.0,
        },
        {
            "player_id": late_player.id,
            "round_number": 3,
            "status": "late_entry",
            "reason": "joined after round 2",
            "score_adjustment": 0.5,
        },
    ]


@pytest.mark.parametrize(
    "round_number",
    ["2", 1.5, "1.5", 0, -1],
)
def test_participation_record_from_dict_parses_numeric_string_round_numbers(
    round_number: object,
) -> None:
    if round_number == "2":
        record = ParticipationRecord.from_dict(
            {"player_id": "player-1", "round_number": round_number, "status": "withdrawn"}
        )

        assert record.round_number == 2
        return

    with pytest.raises(ValueError):
        ParticipationRecord.from_dict(
            {"player_id": "player-1", "round_number": round_number, "status": "withdrawn"}
        )
