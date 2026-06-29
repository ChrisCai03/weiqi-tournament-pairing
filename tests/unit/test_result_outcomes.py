import csv
from io import StringIO

import pytest

from pairing.domain.config import TournamentConfig
from pairing.domain.game import Game
from pairing.domain.player import Player
from pairing.domain.result import Result
from pairing.domain.round import Round
from pairing.domain.tournament import Tournament
from pairing.engine.scoring import counts_as_played, result_contribution
from pairing.import_export.csv_export import results_to_csv


@pytest.mark.parametrize(
    ("outcome_code", "black_player_id", "white_player_id", "result_type", "winner", "scores"),
    [
        ("black_win", "black-1", "white-1", "normal", "black-1", (1.0, 0.0)),
        ("white_win", "black-1", "white-1", "normal", "white-1", (0.0, 1.0)),
        ("draw", "black-1", "white-1", "draw", None, (0.5, 0.5)),
        ("both_win", "black-1", "white-1", "both_win", None, (1.0, 1.0)),
        ("both_loss", "black-1", "white-1", "both_loss", None, (0.0, 0.0)),
        ("black_forfeit", "black-1", "white-1", "forfeit", "black-1", (1.0, 0.0)),
        ("white_forfeit", "black-1", "white-1", "forfeit", "white-1", (0.0, 1.0)),
        ("black_no_show", "black-1", "white-1", "no_show", "white-1", (0.0, 1.0)),
        ("white_no_show", "black-1", "white-1", "no_show", "black-1", (1.0, 0.0)),
        ("both_no_show", "black-1", "white-1", "no_show", None, (0.0, 0.0)),
        ("void", "black-1", "white-1", "void", None, (0.0, 0.0)),
        ("bye", "black-1", None, "bye", "black-1", (1.0, 0.0)),
        ("bye", None, "white-1", "bye", "white-1", (0.0, 1.0)),
    ],
)
def test_completed_outcome_maps_codes_to_completed_results(
    outcome_code: str,
    black_player_id: str | None,
    white_player_id: str | None,
    result_type: str,
    winner: str | None,
    scores: tuple[float, float],
) -> None:
    result = Result.completed_outcome(
        outcome_code=outcome_code,
        black_player_id=black_player_id,
        white_player_id=white_player_id,
        config=TournamentConfig(allow_draws=True),
        entered_by="test-suite",
        notes="verified",
    )

    assert result.status == "completed"
    assert result.result_type == result_type
    assert result.winner_player_id == winner
    assert result.black_score == scores[0]
    assert result.white_score == scores[1]
    assert result.outcome_code == outcome_code
    assert result.entered_by == "test-suite"
    assert result.notes == "verified"
    assert result.entered_at is not None


def test_completed_normal_result_preserves_legacy_shape_until_game_context_is_known() -> None:
    result = Result.completed(result_type="normal", winner_player_id="black-1")

    assert result.outcome_code is None
    assert result.black_score is None
    assert result.white_score is None

    normalized = result.with_game_context(
        black_player_id="black-1",
        white_player_id="white-1",
        config=TournamentConfig(),
    )

    assert normalized.outcome_code == "black_win"
    assert normalized.black_score == 1.0
    assert normalized.white_score == 0.0


def test_completed_outcome_rejects_draw_when_draws_are_disabled() -> None:
    with pytest.raises(ValueError, match="Draw outcomes require allow_draws=True"):
        Result.completed_outcome(
            outcome_code="draw",
            black_player_id="black-1",
            white_player_id="white-1",
            config=TournamentConfig(allow_draws=False),
        )


@pytest.mark.parametrize(
    ("black_player_id", "white_player_id"),
    [("black-1", "white-1"), (None, None)],
)
def test_completed_outcome_rejects_invalid_bye_shape(
    black_player_id: str | None, white_player_id: str | None
) -> None:
    with pytest.raises(ValueError, match="Bye outcomes require exactly one real player"):
        Result.completed_outcome(
            outcome_code="bye",
            black_player_id=black_player_id,
            white_player_id=white_player_id,
            config=TournamentConfig(),
        )


@pytest.mark.parametrize(
    ("payload", "message"),
    [
        (
            {
                "status": "completed",
                "result_type": "draw",
                "winner_player_id": None,
                "black_score": 0.5,
                "white_score": 0.5,
                "outcome_code": "black_win",
            },
            "Outcome code 'black_win' requires result type 'normal'",
        ),
        (
            {
                "status": "completed",
                "result_type": "normal",
                "winner_player_id": "black-1",
                "black_score": 1.0,
                "white_score": 0.0,
            },
            "Completed results with scores must define outcome_code",
        ),
        (
            {
                "status": "completed",
                "result_type": "normal",
                "winner_player_id": "black-1",
                "outcome_code": "black_win",
            },
            "Completed results with outcome_code must define both scores",
        ),
    ],
)
def test_result_from_dict_rejects_malformed_completed_payloads(
    payload: dict[str, object], message: str
) -> None:
    with pytest.raises(ValueError, match=message):
        Result.from_dict(payload)


def test_result_from_dict_rejects_pending_completion_metadata() -> None:
    with pytest.raises(ValueError, match="Pending results must not include completion metadata"):
        Result.from_dict(
            {
                "status": "pending",
                "result_type": "pending",
                "winner_player_id": "black-1",
                "entered_at": "2026-06-25T00:00:00+00:00",
            }
        )


def test_with_game_context_rejects_outcome_winner_on_wrong_player() -> None:
    result = Result.from_dict(
        {
            "status": "completed",
            "result_type": "normal",
            "winner_player_id": "white-1",
            "black_score": 1.0,
            "white_score": 0.0,
            "outcome_code": "black_win",
        }
    )

    with pytest.raises(ValueError, match="must name the black player as winner"):
        result.with_game_context(
            black_player_id="black-1",
            white_player_id="white-1",
            config=TournamentConfig(),
        )


def test_with_game_context_preserves_historical_scores_for_rich_results() -> None:
    result = Result.from_dict(
        {
            "status": "completed",
            "result_type": "normal",
            "winner_player_id": "black-1",
            "black_score": 2.0,
            "white_score": -1.0,
            "outcome_code": "black_win",
        }
    )

    normalized = result.with_game_context(
        black_player_id="black-1",
        white_player_id="white-1",
        config=TournamentConfig(),
    )

    assert normalized.black_score == 2.0
    assert normalized.white_score == -1.0
    assert normalized.outcome_code == "black_win"


@pytest.mark.parametrize(
    ("black_player_id", "white_player_id", "side", "expected_score"),
    [
        ("black-1", None, "black", 2.0),
        (None, "white-1", "white", 2.0),
    ],
)
def test_result_contribution_counts_rich_byes_from_persisted_outcome_scores(
    black_player_id: str | None,
    white_player_id: str | None,
    side: str,
    expected_score: float,
) -> None:
    result = Result.completed_outcome(
        outcome_code="bye",
        black_player_id=black_player_id,
        white_player_id=white_player_id,
        config=TournamentConfig(score_bye=2.0),
    )

    contribution = result_contribution(
        result,
        side=side,
        config=TournamentConfig(score_bye=1.0),
    )

    assert contribution.score == expected_score
    assert contribution.wins == 1
    assert contribution.byes == 1


@pytest.mark.parametrize(
    ("outcome_code", "side", "expected"),
    [
        ("black_forfeit", "black", {"wins": 1, "losses": 0, "forfeits": 0, "no_shows": 0}),
        ("black_forfeit", "white", {"wins": 0, "losses": 1, "forfeits": 1, "no_shows": 0}),
        ("white_no_show", "black", {"wins": 1, "losses": 0, "forfeits": 0, "no_shows": 0}),
        ("white_no_show", "white", {"wins": 0, "losses": 1, "forfeits": 0, "no_shows": 1}),
        ("both_no_show", "black", {"wins": 0, "losses": 1, "forfeits": 0, "no_shows": 1}),
        ("both_no_show", "white", {"wins": 0, "losses": 1, "forfeits": 0, "no_shows": 1}),
        ("both_win", "black", {"wins": 1, "losses": 0, "forfeits": 0, "no_shows": 0}),
        ("both_loss", "white", {"wins": 0, "losses": 1, "forfeits": 0, "no_shows": 0}),
        ("draw", "black", {"wins": 0, "losses": 0, "forfeits": 0, "no_shows": 0}),
        ("bye", "black", {"wins": 1, "losses": 0, "forfeits": 0, "no_shows": 0}),
        ("void", "white", {"wins": 0, "losses": 0, "forfeits": 0, "no_shows": 0}),
    ],
)
def test_result_contribution_tracks_score_and_counter_semantics(
    outcome_code: str, side: str, expected: dict[str, int]
) -> None:
    result = Result.completed_outcome(
        outcome_code=outcome_code,
        black_player_id="black-1",
        white_player_id=None if outcome_code == "bye" else "white-1",
        config=TournamentConfig(allow_draws=True),
    )

    contribution = result_contribution(result, side=side)

    assert contribution.score in {0.0, 0.5, 1.0}
    assert contribution.wins == expected["wins"]
    assert contribution.losses == expected["losses"]
    assert contribution.forfeits == expected["forfeits"]
    assert contribution.no_shows == expected["no_shows"]


def test_result_contribution_counts_white_side_rich_bye_as_win_and_bye() -> None:
    result = Result.completed_outcome(
        outcome_code="bye",
        black_player_id=None,
        white_player_id="white-1",
        config=TournamentConfig(allow_draws=True),
    )

    contribution = result_contribution(result, side="white")

    assert contribution.score == 1.0
    assert contribution.wins == 1
    assert contribution.byes == 1


def test_result_contribution_counts_zero_point_rich_bye_as_win_and_bye() -> None:
    result = Result.completed_outcome(
        outcome_code="bye",
        black_player_id=None,
        white_player_id="white-1",
        config=TournamentConfig(score_bye=0.0),
    )

    contribution = result_contribution(result, side="white")

    assert contribution.score == 0.0
    assert contribution.wins == 1
    assert contribution.byes == 1


def test_counts_as_played_honours_both_result_and_void_policies() -> None:
    result_both_win = Result.completed_outcome(
        outcome_code="both_win",
        black_player_id="black-1",
        white_player_id="white-1",
        config=TournamentConfig(),
    )
    result_both_loss = Result.completed_outcome(
        outcome_code="both_loss",
        black_player_id="black-1",
        white_player_id="white-1",
        config=TournamentConfig(),
    )
    result_void = Result.completed_outcome(
        outcome_code="void",
        black_player_id="black-1",
        white_player_id="white-1",
        config=TournamentConfig(),
    )
    legacy_both_win = Result.completed(result_type="both_win", winner_player_id=None)
    legacy_both_loss = Result.completed(result_type="both_loss", winner_player_id=None)

    strict_config = TournamentConfig(
        count_both_win_as_played=False,
        count_both_loss_as_played=False,
        count_void_as_played=False,
    )
    permissive_config = TournamentConfig(count_void_as_played=True)

    assert counts_as_played(result_both_win, strict_config) is False
    assert counts_as_played(result_both_loss, strict_config) is False
    assert counts_as_played(result_void, strict_config) is False
    assert counts_as_played(legacy_both_win, strict_config) is False
    assert counts_as_played(legacy_both_loss, strict_config) is False
    assert counts_as_played(result_both_win, TournamentConfig()) is True
    assert counts_as_played(result_both_loss, TournamentConfig()) is True
    assert counts_as_played(result_void, permissive_config) is True


def test_counts_as_played_treats_legacy_void_results_as_unplayed_by_default() -> None:
    legacy_void = Result.completed(result_type="void", winner_player_id=None)

    assert counts_as_played(legacy_void, TournamentConfig()) is False
    assert counts_as_played(legacy_void, TournamentConfig(count_void_as_played=True)) is True


def test_results_csv_includes_outcome_code_and_persisted_scores() -> None:
    tournament = Tournament.create("Example Weiqi Open")
    alice = Player.create("Alice", rank="3d", seed_number=1)
    bob = Player.create("Bob", rank="2d", seed_number=2)
    tournament.players.extend([alice, bob])

    game = Game.create(
        round_number=1,
        board_number=1,
        black_player_id=alice.id,
        white_player_id=bob.id,
        pairing_explanation=[],
    )
    game.result = Result.from_dict(
        {
            "status": "completed",
            "result_type": "both_win",
            "winner_player_id": None,
            "black_score": 2.0,
            "white_score": 2.0,
            "outcome_code": "both_win",
        }
    )
    tournament.rounds.append(
        Round.create(number=1, games=[game], pairing_method="swiss", pairing_seed=1)
    )

    rows = list(csv.DictReader(StringIO(results_to_csv(tournament))))

    assert rows == [
        {
            "Round": "1",
            "Board": "1",
            "Winner": "",
            "Result Type": "both_win",
            "outcome_code": "both_win",
            "black_score": "2.0",
            "white_score": "2.0",
            "Entered At": "",
        }
    ]


def test_results_csv_preserves_existing_prefix_and_appends_rich_columns() -> None:
    tournament = Tournament.create("Example Weiqi Open")
    alice = Player.create("Alice", rank="3d", seed_number=1)
    bob = Player.create("Bob", rank="2d", seed_number=2)
    tournament.players.extend([alice, bob])

    game = Game.create(
        round_number=1,
        board_number=1,
        black_player_id=alice.id,
        white_player_id=bob.id,
        pairing_explanation=[],
    )
    game.result = Result.from_dict(
        {
            "status": "completed",
            "result_type": "both_win",
            "winner_player_id": None,
            "black_score": 2.0,
            "white_score": 2.0,
            "outcome_code": "both_win",
        }
    )
    tournament.rounds.append(
        Round.create(number=1, games=[game], pairing_method="swiss", pairing_seed=1)
    )

    header = next(csv.reader(StringIO(results_to_csv(tournament))))

    assert header[:5] == ["Round", "Board", "Winner", "Result Type", "Entered At"]
    assert header[5:] == ["outcome_code", "black_score", "white_score"]
