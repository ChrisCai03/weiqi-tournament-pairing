import pytest

from pairing.domain.player import Player
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
