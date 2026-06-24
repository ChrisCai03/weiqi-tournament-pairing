from __future__ import annotations

from pairing.domain.player import Player


def assign_colours(player_one: Player, player_two: Player, *, board_number: int) -> tuple[str, str]:
    if board_number % 2 == 1:
        return player_one.id, player_two.id
    return player_two.id, player_one.id
