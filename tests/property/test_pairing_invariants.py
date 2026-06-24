from pathlib import Path
from tempfile import TemporaryDirectory

from hypothesis import given, settings
from hypothesis import strategies as st

from pairing.domain import Player, Tournament
from pairing.engine.round_generation import generate_next_round
from pairing.storage import load_tournament, save_tournament

RANKS = ["5d", "3d", "1d", "1k", "5k", "unranked"]


@given(
    ranks=st.lists(st.sampled_from(RANKS), min_size=1, max_size=20),
    format=st.sampled_from(["swiss", "mcmahon"]),
)
@settings(max_examples=50)
def test_round_one_pairing_invariants(ranks: list[str], format: str) -> None:
    tournament = Tournament.create("Property Open", format=format)
    tournament.players.extend(
        [
            Player.create(f"Player {index}", rank=rank, seed_number=index)
            for index, rank in enumerate(ranks, start=1)
        ]
    )

    round_obj = generate_next_round(tournament)
    appearances = [
        player_id
        for game in round_obj.games
        for player_id in (game.black_player_id, game.white_player_id)
        if player_id is not None
    ]
    bye_count = sum(game.result.result_type == "bye" for game in round_obj.games)

    assert sorted(appearances) == sorted(player.id for player in tournament.players)
    assert len(appearances) == len(set(appearances))
    assert bye_count == len(ranks) % 2


@given(
    ranks=st.lists(st.sampled_from(RANKS), min_size=2, max_size=12),
    format=st.sampled_from(["swiss", "mcmahon"]),
)
@settings(max_examples=30)
def test_round_one_pairing_is_deterministic_by_player_contract(
    ranks: list[str],
    format: str,
) -> None:
    def generate_pairs():
        tournament = Tournament.create("Deterministic Open", format=format)
        tournament.players.extend(
            [
                Player.create(f"Player {index}", rank=rank, seed_number=index)
                for index, rank in enumerate(ranks, start=1)
            ]
        )
        names = {player.id: player.display_name for player in tournament.players}
        round_obj = generate_next_round(tournament)
        return [
            (
                names[game.black_player_id],
                names.get(game.white_player_id, ""),
                game.result.result_type,
            )
            for game in round_obj.games
        ]

    assert generate_pairs() == generate_pairs()


@given(ranks=st.lists(st.sampled_from(RANKS), min_size=1, max_size=12))
@settings(max_examples=25)
def test_generated_tournament_round_trips_through_json(ranks) -> None:
    tournament = Tournament.create("Round Trip Property")
    tournament.players.extend(
        [
            Player.create(f"Player {index}", rank=rank, seed_number=index)
            for index, rank in enumerate(ranks, start=1)
        ]
    )
    tournament.rounds.append(generate_next_round(tournament))
    with TemporaryDirectory() as directory:
        path = Path(directory) / "property.tgo.json"
        save_tournament(tournament, path)
        loaded = load_tournament(path)

    assert loaded.to_dict() == tournament.to_dict()
