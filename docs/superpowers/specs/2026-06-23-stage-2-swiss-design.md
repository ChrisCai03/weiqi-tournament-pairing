# Stage 2 Swiss Workflow Design

## Goal

Extend the Stage 1 foundation into a usable Swiss tournament workflow for individual Weiqi/Go events. Stage 2 should cover standings, round generation, result entry, and later-round regeneration, while still being implemented in smaller slices that can be committed independently.

## Scope

Stage 2 covers:

- round/game/result domain objects
- standings calculation
- round 1 Swiss pairing
- result entry
- later-round Swiss pairing
- regeneration after earlier results change
- pairing explanations and audit events

Stage 2 does not yet cover:

- manual pairing override UI flows
- PDF export
- McMahon pairing
- team events
- web UI

## Delivery Strategy

Stage 2 should be built as a sequence of small, complete slices rather than one large engine drop. Each slice must leave the repository in a coherent, testable state and be safe to commit on its own.

Recommended slices:

1. Slice A: round/game/result domain objects and persistence
2. Slice B: standings and tie-break baseline
3. Slice C: round 1 Swiss pairing
4. Slice D: result entry
5. Slice E: later-round Swiss pairing
6. Slice F: regeneration, stale-round handling, and explanations

This approach keeps the engine grounded in the real tournament workflow while still respecting the project's local-first, correctness-first philosophy.

## Current Foundation

Stage 1 already provides:

- `Tournament`, `Player`, `TournamentConfig`, and `AuditLogEntry`
- schema-versioned `.tgo.json` save/load
- CSV player import
- CLI commands for tournament creation and player import
- validation for round counts, seed assignment, and rank consistency

Stage 2 should grow from these files and patterns rather than introducing a separate application layer or new storage model.

## Architectural Direction

The Swiss engine should remain pure application logic. CLI commands should orchestrate the workflow, but the pairing and standings rules should live in dedicated engine modules so they can later support a local web UI and future McMahon support.

The main architectural change in Stage 2 is to replace the current placeholder `rounds: list[dict[str, object]]` with structured round/game/result domain objects and then build the Swiss services around those typed objects.

## Data Model Changes

### Round

Represents one tournament round.

Fields:

- `number`
- `status`
- `generated_at`
- `completed_at`
- `pairing_method`
- `pairing_seed`
- `games`
- `is_regenerated`
- `supersedes_round_version`
- `explanation_summary`

Initial statuses:

- `draft`
- `published`
- `completed`
- `stale`

For Stage 2, rounds can remain in `draft` and `completed` states operationally, with `published` and `stale` reserved for regeneration and future UI clarity.

### Game

Represents one board pairing.

Fields:

- `id`
- `round_number`
- `board_number`
- `black_player_id`
- `white_player_id`
- `handicap`
- `komi`
- `result`
- `pairing_explanation`
- `override_origin`

Stage 2 assumptions:

- handicap is always `0`
- komi is configurable later; for now it may default to `0.0` or remain purely informational
- games are individual only

### Result

Represents the outcome attached to a game.

Fields:

- `status`
- `winner_player_id`
- `result_type`
- `entered_at`
- `entered_by`
- `notes`
- `correction_of`

Supported result types in Stage 2:

- `normal`
- `bye`
- `forfeit`
- `void`

The result model should support unfinished games by using a status such as `pending`.

## Persistence Rules

The `.tgo.json` format remains the canonical save format.

Stage 2 should still use schema version `1` unless the existing structure becomes incompatible. Since Stage 1 already stores `rounds` as generic dictionaries, typed `Round` and `Game` objects can be serialized into the same top-level shape without forcing a migration.

Persistence requirements:

- save/load remains atomic
- all round, game, and result objects must round-trip cleanly
- invalid player references inside games must be rejected at load time
- invalid round numbering or duplicate board numbers within a round must be rejected at load time

## Standings Model

Stage 2 standings should be computed from completed rounds and completed game results.

For each player, standings should calculate:

- total score
- wins
- losses
- byes received
- opponents played
- colour history
- SOS
- SOSOS

Stage 2 assumptions:

- score uses existing tournament config values
- only completed or scored results contribute to standings
- pending games do not yet contribute
- direct encounter is deferred until later unless it falls out naturally from the model

Sorting order for Swiss decisions and standings display:

1. total score
2. wins
3. SOS
4. SOSOS
5. rank strength
6. seed number
7. stable player id

This keeps the tournament deterministic while staying close to the current MVP design.

## Swiss Pairing Model

Stage 2 Swiss should be deterministic, explainable, and modest in scope. It does not need full FIDE Dutch compliance, but it should follow the same broad structure:

1. collect active players
2. compute standings
3. form score groups
4. pair within score groups where possible
5. float leftover players down when necessary
6. assign byes for odd player counts
7. assign colours
8. assign board numbers
9. record explanations and audit events

### Round 1 Pairing

Round 1 can use a simpler rule than later rounds.

Recommended policy:

- sort players by rank strength, then seed number, then stable id
- split into top half and bottom half
- pair corresponding players across halves
- assign colours deterministically using seed parity or first-board alternation

This is easy to test and produces a reasonable opening round without importing a large external dependency.

### Later-Round Pairing

Later rounds should use the current standings and pairing history.

Hard constraints:

- active player appears at most once in a round
- withdrawn players are excluded
- no repeated opponents unless no legal alternative exists
- one pairing bye maximum per player where possible

Soft preferences:

- same score group first
- similar rank strength
- avoid same school or club pairing where possible
- improve colour balance
- avoid three identical colours in a row when possible

The MVP algorithm can be deterministic rule-based with bounded backtracking inside score groups rather than full weighted matching.

## Bye Policy

When there is an odd number of active players:

- exactly one player receives a bye
- prefer the lowest-scoring eligible player
- avoid giving a second pairing bye to the same player when possible
- record the bye as a `Game` with one player slot empty or a dedicated bye representation inside the result model

For Stage 2, the simplest robust representation is still a `Game`-like record so the round remains structurally uniform.

## Colour Policy

Stage 2 colour tracking should be simple and explicit.

Track per player:

- total black games
- total white games
- recent colour sequence

Colour assignment preference order:

1. avoid third identical colour in a row
2. reduce black/white imbalance
3. use deterministic fallback ordering

The engine should produce a short explanation when colour preference could not be satisfied.

## Result Entry Workflow

Stage 2 should add a CLI-level result entry path.

Minimum workflow:

1. select tournament file
2. select round number
3. select board number or game id
4. submit result
5. validate that the game exists and the result is compatible with the players
6. save updated tournament
7. append audit event

Result entry must support:

- normal win for black
- normal win for white
- bye result
- forfeit result
- correction of an existing result

## Regeneration and Stale Rounds

Stage 2 includes later-round regeneration, but it should be introduced carefully.

Rules:

- if a result is changed in an already-scored earlier round, all later rounds are potentially affected
- later rounds after the changed round must be marked `stale`
- the director can explicitly regenerate from a chosen round boundary
- regeneration must be deterministic from saved tournament state plus config

The engine should not silently overwrite downstream rounds.

Recommended command behavior:

- result correction marks later rounds stale
- `pair-next-round` refuses to continue if earlier stale rounds exist
- `regenerate-from --round N` deletes and rebuilds rounds `N+1...`

This is stricter than some tournament tools, but it is clearer and safer for the MVP.

## CLI Additions

Stage 2 should add small, focused commands rather than a monolithic interface.

Recommended commands:

- `standings <tournament_path>`
- `pair-round <tournament_path>`
- `enter-result <tournament_path> --round <n> --board <n> --winner black|white`
- `enter-bye-result <tournament_path> --round <n> --board <n>`
- `regenerate-from <tournament_path> --round <n>`

Command naming can still be refined during planning, but the operational surface should stay this small.

## Engine Module Layout

Recommended additions under `src/pairing/engine/`:

- `standings.py`
- `history.py`
- `swiss.py`
- `bye.py`
- `colours.py`
- `explanations.py`

Recommended additions under `src/pairing/domain/`:

- `round.py`
- `game.py`
- `result.py`

This preserves the separation between state and behavior without over-abstraction.

## Testing Strategy for Stage 2

Stage 2 should continue the correctness-first style from Stage 1.

### Unit Tests

- round/game/result serialization
- standings calculation on small fixtures
- bye assignment
- colour history and colour preference
- round 1 pairing
- repeated-opponent avoidance in later rounds

### Regression Tests

Small tournament fixtures should be added for:

- even round 1 field
- odd player count with bye
- result entry then standings update
- later-round pairing with score groups
- correction creating stale later rounds

### Invariant Tests

Swiss pairing outputs must satisfy:

- no active player appears twice
- no withdrawn player appears
- odd player count gives exactly one bye
- board numbers are unique within a round
- same input state gives same pairing output

## Risks and Simplifications

Main risks:

- later-round pairing can become brittle if we mix hard rules and soft preferences without a clear ordering
- regeneration can corrupt history if stale rounds are overwritten implicitly
- standings logic can drift from pairing logic if history queries are duplicated across modules

Chosen simplifications:

- deterministic rule-based Swiss first, not weighted matching
- individual tournaments only
- no handicap logic yet
- no manual override editing flow yet

These choices are deliberate. The goal of Stage 2 is a trustworthy Swiss workflow, not a fully generalized pairing framework.

## Recommended Implementation Order

### Slice A: Structured Round State

Add typed `Round`, `Game`, and `Result` domain classes plus JSON round-trip coverage.

### Slice B: Standings Baseline

Implement standings and tie-break computation independent of pairing generation.

### Slice C: Round 1 Pairing

Add deterministic first-round Swiss pairing and a CLI command to create the first round.

### Slice D: Result Entry

Add result-entry commands and update standings tests against real saved rounds.

### Slice E: Later-Round Swiss

Add score-group pairing, bye allocation, repeat-opponent avoidance, and colour handling.

### Slice F: Regeneration and Explanations

Add stale-round marking, regeneration command, explanation summaries, and audit improvements.

## Success Criteria

Stage 2 is complete when a tournament director can:

1. create a tournament
2. import players
3. generate round 1 pairings
4. enter results
5. generate the next round
6. view deterministic standings
7. correct an earlier result
8. regenerate later rounds safely

All of that should work locally with JSON tournament files and a CLI, with strong automated test coverage and clear audit history.
