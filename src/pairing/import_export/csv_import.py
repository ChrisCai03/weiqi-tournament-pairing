from __future__ import annotations

import csv
from dataclasses import dataclass, field
from io import StringIO
from pathlib import Path

from pairing.domain.player import Player, RankParseError


EXPECTED_COLUMNS = {"name", "rank", "country", "club", "school", "team", "notes"}


@dataclass(slots=True)
class PlayerImportReport:
    players: list[Player] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def valid(self) -> bool:
        return not self.errors


def import_players_from_csv(path: str | Path) -> PlayerImportReport:
    return import_players_from_csv_text(Path(path).read_text(encoding="utf-8-sig"))


def import_players_from_csv_text(csv_text: str) -> PlayerImportReport:
    report = PlayerImportReport()
    reader = csv.DictReader(StringIO(csv_text))

    if reader.fieldnames is None:
        report.errors.append("CSV is missing a header row.")
        return report

    normalized_fields = [field.strip().lower() for field in reader.fieldnames]
    unknown_columns = sorted(set(normalized_fields) - EXPECTED_COLUMNS)
    if unknown_columns:
        report.warnings.append(f"Unknown columns ignored: {', '.join(unknown_columns)}.")

    seen_names: set[str] = set()
    pending_players: list[Player] = []

    for row_number, row in enumerate(reader, start=2):
        normalized_row = {
            (key.strip().lower() if key is not None else ""): (value or "").strip()
            for key, value in row.items()
        }
        name = normalized_row.get("name", "")
        if not name:
            report.errors.append(f"Row {row_number}: missing player name.")
            continue

        if name.lower() in seen_names:
            report.warnings.append(f"Duplicate player name imported: {name}.")
        seen_names.add(name.lower())

        try:
            pending_players.append(
                Player.create(
                    name,
                    rank=normalized_row.get("rank", ""),
                    country=normalized_row.get("country", ""),
                    club=normalized_row.get("club", ""),
                    school=normalized_row.get("school", ""),
                    team_id=normalized_row.get("team", ""),
                    notes=normalized_row.get("notes", ""),
                )
            )
        except RankParseError as exc:
            report.errors.append(f"Row {row_number}: {exc}")

    if report.errors:
        report.players = []
    else:
        report.players = pending_players
    return report
