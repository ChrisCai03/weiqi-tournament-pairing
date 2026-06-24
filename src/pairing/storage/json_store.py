from __future__ import annotations

import json
import os
from pathlib import Path

from pairing.domain.tournament import SCHEMA_VERSION, Tournament


class TournamentStoreError(RuntimeError):
    """Raised when a tournament file cannot be loaded or saved."""


def save_tournament(tournament: Tournament, path: str | Path) -> None:
    tournament.validate()
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    temp_path = target.with_name(f".{target.name}.tmp")
    payload = json.dumps(tournament.to_dict(), indent=2, sort_keys=True)
    try:
        with temp_path.open("w", encoding="utf-8", newline="\n") as file:
            file.write(payload + "\n")
            file.flush()
            os.fsync(file.fileno())
        os.replace(temp_path, target)
    finally:
        if temp_path.exists():
            temp_path.unlink()


def load_tournament(path: str | Path) -> Tournament:
    source = Path(path)
    if not source.exists():
        raise TournamentStoreError(f"Tournament file not found: {source}")

    try:
        data = json.loads(source.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise TournamentStoreError(f"Invalid tournament JSON: {source}") from exc

    try:
        schema_version = int(data.get("schema_version", 0))
        if schema_version != SCHEMA_VERSION:
            raise TournamentStoreError(f"Unsupported schema version: {schema_version}")

        return Tournament.from_dict(data)
    except TournamentStoreError:
        raise
    except (AttributeError, KeyError, TypeError, ValueError) as exc:
        raise TournamentStoreError(f"Invalid tournament file structure: {source}") from exc
