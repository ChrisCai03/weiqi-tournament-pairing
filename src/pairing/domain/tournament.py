from __future__ import annotations

from dataclasses import dataclass, field
from uuid import uuid4

from pairing.domain.audit import AuditLogEntry
from pairing.domain.config import TournamentConfig
from pairing.domain.player import Player


SCHEMA_VERSION = 1


@dataclass(slots=True)
class Tournament:
    id: str
    name: str
    game_type: str
    format: str
    status: str
    schema_version: int
    config: TournamentConfig
    players: list[Player] = field(default_factory=list)
    teams: list[dict[str, object]] = field(default_factory=list)
    rounds: list[dict[str, object]] = field(default_factory=list)
    manual_overrides: list[dict[str, object]] = field(default_factory=list)
    audit_log: list[AuditLogEntry] = field(default_factory=list)

    @classmethod
    def create(cls, name: str, *, round_count: int = 5) -> "Tournament":
        if round_count <= 0:
            raise ValueError("Round count must be positive.")

        config = TournamentConfig(round_count=round_count)
        tournament = cls(
            id=str(uuid4()),
            name=name.strip(),
            game_type="go",
            format="swiss",
            status="draft",
            schema_version=SCHEMA_VERSION,
            config=config,
        )
        tournament.audit_log.append(
            AuditLogEntry.create(
                "tournament_created",
                f"Created tournament '{tournament.name}' with {round_count} rounds.",
            )
        )
        return tournament

    def add_players(self, players: list[Player]) -> None:
        next_seed = max((player.seed_number for player in self.players), default=0)
        for player in players:
            if player.seed_number == 0:
                next_seed += 1
                player.seed_number = next_seed
            else:
                next_seed = max(next_seed, player.seed_number)
            self.players.append(player)
        self.audit_log.append(
            AuditLogEntry.create(
                "players_imported",
                f"Imported {len(players)} players.",
                details={"count": len(players)},
            )
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "tournament": {
                "id": self.id,
                "name": self.name,
                "game_type": self.game_type,
                "format": self.format,
                "status": self.status,
            },
            "config": self.config.to_dict(),
            "players": [player.to_dict() for player in self.players],
            "teams": self.teams,
            "rounds": self.rounds,
            "manual_overrides": self.manual_overrides,
            "audit_log": [entry.to_dict() for entry in self.audit_log],
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "Tournament":
        tournament_data = dict(data["tournament"])  # type: ignore[arg-type]
        return cls(
            id=str(tournament_data["id"]),
            name=str(tournament_data["name"]),
            game_type=str(tournament_data.get("game_type", "go")),
            format=str(tournament_data.get("format", "swiss")),
            status=str(tournament_data.get("status", "draft")),
            schema_version=int(data.get("schema_version", SCHEMA_VERSION)),
            config=TournamentConfig.from_dict(dict(data.get("config", {}))),
            players=[Player.from_dict(dict(player)) for player in data.get("players", [])],  # type: ignore[arg-type]
            teams=[dict(team) for team in data.get("teams", [])],  # type: ignore[arg-type]
            rounds=[dict(round_data) for round_data in data.get("rounds", [])],  # type: ignore[arg-type]
            manual_overrides=[dict(item) for item in data.get("manual_overrides", [])],  # type: ignore[arg-type]
            audit_log=[AuditLogEntry.from_dict(dict(entry)) for entry in data.get("audit_log", [])],  # type: ignore[arg-type]
        )
