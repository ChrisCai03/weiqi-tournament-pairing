import pytest

from pairing.domain.config import TournamentConfig
from pairing.domain.tournament import Tournament


def test_mcmahon_format_round_trips_through_save_model() -> None:
    tournament = Tournament.create("McMahon Open", round_count=5, format="mcmahon")

    payload = tournament.to_dict()
    restored = Tournament.from_dict(payload)

    assert restored.format == "mcmahon"
    assert restored.config.pairing_method == "mcmahon"
    assert restored.config.mcmahon_bar_rank == tournament.config.mcmahon_bar_rank


def test_mcmahon_bar_must_be_a_ranked_value() -> None:
    with pytest.raises(ValueError, match="McMahon bar rank must be ranked"):
        TournamentConfig.from_dict(
            {
                "pairing_method": "mcmahon",
                "mcmahon_bar_rank": "unranked",
            }
        )
