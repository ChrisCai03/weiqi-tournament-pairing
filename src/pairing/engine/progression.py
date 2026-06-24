from __future__ import annotations

from pairing.domain.tournament import Tournament


def validate_next_round_allowed(tournament: Tournament) -> None:
    if any(round_obj.status == "stale" for round_obj in tournament.rounds):
        raise ValueError("Tournament has stale rounds that must be regenerated first.")

    active_rounds = [
        round_obj for round_obj in tournament.rounds if round_obj.status != "stale"
    ]
    if not active_rounds:
        return

    previous_round = max(active_rounds, key=lambda round_obj: round_obj.number)
    if previous_round.status != "completed":
        raise ValueError(f"Round {previous_round.number} must be completed first.")
