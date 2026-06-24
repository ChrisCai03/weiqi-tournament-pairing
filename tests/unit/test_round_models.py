import pytest

from pairing.domain.game import Game
from pairing.domain.player import Player
from pairing.domain.result import Result
from pairing.domain.round import Round
from pairing.domain.tournament import Tournament


def test_result_round_trip() -> None:
    result = Result.pending()

    restored = Result.from_dict(result.to_dict())

    assert restored.status == "pending"
    assert restored.result_type == "pending"
    assert restored.winner_player_id is None


def test_round_round_trip() -> None:
    game = Game.create(
        round_number=1,
        board_number=1,
        black_player_id="player-a",
        white_player_id="player-b",
        pairing_explanation=["Top-half vs bottom-half opening pairing."],
    )
    round_obj = Round.create(number=1, games=[game], pairing_method="swiss", pairing_seed=1)

    restored = Round.from_dict(round_obj.to_dict())

    assert restored.number == 1
    assert restored.games[0].board_number == 1
    assert restored.games[0].black_player_id == "player-a"


def test_tournament_rounds_round_trip() -> None:
    tournament = Tournament.create("Example Weiqi Open")
    player_a = Player.create("Alice", rank="1d", seed_number=1)
    player_b = Player.create("Bob", rank="1k", seed_number=2)
    tournament.players.extend([player_a, player_b])
    game = Game.create(
        round_number=1,
        board_number=1,
        black_player_id=player_a.id,
        white_player_id=player_b.id,
        pairing_explanation=["Seeded opening pairing."],
    )
    tournament.rounds.append(
        Round.create(number=1, games=[game], pairing_method="swiss", pairing_seed=1)
    )

    restored = Tournament.from_dict(tournament.to_dict())

    assert restored.rounds[0].number == 1
    assert restored.rounds[0].games[0].board_number == 1


def test_tournament_rounds_round_trip_preserves_mcmahon_format() -> None:
    tournament = Tournament.create("McMahon Open", format="mcmahon")
    restored = Tournament.from_dict(tournament.to_dict())

    assert restored.format == "mcmahon"
    assert restored.config.pairing_method == "mcmahon"


def test_round_rejects_duplicate_board_numbers() -> None:
    game_one = Game.create(
        round_number=1,
        board_number=1,
        black_player_id="player-a",
        white_player_id="player-b",
        pairing_explanation=[],
    )
    game_two = Game.create(
        round_number=1,
        board_number=1,
        black_player_id="player-c",
        white_player_id="player-d",
        pairing_explanation=[],
    )

    with pytest.raises(ValueError, match="Duplicate board number"):
        Round.create(number=1, games=[game_one, game_two], pairing_method="swiss", pairing_seed=1)


def test_round_rejects_games_with_mismatched_round_number() -> None:
    game = Game.create(
        round_number=2,
        board_number=1,
        black_player_id="player-a",
        white_player_id="player-b",
        pairing_explanation=[],
    )

    with pytest.raises(ValueError, match="Game round number 2 does not match round 1"):
        Round.create(number=1, games=[game], pairing_method="swiss", pairing_seed=1)
