from __future__ import annotations

from pairing.domain.player import Player


def select_bye_player(players: list[Player]) -> Player:
    if not players:
        raise ValueError("Cannot assign a bye without active players.")

    return sorted(
        players,
        key=lambda player: (-player.rank_sort_value, player.seed_number, player.id),
    )[-1]
