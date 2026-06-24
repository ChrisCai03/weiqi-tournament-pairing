from __future__ import annotations

from pairing.domain.player import Player


def round_pairing_explanation(
    *,
    round_number: int,
    top_player: Player,
    bottom_player: Player,
    pairing_method: str = "swiss",
) -> list[str]:
    return [
        (
            f"Round {round_number} {pairing_method.title()} pairing: matched top-half "
            f"{top_player.display_name} against bottom-half {bottom_player.display_name}."
        )
    ]


def bye_explanation(*, round_number: int, player: Player, pairing_method: str = "swiss") -> list[str]:
    return [
        f"Round {round_number} {pairing_method.title()} bye assigned to {player.display_name} as the lowest-ranked active player."
    ]


def round_summary(*, round_number: int, pairing_method: str = "swiss") -> list[str]:
    return [f"Round {round_number} {pairing_method.title()} pairing generated."]
