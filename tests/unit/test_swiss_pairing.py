import pytest

from pairing.domain.game import Game
from pairing.domain.player import Player
from pairing.domain.result import Result
from pairing.domain.round import Round
from pairing.domain.tournament import Tournament
from pairing.engine.swiss import generate_next_round


def test_generate_next_round_rejects_empty_active_field() -> None:
    tournament = Tournament.create("Example Weiqi Open")

    with pytest.raises(ValueError, match="at least one active player"):
        generate_next_round(tournament)


def test_generate_first_round_pairs_top_half_vs_bottom_half_in_sorted_order() -> None:
    tournament = Tournament.create("Example Weiqi Open")
    withdrawn = Player.create("Withdrawn", rank="9d", seed_number=99)
    withdrawn.status = "withdrawn"
    tournament.players.extend(
        [
            Player.create("Seed Two", rank="3d", seed_number=2),
            Player.create("Seed Four", rank="1k", seed_number=4),
            withdrawn,
            Player.create("Seed One", rank="4d", seed_number=1),
            Player.create("Seed Three", rank="1d", seed_number=3),
        ]
    )

    round_obj = generate_next_round(tournament)

    assert round_obj.number == 1
    assert [game.board_number for game in round_obj.games] == [1, 2]
    paired_ids = [
        frozenset((game.black_player_id, game.white_player_id))
        for game in round_obj.games
    ]
    active_players = sorted(
        (player for player in tournament.players if player.status == "active"),
        key=lambda player: (-player.rank_sort_value, player.seed_number, player.id),
    )
    assert paired_ids == [
        frozenset((active_players[0].id, active_players[2].id)),
        frozenset((active_players[1].id, active_players[3].id)),
    ]


def test_generate_first_round_assigns_bye_to_lowest_ranked_active_player() -> None:
    tournament = Tournament.create("Example Weiqi Open")
    tournament.players.extend(
        [
            Player.create("Alice", rank="4d", seed_number=1),
            Player.create("Bob", rank="3d", seed_number=2),
            Player.create("Charlie", rank="1d", seed_number=3),
            Player.create("Diana", rank="1k", seed_number=4),
            Player.create("Eve", rank="5k", seed_number=5),
        ]
    )

    round_obj = generate_next_round(tournament)

    assert round_obj.number == 1
    assert [game.board_number for game in round_obj.games] == [1, 2, 3]
    bye_game = next(game for game in round_obj.games if game.result.result_type == "bye")
    assert bye_game.result.status == "completed"
    assert bye_game.result.winner_player_id == tournament.players[4].id
    assert {bye_game.black_player_id, bye_game.white_player_id} == {tournament.players[4].id, None}


def test_generate_later_round_avoids_repeated_opponents_when_a_legal_alternative_exists() -> None:
    tournament = Tournament.create("Example Weiqi Open", round_count=3)
    alice = Player.create("Alice", rank="4d", seed_number=1)
    bob = Player.create("Bob", rank="3d", seed_number=2)
    cara = Player.create("Cara", rank="2d", seed_number=3)
    devin = Player.create("Devin", rank="1d", seed_number=4)
    tournament.players.extend([alice, bob, cara, devin])

    tournament.rounds.append(
        _completed_round(
            number=1,
            games=[
                _completed_game(
                    round_number=1,
                    board_number=1,
                    black_player_id=alice.id,
                    white_player_id=cara.id,
                    winner_player_id=alice.id,
                ),
                _completed_game(
                    round_number=1,
                    board_number=2,
                    black_player_id=bob.id,
                    white_player_id=devin.id,
                    winner_player_id=bob.id,
                ),
            ],
        )
    )

    round_two = generate_next_round(tournament)

    assert [game.board_number for game in round_two.games] == [1, 2]
    assert [
        frozenset((game.black_player_id, game.white_player_id))
        for game in round_two.games
    ] == [
        frozenset((alice.id, bob.id)),
        frozenset((cara.id, devin.id)),
    ]


def test_generate_later_round_assigns_one_bye_to_the_lowest_scoring_eligible_player() -> None:
    tournament = Tournament.create("Example Weiqi Open", round_count=3)
    alice = Player.create("Alice", rank="5d", seed_number=1)
    bob = Player.create("Bob", rank="4d", seed_number=2)
    cara = Player.create("Cara", rank="3d", seed_number=3)
    devin = Player.create("Devin", rank="2d", seed_number=4)
    eve = Player.create("Eve", rank="1d", seed_number=5)
    tournament.players.extend([alice, bob, cara, devin, eve])

    tournament.rounds.append(
        _completed_round(
            number=1,
            games=[
                _completed_game(
                    round_number=1,
                    board_number=1,
                    black_player_id=alice.id,
                    white_player_id=cara.id,
                    winner_player_id=alice.id,
                ),
                _completed_game(
                    round_number=1,
                    board_number=2,
                    black_player_id=bob.id,
                    white_player_id=devin.id,
                    winner_player_id=bob.id,
                ),
                _bye_game(
                    round_number=1,
                    board_number=3,
                    player_id=eve.id,
                ),
            ],
        )
    )

    round_two = generate_next_round(tournament)

    bye_games = [game for game in round_two.games if game.result.result_type == "bye"]
    assert len(bye_games) == 1
    assert bye_games[0].result.winner_player_id == devin.id


def test_generate_later_round_falls_back_to_repeat_bye_when_the_first_choice_dead_ends() -> None:
    tournament = Tournament.create("Example Weiqi Open", round_count=3)
    a = Player.create("A", rank="5d", seed_number=1)
    b = Player.create("B", rank="4d", seed_number=2)
    c = Player.create("C", rank="3d", seed_number=3)
    d = Player.create("D", rank="2d", seed_number=4)
    e = Player.create("E", rank="1d", seed_number=5)
    tournament.players.extend([a, b, c, d, e])

    tournament.rounds.extend(
        [
            _completed_round(
                number=1,
                games=[
                    _completed_game(
                        round_number=1,
                        board_number=1,
                        black_player_id=a.id,
                        white_player_id=b.id,
                        winner_player_id=a.id,
                    ),
                    _completed_game(
                        round_number=1,
                        board_number=2,
                        black_player_id=c.id,
                        white_player_id=d.id,
                        winner_player_id=c.id,
                    ),
                    _bye_game(
                        round_number=1,
                        board_number=3,
                        player_id=e.id,
                    ),
                ],
            ),
            _completed_round(
                number=2,
                games=[
                    _completed_game(
                        round_number=2,
                        board_number=1,
                        black_player_id=a.id,
                        white_player_id=b.id,
                        winner_player_id=a.id,
                    ),
                    _completed_game(
                        round_number=2,
                        board_number=2,
                        black_player_id=d.id,
                        white_player_id=c.id,
                        winner_player_id=d.id,
                    ),
                    _bye_game(
                        round_number=2,
                        board_number=3,
                        player_id=e.id,
                    ),
                ],
            ),
        ]
    )

    round_three = generate_next_round(tournament)

    assert round_three.number == 3
    assert [game.board_number for game in round_three.games] == [1, 2, 3]
    repeated_pairs = {frozenset((a.id, b.id)), frozenset((c.id, d.id))}
    assert {
        frozenset((game.black_player_id, game.white_player_id))
        for game in round_three.games
        if game.result.result_type == "normal"
    }.isdisjoint(repeated_pairs)


def test_generate_later_round_orders_boards_by_score_group() -> None:
    tournament = Tournament.create("Example Weiqi Open", round_count=3)
    alice = Player.create("Alice", rank="8d", seed_number=1)
    bob = Player.create("Bob", rank="7d", seed_number=2)
    cara = Player.create("Cara", rank="6d", seed_number=3)
    devin = Player.create("Devin", rank="5d", seed_number=4)
    eve = Player.create("Eve", rank="4d", seed_number=5)
    frank = Player.create("Frank", rank="3d", seed_number=6)
    gina = Player.create("Gina", rank="2d", seed_number=7)
    hank = Player.create("Hank", rank="1d", seed_number=8)
    tournament.players.extend([alice, bob, cara, devin, eve, frank, gina, hank])

    tournament.rounds.append(
        _completed_round(
            number=1,
            games=[
                _completed_game(
                    round_number=1,
                    board_number=1,
                    black_player_id=alice.id,
                    white_player_id=eve.id,
                    winner_player_id=eve.id,
                ),
                _completed_game(
                    round_number=1,
                    board_number=2,
                    black_player_id=bob.id,
                    white_player_id=frank.id,
                    winner_player_id=frank.id,
                ),
                _completed_game(
                    round_number=1,
                    board_number=3,
                    black_player_id=cara.id,
                    white_player_id=gina.id,
                    winner_player_id=gina.id,
                ),
                _completed_game(
                    round_number=1,
                    board_number=4,
                    black_player_id=devin.id,
                    white_player_id=hank.id,
                    winner_player_id=hank.id,
                ),
            ],
        )
    )

    round_two = generate_next_round(tournament)

    assert [game.board_number for game in round_two.games] == [1, 2, 3, 4]
    assert [
        frozenset((game.black_player_id, game.white_player_id))
        for game in round_two.games
    ] == [
        frozenset((eve.id, frank.id)),
        frozenset((gina.id, hank.id)),
        frozenset((alice.id, bob.id)),
        frozenset((cara.id, devin.id)),
    ]


def test_generate_next_round_uses_actual_round_number_in_metadata_and_explanations() -> None:
    tournament = Tournament.create("Example Weiqi Open", round_count=3)
    tournament.players.extend(
        [
            Player.create("Alice", rank="4d", seed_number=1),
            Player.create("Bob", rank="3d", seed_number=2),
            Player.create("Charlie", rank="1d", seed_number=3),
            Player.create("Diana", rank="1k", seed_number=4),
        ]
    )
    existing_round = Round.create(
        number=1,
        games=[
            Game.create(
                round_number=1,
                board_number=1,
                black_player_id=tournament.players[0].id,
                white_player_id=tournament.players[1].id,
                pairing_explanation=["Already paired."],
            )
        ],
        pairing_method="swiss",
        pairing_seed=tournament.config.random_seed,
        explanation_summary=["Round 1 Swiss pairing generated."],
    )
    tournament.rounds.append(existing_round)

    round_obj = generate_next_round(tournament)

    assert round_obj.number == 2
    assert round_obj.explanation_summary == ["Round 2 Swiss pairing generated."]
    assert all("Round 2" in explanation for game in round_obj.games for explanation in game.pairing_explanation)


def test_generate_next_round_refuses_to_pair_beyond_configured_round_count() -> None:
    tournament = Tournament.create("Example Weiqi Open", round_count=1)
    tournament.players.extend(
        [
            Player.create("Alice", rank="4d", seed_number=1),
            Player.create("Bob", rank="3d", seed_number=2),
        ]
    )
    tournament.rounds.append(
        Round.create(
            number=1,
            games=[
                Game.create(
                    round_number=1,
                    board_number=1,
                    black_player_id=tournament.players[0].id,
                    white_player_id=tournament.players[1].id,
                    pairing_explanation=["Round 1 Swiss pairing generated."],
                )
            ],
            pairing_method="swiss",
            pairing_seed=tournament.config.random_seed,
            explanation_summary=["Round 1 Swiss pairing generated."],
        )
    )

    with pytest.raises(ValueError, match="configured number of rounds"):
        generate_next_round(tournament)


def _completed_game(
    *,
    round_number: int,
    board_number: int,
    black_player_id: str,
    white_player_id: str,
    winner_player_id: str,
) -> Game:
    game = Game.create(
        round_number=round_number,
        board_number=board_number,
        black_player_id=black_player_id,
        white_player_id=white_player_id,
        pairing_explanation=[],
    )
    game.result = Result.completed(result_type="normal", winner_player_id=winner_player_id)
    return game


def _bye_game(*, round_number: int, board_number: int, player_id: str) -> Game:
    game = Game.create(
        round_number=round_number,
        board_number=board_number,
        black_player_id=player_id,
        white_player_id=None,
        pairing_explanation=[],
    )
    game.result = Result.completed(result_type="bye", winner_player_id=player_id)
    return game


def _completed_round(*, number: int, games: list[Game]) -> Round:
    round_obj = Round.create(number=number, games=games, pairing_method="swiss", pairing_seed=1)
    round_obj.status = "completed"
    return round_obj
