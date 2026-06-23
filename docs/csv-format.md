# CSV Player Import Format

The Stage 1 player import command accepts UTF-8 CSV files with a header row.

## Columns

Required:

- `name`

Optional:

- `rank`
- `country`
- `club`
- `school`
- `team`
- `notes`

Unknown columns are ignored with a warning.
Blank column headers are ignored with a warning.
Duplicate recognized column headers are rejected as errors.

## Rank Values

Accepted rank examples:

- `7d`
- `1d`
- `1 dan`
- `1k`
- `5k`
- `5 kyu`
- `unranked`
- blank rank cells

Dan ranks must be `1d` through `9d`.
Kyu ranks must be `1k` through `30k`.
Blank or `unranked` values are stored as `unranked`.

## Validation Behavior

- Missing player names are rejected as errors.
- Invalid rank values are rejected as errors.
- Duplicate player names are allowed, but reported as warnings.
- If any row-level errors are found, no players are imported from that file.
