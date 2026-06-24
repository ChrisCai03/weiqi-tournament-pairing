from __future__ import annotations

from pairing.domain.player import Player
from pairing.engine.standings import StandingEntry


def select_bye_player(players: list[Player]) -> Player:
    if not players:
        raise ValueError("Cannot assign a bye without active players.")

    return sorted(
        players,
        key=lambda player: (-player.rank_sort_value, player.seed_number, player.id),
    )[-1]


def ordered_later_round_bye_candidates(standings: list[StandingEntry]) -> list[StandingEntry]:
    if not standings:
        raise ValueError("Cannot assign a bye without active players.")

    ordered = list(reversed(standings))
    no_previous_bye = [entry for entry in ordered if entry.byes == 0]
    repeat_bye = [entry for entry in ordered if entry.byes > 0]
    return no_previous_bye + repeat_bye
