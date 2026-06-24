from __future__ import annotations

from pairing.domain.round import Round
from pairing.domain.tournament import Tournament
from pairing.engine.mcmahon import generate_next_round as generate_mcmahon_round
from pairing.engine.swiss import generate_next_round as generate_swiss_round


def generate_next_round(tournament: Tournament) -> Round:
    if tournament.format == "mcmahon":
        return generate_mcmahon_round(tournament)
    return generate_swiss_round(tournament)
