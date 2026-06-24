from __future__ import annotations

from pairing.engine.history import players_have_met
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
    pairing_cache: dict[tuple[str, ...], list[tuple[StandingEntry, StandingEntry]] | None] | None = None,
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

    full_pairing = pair_entries_without_floats(available, opponent_history, pairing_cache=pairing_cache)
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
        pairings = pair_entries_without_floats(remaining, opponent_history, pairing_cache=pairing_cache)
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
