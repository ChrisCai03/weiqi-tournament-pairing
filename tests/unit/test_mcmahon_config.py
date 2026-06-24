from pairing.domain.tournament import Tournament


def test_mcmahon_format_round_trips_through_save_model() -> None:
    tournament = Tournament.create("McMahon Open", round_count=5, format="mcmahon")

    payload = tournament.to_dict()
    restored = Tournament.from_dict(payload)

    assert restored.format == "mcmahon"
    assert restored.config.pairing_method == "mcmahon"
    assert restored.config.mcmahon_bar_rank == tournament.config.mcmahon_bar_rank
