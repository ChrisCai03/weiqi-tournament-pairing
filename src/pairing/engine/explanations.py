from __future__ import annotations

from pairing.domain.player import Player


def first_round_pairing_explanation(*, top_player: Player, bottom_player: Player) -> list[str]:
    return [
        (
            "Round 1 Swiss pairing: matched top-half "
            f"{top_player.display_name} against bottom-half {bottom_player.display_name}."
        )
    ]


def bye_explanation(*, player: Player) -> list[str]:
    return [f"Round 1 Swiss bye assigned to {player.display_name} as the lowest-ranked active player."]
