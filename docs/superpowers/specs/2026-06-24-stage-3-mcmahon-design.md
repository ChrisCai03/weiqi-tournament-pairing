# Stage 3 McMahon Workflow Design

## Goal

Add McMahon tournament support on top of the Stage 2 Swiss foundation, while keeping the pairing engine deterministic, explainable, and usable from the existing CLI.

## Scope

This stage covers:

- individual McMahon tournaments for Weiqi/Go
- manual dan/kyu ranks only
- McMahon starting-score and bar placement logic
- McMahon round generation, using the same repeat-opponent, colour, bye, and audit machinery as Swiss
- format-aware standings
- minimal CLI support for creating and running McMahon events

This stage does not yet cover:

- team McMahon events
- external rating/rank APIs
- manual pairing override workflows
- PDF export
- web UI
- advanced optimizer backends

## Assumptions

- The Stage 2 Swiss foundation is available in the branch before implementation begins.
- McMahon is a separate tournament format, not a hidden branch inside Swiss.
- The saved tournament file remains the canonical local-first source of truth.
- The format choice and bar settings must be reproducible from saved config and audit history.

## Recommended Architecture

Use one shared round-generation pipeline with format-specific policies.

- `Swiss` continues to handle the existing Swiss rules.
- `McMahon` reuses the same pairing search, bye handling, colour balancing, explanations, and audit trail.
- A small dispatcher chooses the correct generator from `Tournament.format`.
- Standing calculation stays centralized, but McMahon adds a starting-score layer before later-round grouping and sorting.

This keeps the codebase modular without splitting the project into two unrelated engines.

## Data Model Changes

### Tournament

The tournament format must support `swiss` and `mcmahon`.

### TournamentConfig

McMahon needs explicit, reproducible settings for bar placement and opening-score rules.

The MVP should persist:

- the pairing method or format
- the McMahon bar definition
- the starting-score policy used for rank bands
- the normal Swiss settings already used for history, colours, byes, and tie-breaks

### StandingEntry

Standings should expose McMahon-aware values in addition to the existing Swiss-style fields.

The MVP should surface:

- starting score
- current McMahon score
- raw game score
- SOS / SOSOS

### Round / Game / Result

No structural change is required beyond reusing the existing typed Stage 2 models.

Round metadata should still record:

- pairing format
- pair-generation seed
- explanation summary

## McMahon Pairing Rules

The first round uses the McMahon starting-score rule rather than a pure Swiss sort by raw strength.

Later rounds should:

1. sort by current McMahon score
2. form score groups
3. pair within groups where possible
4. float when necessary
5. avoid repeated opponents where possible
6. apply colour balancing and bye selection using the same policies as Swiss

Hard constraints remain the same as Swiss:

- a player appears at most once in a round
- withdrawn players are excluded
- repeated opponents are only allowed when no legal alternative exists
- a player should not receive a second pairing bye unless the tournament is already in a forced edge case

## CLI Surface

The MVP CLI should let a director:

- create a tournament in `mcmahon` format
- import players from CSV
- generate pairings
- enter results
- view standings

The command set stays small. The key addition is choosing `mcmahon` at tournament creation time and showing McMahon-aware standings.

## Explanations and Audit

McMahon pairings need to explain:

- why a player starts above or below the bar
- why a score group was formed
- why a float was used
- why a bye was assigned
- why a colour choice was made

Audit logs should record the format and bar policy used when the round was generated, so a later recalculation can be reproduced.

## Edge Cases

- players clustered on the bar
- no legal pairings inside a score group
- a forced float that crosses the bar
- low-ranked or unranked players in a McMahon event
- repeated-opponent pressure after a correction
- late entry into an in-progress McMahon tournament
- stale rounds after a corrected result

## Success Criteria

Stage 3 is complete when a director can:

1. create a McMahon tournament
2. import players with manual ranks
3. generate McMahon pairings
4. enter results
5. view McMahon-aware standings
6. regenerate later rounds after correction without losing auditability

## Implementation Note

The current worktree must stay on a branch that includes the Stage 2 Swiss foundation before coding begins. If the branch is ever recreated from main, Stage 2 needs to be merged or cherry-picked first.

## Implemented MVP Policy Clarification

The implemented Stage 3 baseline is intentionally a simplified McMahon
variant:

- one configurable ranked bar, defaulting to `1d`
- players at or above the bar start at `1.0`
- players below the bar, including unranked players, start at `0.0`
- current McMahon score is starting score plus game score
- pairing uses the shared score-group, bye, repeat-opponent, and colour logic

The current implementation does not provide rank-band starting scores,
separate upper and lower bars, SODOS, or handicap pairing. Those remain future
features and must not be inferred from the broader original design language.
