from pairing.domain.game import Game
from pairing.domain.player import Player
from pairing.domain.result import Result
from pairing.domain.round import Round
from pairing.domain.tournament import Tournament
from pairing.engine.history import colour_history_by_player, opponent_ids_by_player
from pairing.engine.standings import calculate_standings


def test_history_helpers_track_opponents_and_colours_for_paired_games_only() -> None:
    tournament = Tournament.create("Example Weiqi Open")
    alice = Player.create("Alice", rank="3d", seed_number=1)
    bob = Player.create("Bob", rank="2d", seed_number=2)
    charlie = Player.create("Charlie", rank="1d", seed_number=3)
    tournament.players.extend([alice, bob, charlie])

    paired_game = Game.create(
        round_number=1,
        board_number=1,
        black_player_id=alice.id,
        white_player_id=bob.id,
        pairing_explanation=[],
    )
    bye_game = Game.create(
        round_number=1,
        board_number=2,
        black_player_id=charlie.id,
        white_player_id=None,
        pairing_explanation=[],
    )
    tournament.rounds.append(
        Round.create(number=1, games=[paired_game, bye_game], pairing_method="swiss", pairing_seed=1)
    )

    assert opponent_ids_by_player(tournament) == {
        alice.id: [bob.id],
        bob.id: [alice.id],
        charlie.id: [],
    }
    assert colour_history_by_player(tournament) == {
        alice.id: ["black"],
        bob.id: ["white"],
        charlie.id: [],
    }


def test_calculate_standings_tracks_scores_byes_and_tiebreaks() -> None:
    tournament = Tournament.create("Example Weiqi Open")
    alice = Player.create("Alice", rank="3d", seed_number=1)
    bob = Player.create("Bob", rank="2d", seed_number=2)
    charlie = Player.create("Charlie", rank="1d", seed_number=3)
    diana = Player.create("Diana", rank="1k", seed_number=4)
    eve = Player.create("Eve", rank="2k", seed_number=5)
    tournament.players.extend([alice, bob, charlie, diana, eve])

    round_one_game_one = Game.create(
        round_number=1,
        board_number=1,
        black_player_id=alice.id,
        white_player_id=bob.id,
        pairing_explanation=[],
    )
    round_one_game_one.result = Result.completed(result_type="normal", winner_player_id=alice.id)
    round_one_game_two = Game.create(
        round_number=1,
        board_number=2,
        black_player_id=charlie.id,
        white_player_id=diana.id,
        pairing_explanation=[],
    )
    round_one_game_two.result = Result.completed(result_type="normal", winner_player_id=charlie.id)
    round_one_bye = Game.create(
        round_number=1,
        board_number=3,
        black_player_id=eve.id,
        white_player_id=None,
        pairing_explanation=[],
    )
    round_one_bye.result = Result.completed(result_type="bye", winner_player_id=eve.id)
    round_one = Round.create(
        number=1,
        games=[round_one_game_one, round_one_game_two, round_one_bye],
        pairing_method="swiss",
        pairing_seed=1,
    )
    round_one.status = "completed"

    round_two_game_one = Game.create(
        round_number=2,
        board_number=1,
        black_player_id=alice.id,
        white_player_id=charlie.id,
        pairing_explanation=[],
    )
    round_two_game_one.result = Result.completed(result_type="normal", winner_player_id=alice.id)
    round_two_game_two = Game.create(
        round_number=2,
        board_number=2,
        black_player_id=bob.id,
        white_player_id=eve.id,
        pairing_explanation=[],
    )
    round_two_game_two.result = Result.completed(result_type="normal", winner_player_id=bob.id)
    round_two = Round.create(
        number=2,
        games=[round_two_game_one, round_two_game_two],
        pairing_method="swiss",
        pairing_seed=1,
    )
    round_two.status = "completed"

    tournament.rounds.extend([round_one, round_two])

    standings = calculate_standings(tournament)

    assert [entry.player.display_name for entry in standings] == [
        "Alice",
        "Bob",
        "Charlie",
        "Eve",
        "Diana",
    ]

    alice_entry = next(entry for entry in standings if entry.player.id == alice.id)
    bob_entry = next(entry for entry in standings if entry.player.id == bob.id)
    charlie_entry = next(entry for entry in standings if entry.player.id == charlie.id)
    diana_entry = next(entry for entry in standings if entry.player.id == diana.id)
    eve_entry = next(entry for entry in standings if entry.player.id == eve.id)

    assert alice_entry.score == 2.0
    assert alice_entry.wins == 2
    assert alice_entry.losses == 0
    assert alice_entry.byes == 0
    assert alice_entry.opponents == [bob.id, charlie.id]
    assert alice_entry.colours == ["black", "black"]
    assert alice_entry.sos == 2.0
    assert alice_entry.sosos == 5.0

    assert bob_entry.score == 1.0
    assert bob_entry.wins == 1
    assert bob_entry.losses == 1
    assert bob_entry.byes == 0
    assert bob_entry.sos == 3.0
    assert bob_entry.sosos == 3.0

    assert charlie_entry.score == 1.0
    assert charlie_entry.wins == 1
    assert charlie_entry.losses == 1
    assert charlie_entry.byes == 0
    assert charlie_entry.sos == 2.0
    assert charlie_entry.sosos == 3.0

    assert eve_entry.score == 1.0
    assert eve_entry.wins == 1
    assert eve_entry.losses == 1
    assert eve_entry.byes == 1
    assert eve_entry.opponents == [bob.id]
    assert eve_entry.colours == ["white"]
    assert eve_entry.sos == 1.0
    assert eve_entry.sosos == 3.0

    assert diana_entry.score == 0.0
    assert diana_entry.wins == 0
    assert diana_entry.losses == 1
    assert diana_entry.byes == 0
    assert diana_entry.sos == 1.0
    assert diana_entry.sosos == 2.0


def test_calculate_standings_uses_rank_seed_and_player_id_as_final_sort_keys() -> None:
    tournament = Tournament.create("Example Weiqi Open")

    high_rank = Player.create("High Rank", rank="3d", seed_number=7)
    low_seed = Player.create("Low Seed", rank="1d", seed_number=1)
    high_seed = Player.create("High Seed", rank="1d", seed_number=2)
    alpha_id = Player.create("Alpha Id", rank="1k", seed_number=9)
    alpha_id.id = "alpha-player"
    omega_id = Player.create("Omega Id", rank="1k", seed_number=9)
    omega_id.id = "omega-player"

    tournament.players.extend([omega_id, high_seed, alpha_id, low_seed, high_rank])

    standings = calculate_standings(tournament)

    assert [entry.player.display_name for entry in standings] == [
        "High Rank",
        "Low Seed",
        "High Seed",
        "Alpha Id",
        "Omega Id",
    ]
