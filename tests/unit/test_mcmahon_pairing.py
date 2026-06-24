import pytest

from pairing.domain.game import Game
from pairing.domain.player import Player
from pairing.domain.result import Result
from pairing.domain.round import Round
from pairing.domain.tournament import Tournament
from pairing.engine.mcmahon import mcmahon_starting_score
from pairing.engine.round_generation import generate_next_round


def test_mcmahon_starting_score_uses_the_bar_rank() -> None:
    tournament = Tournament.create("McMahon Open", format="mcmahon")
    tournament.config.mcmahon_bar_rank = "1d"

    stronger = Player.create("Strong", rank="3d", seed_number=1)
    weaker = Player.create("Weak", rank="2k", seed_number=2)
    on_bar = Player.create("On Bar", rank="1d", seed_number=3)
    unranked = Player.create("Unranked", rank="unranked", seed_number=4)

    assert mcmahon_starting_score(stronger, tournament) == 1.0
    assert mcmahon_starting_score(weaker, tournament) == 0.0
    assert mcmahon_starting_score(on_bar, tournament) == 1.0
    assert mcmahon_starting_score(unranked, tournament) == 0.0


def test_generate_next_round_uses_mcmahon_generator() -> None:
    tournament = Tournament.create("McMahon Open", format="mcmahon")
    tournament.players.extend(
        [
            Player.create("Alice", rank="4d", seed_number=1),
            Player.create("Bob", rank="3d", seed_number=2),
            Player.create("Charlie", rank="1d", seed_number=3),
            Player.create("Diana", rank="1k", seed_number=4),
        ]
    )

    round_obj = generate_next_round(tournament)

    assert round_obj.pairing_method == "mcmahon"
    assert round_obj.number == 1
    assert any("bar 1d" in item for item in round_obj.explanation_summary)
    assert all(
        any("starting scores" in item for item in game.pairing_explanation)
        for game in round_obj.games
    )


def test_generate_mcmahon_round_has_stable_bar_pairing_order() -> None:
    tournament = Tournament.create("McMahon Characterization", format="mcmahon")
    tournament.players.extend(
        [
            Player.create("Aya", rank="3d", seed_number=1),
            Player.create("Ben", rank="1d", seed_number=2),
            Player.create("Cheng", rank="1k", seed_number=3),
            Player.create("Dina", rank="3k", seed_number=4),
        ]
    )

    round_obj = generate_next_round(tournament)
    names = {player.id: player.display_name for player in tournament.players}

    assert [
        (names[game.black_player_id], names[game.white_player_id]) for game in round_obj.games
    ] == [
        ("Aya", "Ben"),
        ("Dina", "Cheng"),
    ]


def test_mcmahon_rejects_pending_previous_round() -> None:
    tournament = Tournament.create("McMahon Open", round_count=2, format="mcmahon")
    tournament.players.extend(
        [
            Player.create("Alice", rank="3d", seed_number=1),
            Player.create("Bob", rank="1d", seed_number=2),
        ]
    )
    tournament.rounds.append(generate_next_round(tournament))

    with pytest.raises(ValueError, match="Round 1 must be completed first"):
        generate_next_round(tournament)


def test_mcmahon_warns_when_repeat_is_unavoidable() -> None:
    tournament = Tournament.create("McMahon Repeat", round_count=2, format="mcmahon")
    alice = Player.create("Alice", rank="3d", seed_number=1)
    bob = Player.create("Bob", rank="1d", seed_number=2)
    tournament.players.extend([alice, bob])
    game = Game.create(
        round_number=1,
        board_number=1,
        black_player_id=alice.id,
        white_player_id=bob.id,
        pairing_explanation=[],
    )
    game.result = Result.completed(result_type="normal", winner_player_id=alice.id)
    round_one = Round.create(
        number=1,
        games=[game],
        pairing_method="mcmahon",
        pairing_seed=1,
    )
    round_one.status = "completed"
    tournament.rounds.append(round_one)

    round_two = generate_next_round(tournament)

    assert len(round_two.games) == 1
    assert any(
        "Warning:" in item and "already met" in item for item in round_two.explanation_summary
    )
