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
- Files are meant to be inspectable in a text editor and friendly to version control.
- Manual editing is possible, but CLI commands should be preferred when available.
- Unknown schema versions are rejected at load time.
- Invalid or incomplete file structures are rejected at load time.

## Audit Log

Each tournament file contains an `audit_log` list. In Stage 1 this records:

- tournament creation
- player import events

Later stages can extend the same log for pairings, result entry, corrections, and manual overrides.
