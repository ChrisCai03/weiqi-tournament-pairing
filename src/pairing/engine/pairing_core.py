from __future__ import annotations

from pairing.engine.history import players_have_met
from pairing.engine.pairing_result import PairingWarning
from pairing.engine.standings import StandingEntry


def pair_score_groups(
    entries: list[StandingEntry],
    opponent_history: dict[str, list[str]],
) -> list[tuple[StandingEntry, StandingEntry]] | None:
    score_groups = group_entries_by_score(entries)
    group_signature = tuple(tuple(entry.player.id for entry in group) for group in score_groups)
    pairing_cache: dict[tuple[str, ...], list[tuple[StandingEntry, StandingEntry]] | None] = {}
    group_cache: dict[
        tuple[int, tuple[str, ...], tuple[tuple[str, ...], ...]],
        list[tuple[StandingEntry, StandingEntry]] | None,
    ] = {}
    return _pair_score_group_recursive(
        score_groups,
        group_signature,
        opponent_history,
        carry=(),
        group_index=0,
        pairing_cache=pairing_cache,
        group_cache=group_cache,
    )


def pair_score_groups_with_fallback(
    entries: list[StandingEntry],
    opponent_history: dict[str, list[str]],
) -> tuple[list[tuple[StandingEntry, StandingEntry]], list[PairingWarning]]:
    strict_pairings = pair_score_groups(entries, opponent_history)
    if strict_pairings is not None:
        return strict_pairings, []

    fallback = _pair_minimum_penalty(entries, opponent_history)
    if fallback is None:
        raise ValueError("Unable to generate pairings for the active field.")

    warnings = [
        PairingWarning(
            code="repeat_opponent",
            message=(
                f"Warning: {left.player.display_name} and {right.player.display_name} "
                "have already met; repeat pairing was unavoidable."
            ),
            player_ids=(left.player.id, right.player.id),
        )
        for left, right in fallback
        if players_have_met(opponent_history, left.player.id, right.player.id)
    ]
    return fallback, warnings


def group_entries_by_score(entries: list[StandingEntry]) -> list[list[StandingEntry]]:
    grouped: list[list[StandingEntry]] = []
    for entry in entries:
        if grouped and entry.score == grouped[-1][0].score:
            grouped[-1].append(entry)
        else:
            grouped.append([entry])
    return grouped


def pair_entries_without_floats(
    entries: list[StandingEntry],
    opponent_history: dict[str, list[str]],
    *,
    pairing_cache: dict[tuple[str, ...], list[tuple[StandingEntry, StandingEntry]] | None]
    | None = None,
) -> list[tuple[StandingEntry, StandingEntry]] | None:
    cache = pairing_cache if pairing_cache is not None else {}
    cache_key = tuple(entry.player.id for entry in entries)
    if cache_key in cache:
        return cache[cache_key]

    if not entries:
        cache[cache_key] = []
        return []

    first_entry = entries[0]
    for index in range(1, len(entries)):
        partner = entries[index]
        if players_have_met(opponent_history, first_entry.player.id, partner.player.id):
            continue
        remainder = entries[1:index] + entries[index + 1 :]
        paired_remainder = pair_entries_without_floats(
            remainder,
            opponent_history,
            pairing_cache=cache,
        )
        if paired_remainder is not None:
            result = [(first_entry, partner)] + paired_remainder
            cache[cache_key] = result
            return result

    cache[cache_key] = None
    return None


def _pair_score_group_recursive(
    score_groups: list[list[StandingEntry]],
    group_signature: tuple[tuple[str, ...], ...],
    opponent_history: dict[str, list[str]],
    *,
    carry: tuple[StandingEntry, ...],
    group_index: int,
    pairing_cache: dict[tuple[str, ...], list[tuple[StandingEntry, StandingEntry]] | None],
    group_cache: dict[
        tuple[int, tuple[str, ...], tuple[tuple[str, ...], ...]],
        list[tuple[StandingEntry, StandingEntry]] | None,
    ],
) -> list[tuple[StandingEntry, StandingEntry]] | None:
    if group_index >= len(score_groups):
        return [] if not carry else None

    cache_key = (group_index, tuple(entry.player.id for entry in carry), group_signature)
    if cache_key in group_cache:
        return group_cache[cache_key]

    current_group = score_groups[group_index]
    available = list(carry) + list(current_group)

    full_pairing = pair_entries_without_floats(
        available, opponent_history, pairing_cache=pairing_cache
    )
    if full_pairing is not None:
        rest = _pair_score_group_recursive(
            score_groups,
            group_signature,
            opponent_history,
            carry=(),
            group_index=group_index + 1,
            pairing_cache=pairing_cache,
            group_cache=group_cache,
        )
        if rest is not None:
            result = full_pairing + rest
            group_cache[cache_key] = result
            return result

    for float_index in range(len(available) - 1, -1, -1):
        floated_entry = available[float_index]
        remaining = available[:float_index] + available[float_index + 1 :]
        pairings = pair_entries_without_floats(
            remaining, opponent_history, pairing_cache=pairing_cache
        )
        if pairings is None:
            continue

        rest = _pair_score_group_recursive(
            score_groups,
            group_signature,
            opponent_history,
            carry=(floated_entry,),
            group_index=group_index + 1,
            pairing_cache=pairing_cache,
            group_cache=group_cache,
        )
        if rest is not None:
            result = pairings + rest
            group_cache[cache_key] = result
            return result

    group_cache[cache_key] = None
    return None


def _pair_minimum_penalty(
    entries: list[StandingEntry],
    opponent_history: dict[str, list[str]],
) -> list[tuple[StandingEntry, StandingEntry]] | None:
    if not entries:
        return []
    if len(entries) % 2:
        return None

    first = entries[0]
    best: (
        tuple[
            tuple[int, float, int, tuple[tuple[str, str], ...]],
            list[tuple[StandingEntry, StandingEntry]],
        ]
        | None
    ) = None
    for index in range(1, len(entries)):
        partner = entries[index]
        remainder = entries[1:index] + entries[index + 1 :]
        paired_remainder = _pair_minimum_penalty(remainder, opponent_history)
        if paired_remainder is None:
            continue
        candidate = [(first, partner)] + paired_remainder
        repeat_count = sum(
            players_have_met(opponent_history, left.player.id, right.player.id)
            for left, right in candidate
        )
        score_distance = sum(abs(left.score - right.score) for left, right in candidate)
        rank_distance = sum(
            abs(left.player.rank_sort_value - right.player.rank_sort_value)
            for left, right in candidate
        )
        signature = tuple((left.player.id, right.player.id) for left, right in candidate)
        cost = (repeat_count, score_distance, rank_distance, signature)
        if best is None or cost < best[0]:
            best = (cost, candidate)
    return None if best is None else best[1]
