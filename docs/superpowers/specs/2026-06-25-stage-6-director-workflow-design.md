# Stage 6 Tournament Director Workflow Design

## Goal

Build an operationally complete single-director tournament workflow inspired
by OpenGotha while retaining the Python application's stronger validation,
audit, persistence, and dependency boundaries.

Stage 6 Release 1 covers:

1. per-round participation, withdrawal, re-entry, absence, and late entry;
2. configurable rich results, including both-win and both-loss;
3. a round operations dashboard and quick-check workflow;
4. audited manual pairing repair;
5. audit-log display and recoverable tournament snapshots.

## Design Principles

- One local tournament director and one managing process remain the supported
  operating model.
- OpenGotha supplies product lessons and default policies, not implementation
  structure.
- Every non-default policy is persisted, visible, and auditable.
- UI and CLI call application services; they never mutate the aggregate
  directly.
- Existing valid schema-version-1 files continue to load with default values.
- All destructive or corrective operations retain before-state evidence.
- Unsupported features remain explicit rather than partially active.

## Scope Boundaries

This release does not implement:

- weighted matching;
- affiliation-aware or DU/DD-aware pairing;
- handicap pairing;
- expanded McMahon bands;
- SODOS or direct-confrontation tie-breaks;
- team tournaments;
- round-robin, knockout, or friendly-match formats;
- multi-user or remote operation;
- native PDF generation.

Those are later Stage 6 slices and require separate specifications.

## OpenGotha Ideas Adopted

The release selectively adopts:

- per-round participation independent of player registration;
- a quick-check surface separate from full player editing;
- visible counts for eligible, paired, bye, pending-result, and completed
  players;
- first-class pairing repair actions close to the pairing screen;
- configured tournament-system defaults;
- explicit save-copy and pre-repair recovery snapshots.

It deliberately rejects:

- implicit round state;
- UI-controlled mutation;
- silent repair;
- weak game-insertion validation;
- mutable god objects;
- hidden scoring or pairing weights.

## Domain Model

### Participation

Add a persisted `ParticipationRecord`:

```text
player_id
round_number
status
score_adjustment
reason
updated_at
updated_by
```

Supported statuses:

- `participating`
- `withdrawn`
- `absent`
- `not_entered`

Rules:

- Existing schema-v1 players without records are `participating` while their
  player status is active.
- A withdrawal applies from an effective round through the configured final
  round.
- Re-entry changes the effective round and later rounds back to
  `participating`.
- A one-round absence affects only the selected round.
- A late entrant receives `not_entered` records for completed and currently
  paired earlier rounds, then participates from the selected effective round.
- Missed rounds use `late_entry_missed_round_score`, default `0.0`.
- Directors may override an individual missed-round adjustment with a reason.
- Participation cannot be changed for a player whose completed game would be
  contradicted. The director must correct or regenerate the round first.

Participation is separate from registration identity. `Player.status` remains
the broad active/withdrawn compatibility field, while round records are the
authoritative eligibility source.

### Configurable Scoring Policy

Extend `TournamentConfig` with:

```text
score_both_win = 1.0
score_both_loss = 0.0
score_forfeit_win = 1.0
score_forfeit_loss = 0.0
score_no_show = 0.0
late_entry_missed_round_score = 0.0
count_both_win_as_played = true
count_both_loss_as_played = true
count_void_as_played = false
automatic_backup_before_destructive_change = true
backup_retention_count = 10
```

These defaults follow the approved policy and OpenGotha's general approach of
configurable tournament scoring. Configuration changes are audited and are
restricted after completed results exist unless the director explicitly
accepts standings recalculation.

### Result Outcomes

Replace winner-only scoring assumptions with explicit outcome semantics.

Supported completed result types:

- `normal`: one player wins and one loses;
- `draw`: both receive `score_draw`;
- `both_win`: both receive `score_both_win`;
- `both_loss`: both receive `score_both_loss`;
- `forfeit`: winner and loser use configured forfeit scores;
- `no_show`: the absent side receives `score_no_show`; if only one player is
  absent, the present side receives `score_forfeit_win`; if both are absent,
  both receive `score_no_show`;
- `bye`: the recipient receives `score_bye`;
- `void`: neither receives game points.

`Result` gains:

```text
black_score
white_score
outcome_code
```

The score pair is persisted when the result is entered. This protects
historical meaning if scoring configuration changes later.

Supported `outcome_code` values are:

- `black_win`
- `white_win`
- `draw`
- `both_win`
- `both_loss`
- `black_forfeit`
- `white_forfeit`
- `black_no_show`
- `white_no_show`
- `both_no_show`
- `bye`
- `void`

The outcome code determines result type, winner where applicable, win/loss/draw
counters, and the configured score pair. Arbitrary score pairs are not entered
directly; unusual tournament policies are expressed through configuration.

History and tie-break policy:

- `normal`, `draw`, `both_win`, `both_loss`, `forfeit`, and `no_show` count as
  played encounters;
- `both_win` and `both_loss` contribute the opponent to SOS exactly like a
  normal played game;
- `void` does not count for repeat avoidance, colour history, SOS, or game
  score;
- both-win increments the wins count for both players;
- both-loss increments the losses count for both players;
- draw increments a new draws count;
- a one-player forfeit or no-show increments one win and one loss;
- a both-no-show result increments a loss for both players;
- counters follow outcome semantics, not numerical score comparisons.

Result correction retains the complete previous score pair and outcome.

### Round Operations Status

Add a derived `RoundOperationsStatus` returned by the application layer:

```text
round_number
eligible_count
not_participating_count
paired_count
bye_count
unpaired_eligible_count
pending_result_count
completed_result_count
warning_messages
can_generate
can_repair
can_close
```

This is not persisted. It is derived from participation, round, game, and
result state so CLI and web display the same truth.

### Manual Override Record

Replace the dormant dictionary contract with a typed
`ManualOverrideRecord`:

```text
id
timestamp
round_number
operation
before_games
after_games
warnings
director_note
actor
backup_id
```

Supported initial operations:

- swap opponents between two pending boards;
- exchange colours on a pending game;
- move a pending game to another board number;
- assign or replace a bye among eligible unpaired players;
- regenerate only the still-pending portion of the current round.

Repairs may not alter a completed game. If results already exist, only pending
games may be changed, and completed players are excluded from repair.

Validation classes:

- hard violations: duplicate player in a round, unknown player, ineligible
  player, completed game mutation, duplicate board number, invalid bye;
- warnings: repeat opponent, avoidable score gap, colour imbalance,
  affiliation conflict, second bye.

Hard violations are rejected. Warnings require a non-blank director note and
explicit acceptance. The accepted repair, warning set, and before/after games
are persisted and audited.

## Application Services

Add focused services rather than enlarging `TournamentService` indefinitely:

```text
ParticipationService
ResultService
RoundOperationsService
PairingRepairService
BackupService
```

`TournamentService` remains the entry facade and delegates to these focused
services. Each mutating workflow follows:

1. load;
2. validate command and current state;
3. create a recovery snapshot when configured;
4. mutate;
5. append audit and override records;
6. validate the complete aggregate;
7. atomically save;
8. return a typed outcome.

### Participation Commands

- `set_round_participation`
- `withdraw_player`
- `reenter_player`
- `add_late_player`
- `set_missed_round_adjustment`

### Result Commands

- `record_outcome`
- `correct_outcome`

Existing `record_result` and `correct_result` remain compatibility wrappers for
black/white normal wins.

### Repair Commands

- `swap_pending_opponents`
- `exchange_pending_colours`
- `move_pending_game`
- `replace_round_bye`
- `regenerate_pending_pairings`

## Backup and Recovery

Backups are sibling JSON snapshots, not another canonical store.

Default location:

```text
<tournament filename>.backups/
```

Filename contains UTC timestamp, audit operation, and source-state hash.

Automatic snapshots occur before:

- result correction that invalidates later rounds;
- regeneration;
- accepted manual repair;
- participation changes affecting an existing draft round;
- scoring-policy changes after any round exists.

The service retains the newest ten backups by default. Retention cleanup never
deletes the canonical file. CLI and web expose:

- create snapshot;
- list snapshots;
- restore snapshot to a new file;
- never overwrite the active tournament during restore.

This improves on OpenGotha's single rolling work file by preserving a small,
auditable recovery chain.

## CLI Workflow

Add:

```text
pairing quick-check <file> --round N
pairing withdraw <file> --player ID --from-round N --reason TEXT
pairing reenter <file> --player ID --from-round N --reason TEXT
pairing late-entry <file> --name ... --rank ... --from-round N
pairing set-participation <file> --player ID --round N --status ...
pairing enter-outcome <file> --round N --board N --outcome ...
pairing correct-outcome <file> --round N --board N --outcome ...
pairing repair-pairing <operation-specific arguments>
pairing audit <file>
pairing backup create|list|restore ...
```

Player IDs are accepted as stable identifiers. UI surfaces may display names,
but commands do not rely on ambiguous names.

## Web Workflow

### Operations Dashboard

The overview becomes a round operations dashboard:

- one row per configured round;
- participation, pairing, result, and warning counts;
- current round emphasized;
- blocked next action explained;
- links to quick check, pairings, results, and audit evidence.

### Quick Check

Add a compact table optimized for floor operations:

- player, rank, club/school;
- broad player status;
- per-round participation status;
- missed-round adjustment;
- current pairing/result state;
- batch withdrawal, re-entry, and absence controls.

The full Players page remains the detailed identity editor.

### Results

Each board exposes explicit outcome buttons:

- Black win
- White win
- Draw
- Both win
- Both lose
- Forfeit
- No-show
- Void

The confirmation view shows the score pair before submission. Correction uses
the same controls and clearly labels downstream invalidation.

### Pairing Repair

The pairings page exposes repair actions only for pending games. A preview
shows:

- proposed games;
- hard errors;
- warnings;
- affected players;
- required note;
- backup creation.

No repair is persisted from the preview request.

### Audit and Recovery

Add an Audit page with filters by round, event type, actor, and player. Show
manual overrides with before/after summaries and links to available backups.

## Persistence and Compatibility

Schema version remains `1` because all new fields are optional additions.

Compatibility defaults:

- missing participation records imply active participation;
- missing rich score fields are derived from the old result type and winner;
- existing `manual_overrides` dictionaries remain loadable as operation
  `legacy`, preserving their original dictionary in `before_games` and using
  empty defaults for fields that did not previously exist;
- missing new configuration fields receive the defaults in this specification.

Saving a loaded legacy tournament writes the normalized optional fields. No
separate migration command is required.

## Error Handling

- Invalid commands return domain-specific errors with the violated rule.
- Web mutations use POST and redirect after success.
- Failed validation leaves the tournament and backups unchanged.
- Backup failure blocks destructive mutation.
- A repair preview cannot be reused after the tournament state hash changes.
- Restore always creates a new destination file and validates it before
  reporting success.

## Testing Strategy

### Unit Tests

- participation defaults and effective-round transitions;
- late-entry score adjustments;
- every result outcome and score pair;
- both-win/both-loss history and SOS behavior;
- void exclusion;
- round operations status derivation;
- repair validation and warning generation;
- backup naming, retention, validation, and safe restore.

### Property Tests

- ineligible players are never generated into pairings;
- each eligible player appears exactly once or receives one bye;
- repairs never duplicate a player or board;
- result scoring is the persisted black/white score pair;
- special played outcomes contribute one opponent encounter;
- void outcomes contribute none.

### Integration Tests

- withdraw, pair, re-enter, and complete a multi-round tournament;
- late entry after completed rounds with default and overridden adjustment;
- enter and correct every result type;
- repair pending boards after partial result entry;
- audit and backup evidence survives reload;
- legacy schema-v1 fixtures load and normalize;
- CLI and web produce the same state transitions.

### Realistic Trial

Extend the 32-player trial with:

- one late entrant;
- one withdrawal and re-entry;
- one absence;
- both-win and both-loss results;
- one accepted pairing repair;
- correction, regeneration, and backup restore verification.

## Delivery Slices

### Slice 6A: Participation and Rich Results

- participation model and services;
- late-entry scoring;
- explicit outcome scoring;
- standings, history, CSV, CLI, and compatibility updates.

### Slice 6B: Operations Dashboard

- round status projection;
- quick-check CLI and web UI;
- withdrawal, re-entry, absence, and late-entry controls;
- audit page.

### Slice 6C: Pairing Repair

- typed override records;
- repair preview and validation;
- pending-game repair operations;
- CLI and web controls.

### Slice 6D: Recovery and Field Trial

- automatic and explicit backups;
- safe restore-to-new-file;
- realistic Stage 6 trial;
- runbook and roadmap update.

Each slice must pass its focused tests, full quality gates, specification
review, and code-quality review before the next slice begins.

## Success Criteria

1. Existing schema-v1 tournaments still load and behave as before.
2. Participation is explicit per round and controls pairing eligibility.
3. Late entrants receive zero missed-round points by default, with auditable
   overrides.
4. Both-win and both-loss are supported, configurable, and count as played
   encounters for repeat history and SOS.
5. Result score pairs are persisted and corrections retain prior values.
6. The dashboard reports truthful round readiness and blockers.
7. Manual repairs cannot violate aggregate invariants.
8. Accepted warning-level repairs require a note and retain before/after
   evidence.
9. Destructive workflows create validated recovery snapshots.
10. CLI and web use the same services for all new behavior.
11. The 32-player Stage 6 trial completes deterministically.
12. Ruff, mypy, compilation, tests, and at least 90% production coverage pass.
