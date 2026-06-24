from __future__ import annotations

from pairing.domain.player import Player


def assign_colours(
    player_one: Player,
    player_two: Player,
    *,
    board_number: int,
    colour_history: dict[str, list[str]] | None = None,
) -> tuple[str, str]:
    if colour_history is None:
        if board_number % 2 == 1:
            return player_one.id, player_two.id
        return player_two.id, player_one.id

    forward_score = _colour_assignment_score(player_one, "black", colour_history) + _colour_assignment_score(
        player_two,
        "white",
        colour_history,
    )
    reverse_score = _colour_assignment_score(player_one, "white", colour_history) + _colour_assignment_score(
        player_two,
        "black",
        colour_history,
    )

    if forward_score < reverse_score:
        return player_one.id, player_two.id
    if reverse_score < forward_score:
        return player_two.id, player_one.id
    if board_number % 2 == 1:
        return player_one.id, player_two.id
    return player_two.id, player_one.id


def _colour_assignment_score(
    player: Player,
    assigned_colour: str,
    colour_history: dict[str, list[str]],
) -> int:
    history = colour_history.get(player.id, [])
    black_count = history.count("black") + (1 if assigned_colour == "black" else 0)
    white_count = history.count("white") + (1 if assigned_colour == "white" else 0)
    score = abs(black_count - white_count) * 10
    if len(history) >= 2 and history[-1] == history[-2] == assigned_colour:
        score += 5
    return score
