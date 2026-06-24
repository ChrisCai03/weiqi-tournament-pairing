# Codebase Stabilization and Local UI Design

## Goal

Turn the current Stage 4 branch into a maintainable, correctness-first baseline for a single tournament director operating one local process. Preserve useful pairing work and the simple UI, while repairing architectural duplication, weak validation, shallow tests, startup friction, and unclear repository handoff.

## Current State

The latest implementation is on `codex/stage-4-web`, not `main`.

Implemented today:

- schema-versioned `.tgo.json` storage
- CSV player import
- Swiss and McMahon round generation
- result entry and standings
- stale-round regeneration
- CSV exports
- a standard-library WSGI web console
- a public pairing display

The full Stage 4 suite currently reports 88 passing tests. The sample UI renders successfully when its server is running.

## Audit Findings

### Strengths

- Pairing and standings logic are already separated from storage and UI.
- JSON saves are atomic.
- The engine is deterministic and has substantial unit coverage.
- Typed round, game, and result models replaced early dictionary placeholders.
- Existing files can be retained without a schema migration.
- Swiss and McMahon share useful pairing primitives.

### High-Priority Problems

1. Workflow logic is duplicated across CLI and web adapters.
2. `src/pairing/web/app.py` combines routing, mutation, rendering, HTTP responses, and styling in one 486-line module.
3. Web tests are shallow. One pairing test never reloads or asserts the saved round, so it can pass without proving the action worked.
4. Domain deserialization accepts several invalid enum-like values and incomplete cross-object invariants.
5. Pairing generation and exports do not consistently append the audit events promised by the product design.
6. Several persisted configuration fields advertise behavior the engine does not yet implement, including affiliation avoidance and broader result policies.
7. Launch instructions depend on the correct worktree, `PYTHONPATH`, a pre-existing tournament file, and a still-running foreground process. This made a working UI appear unavailable.
8. Stage 4 arrived as one large commit without its own approved design or implementation plan.
9. `main` lags behind later worktrees, making the repository's latest development easy to misidentify.
10. Project handoff notes describe future work but do not record maintenance decisions, known limitations, or verification history in a durable log.

## Scope

### Included

- preserve compatibility with schema version 1 tournament files
- introduce a small application-service layer for tournament operations
- make CLI and web thin adapters over those services
- strengthen domain and persisted-state validation
- add missing audit events for state-changing workflows
- split the web application into focused modules
- replace weak tests and add regression and invariant coverage
- improve local server startup, error reporting, and demo discoverability
- keep the current simple visual language
- create a maintenance log and refresh architecture and roadmap documentation
- commit each coherent, verified slice

### Deferred

- multi-user or concurrent editing
- authentication and authorization
- hosted deployment
- React, FastAPI, databases, or desktop packaging
- major visual redesign
- manual pairing override UI
- PDF output
- external rating APIs
- full FIDE Dutch compliance
- a general weighted-matching optimizer

## Architecture

The application will use five explicit layers:

```text
CLI / Local Web
       |
Application Services
       |
Domain Model ---- Pairing / Standings Engine
       |
JSON Store and CSV Export
```

### Domain

Domain objects represent valid tournament state. They validate their own fields and relationships that can be checked without I/O.

The tournament aggregate validates:

- supported format and status values
- config format consistency
- unique player IDs and positive unique seed numbers
- unique round numbers
- game references to known players
- one player appearing at most once per round
- valid bye structure
- result winner membership in the game
- round status and result consistency

Loading malformed persisted state must fail with a useful `TournamentStoreError`.

### Pairing and Standings Engine

Engine modules remain pure and independent of storage, CLI, and HTTP.

The existing deterministic Swiss and McMahon behavior remains the baseline. Refactoring must preserve pairing outputs unless a failing regression test demonstrates an actual correctness defect.

Configuration fields that are not implemented must be documented as reserved rather than presented as active behavior.

### Application Services

Create focused services for:

- importing players
- generating the next round
- regenerating from a boundary
- recording a result
- calculating display standings
- producing exports

Services receive a tournament or repository abstraction, enforce workflow rules, append audit events, and return typed outcomes. They do not render text or HTML.

CLI and web must call these services instead of reproducing load-mutate-save sequences.

### Storage

The existing JSON file remains the canonical local store.

The storage boundary will:

- retain atomic writes
- validate the complete aggregate after deserialization
- surface clear file and schema errors
- avoid hidden migrations

No schema version change is planned. If validation discovers an existing valid file that cannot be represented safely, that case must be documented and handled explicitly.

### Web

Keep the dependency-free WSGI approach for this stage.

Split responsibilities into modules such as:

- `web/app.py`: application assembly and dispatch
- `web/routes.py`: route matching and action orchestration
- `web/views.py`: page and section rendering
- `web/responses.py`: HTML, CSV, redirect, and error responses
- `web/server.py`: server startup and lifecycle

HTML may remain server-rendered with inline or shared CSS. The current tabs and workflow pages remain recognizable.

Unknown paths must return 404 rather than silently rendering the overview. Unsupported methods must return 405 with an `Allow` header. User input failures must render useful messages without corrupting saved state.

### CLI and Startup

The CLI remains the managing terminal.

Startup requirements:

- a documented command that works from the Stage 4 checkout
- clear display of the exact URL and tournament path
- actionable errors for missing files and occupied ports
- optional browser opening controlled by a flag
- a repeatable demo-data command or script that creates a sample tournament and starts the UI

The server remains foreground by default so its lifetime is obvious.

## Audit Policy

State-changing application services append audit entries for:

- players imported
- round generated
- round regeneration requested and completed
- result entered or corrected
- future rounds invalidated or purged

Export reads do not mutate tournament files merely to record an export. Export audit history is deferred until there is a separate durable event sink.

Audit entries should identify the actor (`cli` or `web`) and include relevant round, board, count, or format details.

## Error Handling

- Domain errors use `ValueError` or a focused domain exception with user-readable messages.
- Storage wraps malformed files and I/O failures in `TournamentStoreError`.
- Application services do not swallow exceptions.
- CLI translates known failures to stderr and a non-zero exit code.
- Web translates known failures to a 4xx response and unexpected failures to a 500 response without writing partial state.
- Save occurs only after the complete operation succeeds.

## Testing Strategy

### Regression Tests

- reload the file after every mutating CLI and web action
- prove the existing web pairing test fails if persistence is removed
- verify unknown routes, invalid methods, invalid forms, and occupied ports
- preserve deterministic Swiss and McMahon fixture outputs

### Domain and Storage Tests

- malformed enum-like values
- duplicate player, seed, round, and board identifiers
- unknown player references
- invalid bye and winner relationships
- invalid round/result status combinations
- schema version and atomic-save behavior

### Application-Service Tests

- each service performs one complete workflow
- audit events contain the expected actor and details
- failures leave persisted files unchanged
- CLI and web produce the same state for equivalent actions

### Invariant and Property Tests

Use Hypothesis for:

- every active player appearing at most once
- inactive players never being paired
- even fields producing no bye
- odd fields producing exactly one bye
- winner references belonging to their game
- save/load preserving valid generated tournaments

### Verification

Every implementation slice must run its focused tests before commit. Final verification requires:

- full test suite
- Python compilation
- CLI help and representative command smoke tests
- a live HTTP smoke test
- browser verification of overview, players, pairings, results, standings, exports, and display

## Delivery Slices

1. Commit this design and audit baseline.
2. Add characterization tests and correct shallow tests.
3. Add aggregate validation and storage regression coverage.
4. Introduce application services and move CLI orchestration.
5. Move web actions onto application services.
6. Split web routing, responses, and rendering.
7. Improve startup and add the repeatable sample UI workflow.
8. Add property tests and end-to-end workflow coverage.
9. Refresh README, architecture notes, roadmap, and maintenance log.
10. Run full verification and leave the sample UI online.

## Revised Roadmap

### Milestone A: Stabilized Local Core

Complete this design. Treat the resulting branch as the new integration baseline before adding product features.

### Milestone B: Tournament Director Essentials

- manual pairing repair and explicit override records
- player withdrawal, late entry, and re-entry
- result correction UI
- configurable scoring and supported tie-break presentation
- audit-log display

### Milestone C: Reports and Real Tournament Trials

- print-friendly pairing, result, and standings pages
- PDF export only after print layouts settle
- realistic tournament fixtures and simulations
- structured feedback from tournament directors

### Milestone D: Pairing Quality

- affiliation avoidance
- clearer float and colour explanations
- unavoidable-repeat handling
- McMahon bar and starting-score policy refinement
- optional weighted matching after regression fixtures define expected behavior

### Milestone E: Distribution

- dependable package installation
- one-command local launch
- backups and recovery guidance
- desktop packaging evaluation

Multi-user networking remains outside this roadmap until local workflows are proven.

## Success Criteria

This stabilization is complete when:

1. equivalent CLI and web operations share one tested implementation
2. malformed tournament state is rejected at the storage boundary
3. pairing and result workflows have meaningful persisted-state tests
4. the web code has clear module boundaries without changing its simple appearance
5. a tournament director can create or load a sample and start the UI with documented commands
6. the server reports a reachable URL and understandable startup failures
7. the full verification suite passes
8. maintenance decisions, known limitations, and the next roadmap are documented
9. all work is saved in coherent commits
