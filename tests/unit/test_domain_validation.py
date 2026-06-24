import pytest

from pairing.domain import Game, Player, Result, Round, Tournament, TournamentConfig


@pytest.mark.parametrize("name", ["", "   "])
def test_tournament_create_rejects_blank_name(name: str) -> None:
    with pytest.raises(ValueError, match="Tournament name must not be blank"):
        Tournament.create(name)


@pytest.mark.parametrize("name", ["", "   "])
def test_player_create_rejects_blank_name(name: str) -> None:
    with pytest.raises(ValueError, match="Player name must not be blank"):
        Player.create(name, rank="1d")


def test_tournament_validation_rejects_duplicate_player_ids() -> None:
    tournament = Tournament.create("Validation Open")
    player = Player.create("Alice", rank="1d", seed_number=1)
    tournament.players.extend([player, player])

    with pytest.raises(ValueError, match="Duplicate player id"):
        tournament.validate()


def test_tournament_validation_rejects_duplicate_positive_seeds() -> None:
    tournament = Tournament.create("Validation Open")
    tournament.players.extend(
        [
            Player.create("Alice", rank="1d", seed_number=1),
            Player.create("Bob", rank="1k", seed_number=1),
        ]
    )

    with pytest.raises(ValueError, match="Duplicate player seed number"):
        tournament.validate()


def test_tournament_validation_rejects_non_positive_seed() -> None:
    tournament = Tournament.create("Validation Open")
    tournament.players.append(Player.create("Alice", rank="1d"))

    with pytest.raises(ValueError, match="seed number must be positive"):
        tournament.validate()


def test_tournament_validation_rejects_config_format_mismatch() -> None:
    tournament = Tournament.create("Validation Open", format="mcmahon")
    tournament.config.pairing_method = "swiss"

    with pytest.raises(ValueError, match="pairing method must match"):
        tournament.validate()


def test_tournament_validation_rejects_unknown_game_player() -> None:
    tournament = Tournament.create("Validation Open")
    alice = Player.create("Alice", rank="1d", seed_number=1)
    tournament.players.append(alice)
    game = Game.create(
        round_number=1,
        board_number=1,
        black_player_id=alice.id,
        white_player_id="missing",
        pairing_explanation=[],
    )
    tournament.rounds.append(
        Round.create(number=1, games=[game], pairing_method="swiss", pairing_seed=1)
    )

    with pytest.raises(ValueError, match="unknown player"):
        tournament.validate()


def test_tournament_validation_rejects_player_twice_in_round() -> None:
    tournament = Tournament.create("Validation Open")
    alice = Player.create("Alice", rank="1d", seed_number=1)
    bob = Player.create("Bob", rank="1k", seed_number=2)
    cara = Player.create("Cara", rank="2k", seed_number=3)
    tournament.players.extend([alice, bob, cara])
    tournament.rounds.append(
        Round.create(
            number=1,
            games=[
                Game.create(
                    round_number=1,
                    board_number=1,
                    black_player_id=alice.id,
                    white_player_id=bob.id,
                    pairing_explanation=[],
                ),
                Game.create(
                    round_number=1,
                    board_number=2,
                    black_player_id=alice.id,
                    white_player_id=cara.id,
                    pairing_explanation=[],
                ),
            ],
            pairing_method="swiss",
            pairing_seed=1,
        )
    )

    with pytest.raises(ValueError, match="appears more than once"):
        tournament.validate()


def test_tournament_validation_rejects_invalid_winner() -> None:
    tournament = Tournament.create("Validation Open")
    alice = Player.create("Alice", rank="1d", seed_number=1)
    bob = Player.create("Bob", rank="1k", seed_number=2)
    tournament.players.extend([alice, bob])
    game = Game.create(
        round_number=1,
        board_number=1,
        black_player_id=alice.id,
        white_player_id=bob.id,
        pairing_explanation=[],
    )
    game.result = Result.completed(result_type="normal", winner_player_id="missing")
    tournament.rounds.append(
        Round.create(number=1, games=[game], pairing_method="swiss", pairing_seed=1)
    )

    with pytest.raises(ValueError, match="winner must be one of the game players"):
        tournament.validate()


def test_tournament_validation_rejects_invalid_bye_shape() -> None:
    tournament = Tournament.create("Validation Open")
    alice = Player.create("Alice", rank="1d", seed_number=1)
    bob = Player.create("Bob", rank="1k", seed_number=2)
    tournament.players.extend([alice, bob])
    game = Game.create(
        round_number=1,
        board_number=1,
        black_player_id=alice.id,
        white_player_id=bob.id,
        pairing_explanation=[],
    )
    game.result = Result.completed(result_type="bye", winner_player_id=alice.id)
    tournament.rounds.append(
        Round.create(number=1, games=[game], pairing_method="swiss", pairing_seed=1)
    )

    with pytest.raises(ValueError, match="bye must contain exactly one player"):
        tournament.validate()


@pytest.mark.parametrize("status", ["unknown", "", "ACTIVE"])
def test_player_from_dict_rejects_unsupported_status(status: str) -> None:
    with pytest.raises(ValueError, match="Unsupported player status"):
        Player.from_dict(
            {
                "id": "player-1",
                "display_name": "Alice",
                "rank": "1d",
                "rank_sort_value": 1,
                "status": status,
                "seed_number": 1,
            }
        )


def test_config_rejects_unsupported_pairing_method() -> None:
    with pytest.raises(ValueError, match="Unsupported pairing method"):
        TournamentConfig.from_dict({"pairing_method": "round-robin"})
