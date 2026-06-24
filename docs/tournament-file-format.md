# Tournament File Format

Stage 1 stores tournaments as a single JSON file with the extension `.tgo.json`.

## Schema Version

Stage 1 uses `schema_version: 1`.

## Top-Level Shape

```json
{
  "schema_version": 1,
  "tournament": {
    "id": "uuid",
    "name": "Example Weiqi Open",
    "game_type": "go",
    "format": "swiss",
    "status": "draft"
  },
  "config": {
    "round_count": 5,
    "pairing_method": "swiss",
    "score_win": 1.0,
    "score_loss": 0.0,
    "score_draw": 0.5,
    "score_bye": 1.0,
    "allow_draws": false,
    "rank_system": "dan_kyu",
    "colour_policy": "balanced",
    "bye_policy": "lowest_score_no_previous_bye",
    "handicap_policy": "none",
    "affiliation_policy": "avoid_when_possible",
    "tiebreak_order": ["score", "wins", "sos", "sosos"],
    "random_seed": 1
  },
  "players": [],
  "teams": [],
  "rounds": [],
  "manual_overrides": [],
  "audit_log": [
    {
      "id": "uuid",
      "timestamp": "2026-06-23T10:00:00+00:00",
      "event_type": "tournament_created",
      "actor": "cli",
      "summary": "Created tournament 'Example Weiqi Open' with 5 rounds.",
      "round_number": null,
      "details": {},
      "state_hash_before": null,
      "state_hash_after": null
    }
  ]
}
```

## Notes

- Files are saved atomically through a temporary file and replace step.
- The complete tournament aggregate is validated before save and after load.
- Files are meant to be inspectable in a text editor and friendly to version control.
- Manual editing is possible, but CLI commands should be preferred when available.
- Unknown schema versions are rejected at load time.
- Invalid or incomplete file structures are rejected at load time.

## Supported Values

- Tournament format and config pairing method: `swiss`, `mcmahon`
- Tournament status: `draft`, `active`, `completed`
- Player status: `active`, `withdrawn`
- Round status: `draft`, `published`, `completed`, `stale`
- Result status: `pending`, `completed`
- Result type: `pending`, `normal`, `bye`
- Rank system: `dan_kyu`
- Colour policy: `balanced`
- Bye policy: `lowest_score_no_previous_bye`
- Handicap policy: `none`
- Affiliation policy: `avoid_when_possible`
- Tie-break values: `score`, `wins`, `sos`, `sosos`

Draws, forfeits, voids, no-shows, manual overrides, handicap pairing, and
affiliation-aware pairing are reserved for later designs. Their presence in
older design documents does not mean they are active schema-version-1
workflows.

## Player Shape

Each player contains:

```json
{
  "id": "uuid",
  "display_name": "Alice",
  "rank": "3d",
  "rank_sort_value": 3,
  "country": "SG",
  "club": "Example Club",
  "school": "",
  "team_id": "",
  "status": "active",
  "seed_number": 1,
  "notes": ""
}
```

Player IDs and positive seed numbers must be unique.

## Round, Game, and Result Shapes

```json
{
  "number": 1,
  "status": "draft",
  "generated_at": "2026-06-24T08:00:00+00:00",
  "completed_at": null,
  "pairing_method": "swiss",
  "pairing_seed": 1,
  "is_regenerated": false,
  "supersedes_round_version": null,
  "explanation_summary": ["Round 1 Swiss pairing generated."],
  "games": [
    {
      "id": "uuid",
      "round_number": 1,
      "board_number": 1,
      "black_player_id": "player-uuid",
      "white_player_id": "opponent-uuid",
      "handicap": 0,
      "komi": 0.0,
      "override_origin": "engine",
      "pairing_explanation": ["Opening pairing."],
      "result": {
        "status": "pending",
        "result_type": "pending",
        "winner_player_id": null,
        "entered_at": null,
        "entered_by": "cli",
        "notes": "",
        "correction_of": null
      }
    }
  ]
}
```

Round numbers, game IDs, and board numbers must be unique in their scopes.
Every referenced player must exist, and a player may appear at most once in a
round. A bye game contains exactly one player and a completed `bye` result
naming that player.

## Audit Log

Each tournament file contains an `audit_log` list. In Stage 1 this records:

- tournament creation
- player import events

Later stages can extend the same log for pairings, result entry, corrections, and manual overrides.
