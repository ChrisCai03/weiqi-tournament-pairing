from __future__ import annotations

from pairing.domain.player import Player
from pairing.engine.standings import StandingEntry


def select_bye_player(players: list[Player] | list[StandingEntry]) -> Player:
    if not players:
        raise ValueError("Cannot assign a bye without active players.")

    first_item = players[0]
    if hasattr(first_item, "player") and hasattr(first_item, "byes"):
        standings = list(players)
        eligible = [entry for entry in standings if entry.byes == 0]
        selection_pool = eligible if eligible else standings
        return selection_pool[-1].player

    return sorted(
        players,
        key=lambda player: (-player.rank_sort_value, player.seed_number, player.id),
    )[-1]
