from __future__ import annotations

from pathlib import Path

from pairing.application import TournamentService
from pairing.storage import load_tournament


def test_realistic_open_fixture_import_survives_reload(tmp_path) -> None:
    tournament_path = tmp_path / "realistic-open.tgo.json"
    fixture_path = (
        Path(__file__).resolve().parents[1] / "fixtures" / "players" / "realistic-open.csv"
    )

    TournamentService.create(
        tournament_path,
        name="Realistic Open",
        round_count=5,
        format="swiss",
        actor="test",
    )

    import_outcome = TournamentService(tournament_path).import_players_file(
        fixture_path,
        actor="test",
    )
    assert import_outcome.imported_count == 32

    loaded = load_tournament(tournament_path)
    assert len(loaded.players) == 32

    reloaded = load_tournament(tournament_path)
    assert len(reloaded.players) == 32

    seed_numbers = [player.seed_number for player in reloaded.players]
    assert sorted(seed_numbers) == list(range(1, 33))
    assert len(set(seed_numbers)) == 32

    ranks = [player.rank for player in reloaded.players]
    assert any(rank.endswith("d") for rank in ranks)
    assert any(rank.endswith("k") for rank in ranks)
    assert ranks.count("unranked") == 2

    by_name = {player.display_name: player for player in reloaded.players}
    assert by_name["Aiko Tan"].country == "Japan"
    assert by_name["Aiko Tan"].club == "Tokyo Go Club"
    assert by_name["Aiko Tan"].school == "Seishin High"

    assert by_name["Ben Liu"].country == "United States"
    assert by_name["Ben Liu"].club == "Bay Area Go Club"
    assert by_name["Ben Liu"].school == "Stanford University"

    assert by_name["Mina Okada"].country == "Canada"
    assert by_name["Mina Okada"].club == "Toronto Go Club"
    assert by_name["Mina Okada"].school == "University of Toronto"
