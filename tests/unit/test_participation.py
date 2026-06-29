import math

import pytest

from pairing.domain.game import Game
from pairing.domain.participation import ParticipationRecord
from pairing.domain.player import Player
from pairing.domain.round import Round
from pairing.domain.tournament import Tournament


def _player(name: str, seed_number: int, *, status: str = "active") -> Player:
    player = Player.create(name, rank="1k", seed_number=seed_number)
    player.status = status
    return player


def _tournament(*players: Player, round_count: int = 5, late_entry_missed_round_score: float = 0.0) -> Tournament:
    tournament = Tournament.create("Participation Open", round_count=round_count)
    tournament.config.late_entry_missed_round_score = late_entry_missed_round_score
    tournament.players.extend(players)
    tournament.validate()
    return tournament


def test_default_participation_uses_player_status_without_materializing_records() -> None:
    active_player = _player("Active", 1)
    withdrawn_player = _player("Withdrawn", 2, status="withdrawn")
    tournament = _tournament(active_player, withdrawn_player)

    assert tournament.participation == []
    assert tournament.participation_status(active_player.id, 1) == "active"
    assert tournament.participation_status(withdrawn_player.id, 1) == "withdrawn"
    assert [player.id for player in tournament.eligible_players(1)] == [active_player.id]


def test_absence_only_applies_to_the_recorded_round() -> None:
    player = _player("Absent Once", 1)
    tournament = _tournament(player)
    tournament.participation.append(
        ParticipationRecord(player_id=player.id, round_number=2, status="absent", reason="travel")
    )
    tournament.validate()

    assert tournament.participation_status(player.id, 1) == "active"
    assert tournament.participation_status(player.id, 2) == "absent"
    assert tournament.participation_status(player.id, 3) == "active"
    assert [item.id for item in tournament.eligible_players(2)] == []
    assert [item.id for item in tournament.eligible_players(3)] == [player.id]


def test_withdrawal_persists_until_reentry() -> None:
    player = _player("Cycle Player", 1)
    tournament = _tournament(player)
    tournament.participation.extend(
        [
            ParticipationRecord(player_id=player.id, round_number=2, status="withdrawn"),
            ParticipationRecord(player_id=player.id, round_number=4, status="reentered"),
        ]
    )
    tournament.validate()

    assert tournament.participation_status(player.id, 1) == "active"
    assert tournament.participation_status(player.id, 2) == "withdrawn"
    assert tournament.participation_status(player.id, 3) == "withdrawn"
    assert tournament.participation_status(player.id, 4) == "reentered"
    assert tournament.participation_status(player.id, 5) == "active"
    assert [item.id for item in tournament.eligible_players(3)] == []
    assert [item.id for item in tournament.eligible_players(4)] == [player.id]


def test_late_entry_defaults_adjustment_from_tournament_config() -> None:
    player = _player("Late Arrival", 1)
    tournament = _tournament(player, late_entry_missed_round_score=0.5)
    tournament.participation.append(
        ParticipationRecord(player_id=player.id, round_number=3, status="late_entry")
    )
    tournament.validate()

    assert tournament.participation[0].score_adjustment == 0.5
    assert tournament.participation_status(player.id, 1) == "not_entered"
    assert tournament.participation_status(player.id, 2) == "not_entered"
    assert tournament.participation_status(player.id, 3) == "late_entry"
    assert tournament.participation_status(player.id, 4) == "active"
    assert [item.id for item in tournament.eligible_players(2)] == []
    assert [item.id for item in tournament.eligible_players(3)] == [player.id]


@pytest.mark.parametrize(
    ("earlier_status", "late_entry_round"),
    [("absent", 3), ("withdrawn", 4)],
)
def test_tournament_validation_rejects_participation_before_first_late_entry(
    earlier_status: str,
    late_entry_round: int,
) -> None:
    player = _player("Late History", 1)
    tournament = _tournament(player)
    tournament.participation.extend(
        [
            ParticipationRecord(player_id=player.id, round_number=2, status=earlier_status),
            ParticipationRecord(
                player_id=player.id,
                round_number=late_entry_round,
                status="late_entry",
            ),
        ]
    )

    with pytest.raises(ValueError, match="late entry"):
        tournament.validate()


def test_tournament_validation_rejects_games_for_ineligible_participation_states() -> None:
    late_entry_tournament = _tournament(_player("Late Entry", 1), _player("Opponent", 2))
    late_entry_player = late_entry_tournament.players[0]
    late_entry_tournament.participation.append(
        ParticipationRecord(player_id=late_entry_player.id, round_number=3, status="late_entry")
    )
    late_entry_tournament.rounds.append(
        Round.create(
            number=1,
            games=[
                Game.create(
                    round_number=1,
                    board_number=1,
                    black_player_id=late_entry_player.id,
                    white_player_id=late_entry_tournament.players[1].id,
                    pairing_explanation=[],
                )
            ],
            pairing_method=late_entry_tournament.format,
            pairing_seed=late_entry_tournament.config.random_seed,
        )
    )

    with pytest.raises(ValueError, match="not_entered"):
        late_entry_tournament.validate()

    absent_tournament = _tournament(_player("Absent", 1), _player("Opponent", 2))
    absent_player = absent_tournament.players[0]
    absent_tournament.participation.append(
        ParticipationRecord(player_id=absent_player.id, round_number=1, status="absent")
    )
    absent_tournament.rounds.append(
        Round.create(
            number=1,
            games=[
                Game.create(
                    round_number=1,
                    board_number=1,
                    black_player_id=absent_player.id,
                    white_player_id=absent_tournament.players[1].id,
                    pairing_explanation=[],
                )
            ],
            pairing_method=absent_tournament.format,
            pairing_seed=absent_tournament.config.random_seed,
        )
    )

    with pytest.raises(ValueError, match="absent"):
        absent_tournament.validate()

    active_tournament = _tournament(_player("Active", 1), _player("Opponent", 2))
    active_tournament.rounds.append(
        Round.create(
            number=1,
            games=[
                Game.create(
                    round_number=1,
                    board_number=1,
                    black_player_id=active_tournament.players[0].id,
                    white_player_id=active_tournament.players[1].id,
                    pairing_explanation=[],
                )
            ],
            pairing_method=active_tournament.format,
            pairing_seed=active_tournament.config.random_seed,
        )
    )
    active_tournament.validate()

    reentered_tournament = _tournament(_player("Withdrawn", 1), _player("Opponent", 2))
    reentered_player = reentered_tournament.players[0]
    reentered_tournament.participation.extend(
        [
            ParticipationRecord(player_id=reentered_player.id, round_number=1, status="withdrawn"),
            ParticipationRecord(player_id=reentered_player.id, round_number=2, status="reentered"),
        ]
    )
    reentered_tournament.rounds.append(
        Round.create(
            number=2,
            games=[
                Game.create(
                    round_number=2,
                    board_number=1,
                    black_player_id=reentered_player.id,
                    white_player_id=reentered_tournament.players[1].id,
                    pairing_explanation=[],
                )
            ],
            pairing_method=reentered_tournament.format,
            pairing_seed=reentered_tournament.config.random_seed,
        )
    )
    reentered_tournament.validate()


def test_participation_record_rejects_duplicate_player_round_entries() -> None:
    player = _player("Duplicate", 1)
    tournament = _tournament(player)
    tournament.participation.extend(
        [
            ParticipationRecord(player_id=player.id, round_number=2, status="withdrawn"),
            ParticipationRecord(player_id=player.id, round_number=2, status="absent"),
        ]
    )

    with pytest.raises(ValueError, match="Duplicate participation record"):
        tournament.validate()


def test_participation_record_rejects_unknown_players() -> None:
    player = _player("Known", 1)
    tournament = _tournament(player)
    tournament.participation.append(
        ParticipationRecord(player_id="missing-player", round_number=2, status="withdrawn")
    )

    with pytest.raises(ValueError, match="unknown player"):
        tournament.validate()


@pytest.mark.parametrize("round_number", [0, 6])
def test_participation_record_rejects_invalid_rounds(round_number: int) -> None:
    player = _player("Round Check", 1)
    tournament = _tournament(player, round_count=5)
    tournament.participation.append(
        ParticipationRecord(player_id=player.id, round_number=round_number, status="withdrawn")
    )

    with pytest.raises(ValueError, match="Participation round number"):
        tournament.validate()


@pytest.mark.parametrize("score_adjustment", [math.inf, math.nan])
def test_participation_record_rejects_non_finite_adjustments(score_adjustment: float) -> None:
    player = _player("Finite Please", 1)
    tournament = _tournament(player)
    tournament.participation.append(
        ParticipationRecord(
            player_id=player.id,
            round_number=2,
            status="late_entry",
            score_adjustment=score_adjustment,
        )
    )

    with pytest.raises(ValueError, match="Participation score adjustment must be finite"):
        tournament.validate()


@pytest.mark.parametrize("round_number", [1.5, 2.25])
def test_participation_record_rejects_non_integer_round_numbers(round_number: float) -> None:
    record = ParticipationRecord(player_id=" player-1 ", round_number=round_number, status="withdrawn")

    with pytest.raises(ValueError, match="Participation round number"):
        record.validate()


def test_tournament_validation_rejects_non_integer_participation_round_numbers() -> None:
    player = _player("Non Integer Round", 1)
    tournament = _tournament(player)
    tournament.participation.append(
        ParticipationRecord(player_id=player.id, round_number=1.5, status="withdrawn")
    )

    with pytest.raises(ValueError, match="Participation round number"):
        tournament.validate()


def test_participation_lookup_rejects_non_integer_round_numbers() -> None:
    player = _player("Lookup Round", 1)
    tournament = _tournament(player)

    with pytest.raises(ValueError, match="Participation round number"):
        tournament.participation_status(player.id, 1.5)

    with pytest.raises(ValueError, match="Participation round number"):
        tournament.eligible_players(1.5)


def test_participation_record_from_dict_rejects_non_integer_round_numbers() -> None:
    with pytest.raises(ValueError):
        ParticipationRecord.from_dict(
            {"player_id": "player-1", "round_number": 1.5, "status": "withdrawn"}
        )


def test_participation_validation_rejects_whitespace_variants_of_duplicate_player_ids() -> None:
    player = _player("Duplicate Trimmed", 1)
    tournament = _tournament(player)
    tournament.participation.extend(
        [
            ParticipationRecord(player_id=player.id, round_number=2, status="withdrawn"),
            ParticipationRecord(player_id=f" {player.id} ", round_number=2, status="absent"),
        ]
    )

    with pytest.raises(ValueError, match="Duplicate participation record"):
        tournament.validate()
