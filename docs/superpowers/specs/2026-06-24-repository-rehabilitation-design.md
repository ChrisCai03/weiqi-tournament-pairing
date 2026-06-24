# Repository Rehabilitation Design

## Goal

Audit, refactor, and rehabilitate the complete Weiqi tournament pairing repository built across Stages 1–4. Establish a trustworthy local application baseline for one tournament director running one managing terminal, while preserving useful behavior and schema-version-1 tournament files.

This is not a feature expansion or visual redesign. Correctness, explicit contracts, test quality, maintainability, auditability, and reliable local operation take priority.

## Product Boundary

The supported operating model is:

- one tournament director
- one local Python process
- one canonical `.tgo.json` tournament file
- CLI and server-rendered web interfaces
- no concurrent writers
- no authentication, hosted service, or database

The web UI remains visually simple. Its purpose is to expose the same trusted workflows as the CLI.

## Repository Baseline

The latest implementation is on `codex/stage-4-web`. The `main` branch stops before the Stage 2 implementation.

Current capabilities:

- schema-versioned JSON persistence
- CSV player import
- deterministic Swiss and McMahon pairing
- standings and basic tie-break calculations
- result entry
- stale-round marking and regeneration
- CSV exports
- local WSGI web console
- public pairing display

The current suite reports 88 passing tests. Those tests provide a useful starting point, but they do not prove all advertised behavior.

## Stage-by-Stage Audit

### Stage 1: Domain, Storage, Import, and CLI Foundation

#### What is good

- Standard-library implementation keeps the dependency surface small.
- Dataclasses make persisted structures inspectable.
- JSON saves use a temporary sibling file and atomic replacement.
- Schema versions are checked on load.
- Rank parsing and CSV validation have focused tests.
- Invalid JSON and several malformed structures are rejected.

#### Problems

- Empty tournament and player names are accepted.
- Duplicate player IDs and duplicate positive seeds are accepted.
- Player statuses and tournament/config enum-like values are arbitrary strings.
- Tournament format and `config.pairing_method` can disagree.
- Complete aggregate validation is absent.
- Some deserializers coerce malformed data instead of rejecting it.
- The schema documentation no longer fully describes later-stage round structures.
- Several config fields claim policies that are not implemented.

### Stage 2: Swiss Workflow

#### What is good

- Typed round, game, and result models replaced generic dictionaries.
- Standings, history, colour allocation, byes, pairing search, and explanations are separated.
- Pairing is deterministic.
- Tests cover round-one seeding, score-group pairing, colour balancing, byes, standings, regeneration, and stale rounds.
- Later-round pairing uses bounded recursive search and caches.

#### Problems

- A later round can be generated while the previous round still has pending games.
- Completed pairing history ignores pending games, allowing players already paired in an unfinished round to be paired again.
- Repeated opponents are treated as impossible rather than as a last-resort warning, despite the design allowing unavoidable repeats.
- Round generation does not consistently create audit events.
- Result entry overwrites a prior result without a proper correction record.
- `correction_of` exists but is not meaningfully used.
- Regeneration purges history rather than retaining explicit supersession metadata.
- Bye explanations always describe a rank-based choice even when later rounds use score and prior-bye eligibility.
- Pairing explanations do not describe score groups, floats, colour choices, or compromises.
- Affiliation preferences are configured but ignored.
- Random seed is persisted but does not currently affect pairing.
- Round status transitions are only partially defined.

### Stage 3: McMahon Workflow

#### What is good

- Format dispatch is isolated.
- McMahon reuses the common standings and pairing machinery.
- Starting score is shown separately from game score.
- The CLI can create and run a McMahon tournament.

#### Problems

- Only two tests exercise McMahon pairing behavior.
- The implemented starting-score policy is binary: players at or above one bar receive `1.0`; everyone else receives `0.0`.
- The specification describes rank bands and reproducible bar policy more broadly than the implementation supports.
- McMahon-specific explanations do not explain starting score or bar placement.
- The same generic bye explanation is inaccurate for later McMahon rounds.
- Edge cases around the bar, unranked players, floats across the bar, and corrections are unproved.
- The Stage 3 claim of shared audit machinery is not fulfilled.

### Stage 4: CSV Export and Local Web

#### What is good

- The UI runs and renders the principal tournament workflow.
- The dependency-free WSGI server is suitable for the local-only scope.
- CSV exports are straightforward and inspectable.
- HTML output escapes most user-controlled labels.

#### Problems

- One 486-line module owns routing, form parsing, mutation, persistence, error handling, HTML, and CSS.
- CLI and web duplicate load-mutate-save orchestration.
- Unknown routes silently return the overview with status 200.
- HTTP methods are not constrained per route.
- Broad error handling can attempt a second failing load while rendering an error.
- There is no focused unexpected-error response.
- One web mutation test never reloads or checks the saved tournament.
- Only four web tests exist.
- Result labels and pairing explanations are overly generic.
- Player lookup is repeatedly linear.
- Startup depends on the correct worktree, `PYTHONPATH`, an existing file, and a foreground process.
- Port conflicts and browser discoverability are not handled clearly.

## Repository-Wide Technical Risks

### False Confidence From Test Count

The suite is green, but coverage is uneven:

- no property tests despite Hypothesis being installed
- no simulation tests
- no CLI/web state-equivalence tests
- little live-server coverage
- no complete persisted tournament workflow
- weak malformed aggregate coverage
- minimal McMahon regression coverage

### Model Claims Exceed Implemented Behavior

Persisted fields imply support for draws, affiliation avoidance, handicap policy, configurable tie-break order, manual overrides, correction ancestry, state hashes, and random seeds. Most are inert or only partially supported.

The rehabilitation must choose one of two treatments for each field:

1. implement and prove its contract, or
2. explicitly mark it reserved and prevent interfaces from claiming it is active.

### Branch and Handoff Ambiguity

Later stages exist in chained worktrees rather than the main branch. Documentation names stages but does not give a durable integration policy or maintenance history.

## Architectural Direction

```text
CLI / Local Web
       |
Application Services
       |
Tournament Aggregate ---- Pairing and Standings Engine
       |
JSON Repository / CSV Reports
```

### Domain Layer

Domain classes represent valid local tournament state.

Validation is divided into:

- field validation within each model
- aggregate validation across players, rounds, games, and results
- workflow validation in application services

The aggregate must reject:

- blank tournament and player names
- unsupported statuses, formats, result types, and policies
- non-positive or duplicate seeds
- duplicate IDs
- duplicate round numbers
- invalid or duplicate board numbers
- games referencing unknown players
- one player appearing twice in a round
- a normal game without two distinct players
- an invalid bye representation
- a winner who is not part of the game
- completed results missing required metadata
- impossible round/result status combinations
- tournament/config pairing-method disagreement

Validation runs before saving and after loading.

### Application Services

Create a focused `pairing.application` package. It owns complete use cases:

- create tournament
- import players
- generate next round
- regenerate from a boundary
- record or correct a result
- calculate standings
- export reports
- create demo tournament

Services:

- receive explicit actor information
- enforce workflow preconditions
- call pure engine functions
- append audit events
- validate the resulting aggregate
- save only after all steps succeed
- return typed results suitable for CLI and web presentation

CLI and web adapters must not independently mutate tournaments.

### Pairing Engine

The engine remains independent of storage and presentation.

Common mechanics may be shared only where Swiss and McMahon contracts genuinely match:

- opponent and colour history
- pairing search
- bye candidate evaluation
- colour allocation
- standings primitives

Format-specific policy remains explicit:

- initial ordering and starting scores
- score-group meaning
- explanations
- format validation

### Storage

Keep schema version 1 where valid files remain representable.

Storage guarantees:

- validate before save
- write a temporary sibling file
- flush and replace atomically
- leave the existing file unchanged on failure
- wrap invalid structures with actionable `TournamentStoreError` messages

If rehabilitation requires a persisted structural change, introduce schema version 2 with an explicit migration instead of silently changing version 1.

### CLI

The CLI remains the managing terminal and becomes a thin adapter:

- parse arguments
- call one application service
- print service results
- translate known failures to stderr and exit code 1

The installed `pairing` command and `python -m pairing.cli.main` must behave consistently.

### Web

Retain server-rendered WSGI and the current visual language.

Split into focused modules:

- application assembly and route dispatch
- route definitions and method policy
- form decoding
- action handlers calling application services
- HTML views
- HTTP responses
- server lifecycle

Required HTTP behavior:

- known GET routes return 200
- successful mutation redirects with 303
- invalid forms and domain failures return 400
- unknown routes return 404
- unsupported methods return 405 and `Allow`
- unexpected failures return 500 without mutating the file

## Correctness Policies

### Round Progression

A new round may be generated only when:

- no stale rounds exist
- the immediately preceding active round is completed
- the configured round count has not been exceeded
- at least one active player exists

The only exception is an explicit director repair or regeneration workflow.

### Pairing History

All non-stale pairings count as opponent and colour commitments, including games whose results are pending. Results affect scores; pairings affect repeat and colour history.

### Unavoidable Repeats

Avoid repeat opponents as a hard preference during normal search.

If no no-repeat solution exists:

- generate a deterministic least-bad repeated pairing
- attach explicit warnings and explanations
- record the compromise in the round audit event

The local director should not be stranded at the end of an otherwise valid tournament.

### Results and Corrections

Initial result entry and correction are distinct operations.

A correction:

- records the previous result
- writes an audit entry containing the previous result snapshot
- sets `correction_of` to that audit entry's ID
- appends a correction audit event
- marks later rounds stale
- never silently discards the prior value

Supported rehabilitation baseline:

- black win
- white win
- pairing bye

Draws, forfeits, voids, and no-shows remain reserved until separately designed and tested.

### Regeneration

Regeneration from round `N`:

- preserves rounds through `N`
- marks later rounds stale
- records complete snapshots of the stale rounds in the regeneration audit entry
- removes the stale rounds from the active `rounds` list after the audit snapshot exists
- creates the next replacement round
- records which rounds were superseded

This keeps active round numbers unique and remains compatible with schema version 1. Superseded rounds must not disappear without an audit snapshot.

### McMahon Baseline

The rehabilitation will document and test the actual MVP policy:

- one configurable bar rank
- players at or above the bar start at `1.0`
- players below the bar start at `0.0`
- current McMahon score equals starting score plus game score

This is intentionally a simplified McMahon variant. Rank-band starting scores, upper/lower bars, handicap policy, and SODOS are future work.

### Audit Events

State-changing services append events for:

- tournament creation
- player import
- round generation
- unavoidable pairing compromise
- initial result entry
- result correction
- downstream invalidation
- regeneration

Events include actor and relevant format, round, board, count, and compromise details.

Read-only exports do not mutate the tournament file merely to record access.

## Test Architecture

### Characterization Tests

Before refactoring, capture valid current behavior for:

- schema-v1 round trips
- Swiss deterministic fixtures
- McMahon deterministic fixtures
- standings and tie-break outputs
- CLI text and exit codes
- current UI pages and CSV layouts

### Domain and Storage Tests

Cover every invalid aggregate listed in the domain section, plus:

- failed save preserves the previous file
- malformed temporary files do not replace valid saves
- unknown schema versions remain rejected

### Application-Service Tests

Each service gets persisted workflow tests:

- successful mutation reloads to expected state
- audit event is correct
- invalid operation leaves file bytes unchanged
- equivalent CLI and web actions produce equivalent tournament state

### Pairing Tests

Add regression and property tests for:

- active players appear exactly once
- inactive players never appear
- even fields have no bye
- odd fields have one bye
- no player receives a second bye when an eligible alternative exists
- opponent history includes pending pairings
- no-repeat pairings are preferred
- unavoidable repeats produce warnings instead of failure
- colour assignment minimizes documented penalties
- deterministic input produces deterministic output
- round progression rejects pending predecessors

### McMahon Tests

Add:

- above/below-bar starting scores
- bar-edge ranks
- unranked players
- first and later rounds
- odd fields and repeat pressure
- corrections and regeneration
- explanations containing bar and score information

### Integration and Live Tests

- complete Swiss tournament through multiple rounds
- complete simplified McMahon tournament
- CSV import through CLI and web
- live WSGI server startup and HTTP requests
- port-conflict reporting
- all UI routes and mutations
- demo creation and startup

## Tooling

Add lightweight development tooling:

- Ruff for formatting and linting
- mypy or Pyright-compatible type checking for production modules
- pytest coverage reporting

Tooling is a quality gate, not an excuse for broad formatting churn. Add it after characterization tests protect behavior.

## Delivery Phases

### Phase 0: Audit Baseline

- commit this repository-wide design
- create the maintenance log
- document current branch/worktree state
- add characterization tests for fragile behavior

### Phase 1: Domain and Storage Integrity

- implement field and aggregate validation
- add storage failure guarantees
- define supported and reserved values
- update file-format documentation

### Phase 2: Application Services

- introduce repository/use-case boundaries
- move CLI workflows to services
- add audit event contracts
- test persistence and rollback behavior

### Phase 3: Pairing and Result Correctness

- enforce round progression
- separate pairing history from scored-result history
- implement unavoidable-repeat fallback
- repair result correction and regeneration history
- improve explanations

### Phase 4: McMahon Rehabilitation

- formalize the simplified policy
- expand regressions and edge cases
- correct explanations and documentation
- remove unsupported claims

### Phase 5: Web and CLI Adapters

- split the web modules
- move web mutations to services
- harden HTTP semantics
- simplify CLI dispatch
- preserve the simple UI

### Phase 6: System Tests and Tooling

- property tests
- simulation tests
- adapter-equivalence tests
- live-server tests
- lint, formatting, typing, and coverage gates

### Phase 7: Operations and Documentation

- reliable installation and launch instructions
- repeatable demo command
- clear URL and port-conflict behavior
- architecture documentation
- maintenance log and refreshed roadmap
- branch integration recommendation

### Phase 8: Final Verification

- full tests
- property/simulation tests
- lint and type checks
- Python compilation
- package installation smoke test
- CLI workflow smoke tests
- live browser verification
- sample UI left running

## Commit Strategy

Make small commits that each leave the repository coherent:

1. design and audit documentation
2. characterization tests
3. domain validation
4. storage guarantees
5. application services
6. CLI migration
7. pairing corrections
8. result/regeneration corrections
9. McMahon rehabilitation
10. web service migration
11. web module split
12. property/integration tests
13. tooling
14. operations and roadmap documentation
15. final cleanup

Every commit requires focused passing tests. Full-suite verification is required at phase boundaries.

## Revised Product Roadmap

### Milestone A: Repository Rehabilitation

Complete this design and establish one integration baseline.

### Milestone B: Tournament Director Essentials

- withdrawal, late entry, and re-entry
- explicit manual pairing repair and override records
- result correction UI
- audit-log display
- supported scoring configuration

### Milestone C: Reports and Tournament Trials

- print-friendly pages
- PDF after print layouts settle
- realistic tournament fixtures
- simulations and tournament-director feedback

### Milestone D: Pairing Quality

- affiliation preference
- richer float and colour policy
- expanded McMahon starting-score policies
- SODOS and Go-specific tie-breaks
- optional weighted matching

### Milestone E: Distribution

- one-command local launch
- backups and recovery
- desktop packaging evaluation

Multi-user networking remains deferred until the local product is proven.

## Success Criteria

Repository rehabilitation is complete when:

1. valid existing schema-v1 files still load
2. malformed aggregate state is rejected
3. CLI and web use the same application workflows
4. a pending round blocks normal next-round generation
5. unavoidable repeats produce explicit pairings and warnings
6. corrections and regeneration retain audit history
7. the simplified McMahon policy is accurately implemented, tested, and documented
8. the web code has focused modules and correct HTTP behavior
9. property and end-to-end tests cover core invariants
10. lint, type, test, compilation, packaging, CLI, server, and browser checks pass
11. maintenance and roadmap documentation accurately describe the repository
12. the sample UI can be launched reliably and remains available at handoff
