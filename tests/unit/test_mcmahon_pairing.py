from pairing.domain.player import Player
from pairing.domain.tournament import Tournament
from pairing.engine.mcmahon import mcmahon_starting_score
from pairing.engine.round_generation import generate_next_round


def test_mcmahon_starting_score_uses_the_bar_rank() -> None:
    tournament = Tournament.create("McMahon Open", format="mcmahon")
    tournament.config.mcmahon_bar_rank = "1d"

    stronger = Player.create("Strong", rank="3d", seed_number=1)
    weaker = Player.create("Weak", rank="2k", seed_number=2)

    assert mcmahon_starting_score(stronger, tournament) == 1.0
    assert mcmahon_starting_score(weaker, tournament) == 0.0


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
        (names[game.black_player_id], names[game.white_player_id])
        for game in round_obj.games
    ] == [
        ("Aya", "Ben"),
        ("Dina", "Cheng"),
    ]
