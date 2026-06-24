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


def bye_explanation(
    *, round_number: int, player: Player, pairing_method: str = "swiss"
) -> list[str]:
    return [
        f"Round {round_number} {pairing_method.title()} bye assigned to {player.display_name} as the lowest-ranked active player."
    ]


def round_summary(*, round_number: int, pairing_method: str = "swiss") -> list[str]:
    return [f"Round {round_number} {pairing_method.title()} pairing generated."]


def mcmahon_policy_summary(*, bar_rank: str) -> str:
    return (
        f"Simplified McMahon policy used bar {bar_rank}: players at or above "
        "the bar started at 1.0; players below it started at 0.0."
    )


def mcmahon_score_explanation(
    *,
    player_one: Player,
    player_two: Player,
    player_one_score: float,
    player_two_score: float,
    bar_rank: str,
) -> str:
    return (
        f"McMahon bar {bar_rank}; starting scores were "
        f"{player_one.display_name} {player_one_score:.1f} and "
        f"{player_two.display_name} {player_two_score:.1f}."
    )
