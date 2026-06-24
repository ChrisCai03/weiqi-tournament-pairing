from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import uuid4

from pairing.domain.audit import AuditLogEntry
from pairing.domain.config import TournamentConfig
from pairing.domain.player import Player
from pairing.domain.result import Result
from pairing.domain.round import Round
from pairing.domain.validation import (
    TOURNAMENT_FORMATS,
    TOURNAMENT_STATUSES,
    require_choice,
    require_non_blank,
    require_positive,
    require_unique,
)


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
    rounds: list[Round] = field(default_factory=list)
    manual_overrides: list[dict[str, object]] = field(default_factory=list)
    audit_log: list[AuditLogEntry] = field(default_factory=list)

    @classmethod
    def create(cls, name: str, *, round_count: int = 5, format: str = "swiss") -> "Tournament":
        if round_count <= 0:
            raise ValueError("Round count must be positive.")
        normalized_name = require_non_blank(name, "Tournament name")
        require_choice(format, TOURNAMENT_FORMATS, "tournament format")

        config = TournamentConfig(round_count=round_count, pairing_method=format)
        tournament = cls(
            id=str(uuid4()),
            name=normalized_name,
            game_type="go",
            format=format,
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

    def add_players(self, players: list[Player], *, actor: str = "cli") -> None:
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
                actor=actor,
                details={"count": len(players)},
            )
        )

    def next_round_number(self) -> int:
        return max((round_obj.number for round_obj in self.rounds), default=0) + 1

    def get_round(self, number: int) -> Round:
        for round_obj in self.rounds:
            if round_obj.number == number:
                return round_obj
        raise ValueError(f"Round {number} not found.")

    def get_game(self, round_number: int, board_number: int):
        round_obj = self.get_round(round_number)
        for game in round_obj.games:
            if game.board_number == board_number:
                return game
        raise ValueError(f"Board {board_number} not found in round {round_number}.")

    def record_result(
        self,
        *,
        round_number: int,
        board_number: int,
        winner: str,
        actor: str = "cli",
    ) -> list[Round]:
        game = self.get_game(round_number, board_number)
        if winner not in {"black", "white"}:
            raise ValueError("Winner must be 'black' or 'white'.")
        if game.white_player_id is None or game.result.result_type == "bye":
            raise ValueError("Cannot record a normal result for a bye board.")

        winner_player_id = game.black_player_id if winner == "black" else game.white_player_id
        if winner_player_id is None:
            raise ValueError(
                f"Cannot record {winner} win for round {round_number} board {board_number}."
            )

        game.result = Result.completed(result_type="normal", winner_player_id=winner_player_id)

        round_obj = self.get_round(round_number)
        if all(item.result.status == "completed" for item in round_obj.games):
            round_obj.status = "completed"
            round_obj.completed_at = _utc_now_iso()

        invalidated_rounds = self.mark_rounds_stale_after(round_number)
        self.audit_log.append(
            AuditLogEntry.create(
                "result_entered",
                f"Recorded {winner} win for round {round_number} board {board_number}.",
                actor=actor,
                round_number=round_number,
                details={
                    "board_number": board_number,
                    "winner": winner,
                    "winner_player_id": winner_player_id,
                },
            )
        )
        if invalidated_rounds:
            self.audit_log.append(
                AuditLogEntry.create(
                    "future_rounds_invalidated",
                    f"Marked {len(invalidated_rounds)} later rounds stale after round {round_number}.",
                    actor=actor,
                    round_number=round_number,
                    details={
                        "stale_round_numbers": [round_obj.number for round_obj in invalidated_rounds],
                    },
                )
            )
        return invalidated_rounds

    def mark_rounds_stale_after(self, round_number: int) -> list[Round]:
        stale_rounds = [
            round_obj
            for round_obj in self.rounds
            if round_obj.number > round_number and round_obj.status != "stale"
        ]
        for round_obj in stale_rounds:
            round_obj.status = "stale"
        return stale_rounds

    def purge_stale_rounds(self) -> list[Round]:
        stale_rounds = [round_obj for round_obj in self.rounds if round_obj.status == "stale"]
        if not stale_rounds:
            return []

        self.rounds = [round_obj for round_obj in self.rounds if round_obj.status != "stale"]
        self.audit_log.append(
            AuditLogEntry.create(
                "stale_rounds_purged",
                f"Purged {len(stale_rounds)} stale rounds.",
                details={
                    "purged_round_numbers": [round_obj.number for round_obj in stale_rounds],
                },
            )
        )
        return stale_rounds

    def validate(self) -> None:
        require_non_blank(self.id, "Tournament id")
        self.name = require_non_blank(self.name, "Tournament name")
        require_choice(self.format, TOURNAMENT_FORMATS, "tournament format")
        require_choice(self.status, TOURNAMENT_STATUSES, "tournament status")
        self.config.validate()
        if self.config.pairing_method != self.format:
            raise ValueError("Tournament config pairing method must match tournament format.")

        require_unique((player.id for player in self.players), "player id")
        require_unique((round_obj.number for round_obj in self.rounds), "round number")
        player_ids = {player.id for player in self.players}
        seed_numbers: list[int] = []
        game_ids: list[str] = []

        for player in self.players:
            require_non_blank(player.id, "Player id")
            player.display_name = require_non_blank(player.display_name, "Player name")
            require_positive(player.seed_number, "Player seed number")
            seed_numbers.append(player.seed_number)
        require_unique(seed_numbers, "player seed number")

        for round_obj in self.rounds:
            round_obj.validate()
            game_ids.extend(game.id for game in round_obj.games)
            appearances: set[str] = set()
            for game in round_obj.games:
                game_players = [
                    player_id
                    for player_id in (game.black_player_id, game.white_player_id)
                    if player_id is not None
                ]
                for player_id in game_players:
                    if player_id not in player_ids:
                        raise ValueError(
                            f"Round {round_obj.number} board {game.board_number} "
                            f"references unknown player {player_id}."
                        )
                    if player_id in appearances:
                        raise ValueError(
                            f"Player {player_id} appears more than once in round "
                            f"{round_obj.number}."
                        )
                    appearances.add(player_id)

                if game.result.result_type == "bye":
                    if len(game_players) != 1:
                        raise ValueError("A bye must contain exactly one player.")
                    if game.result.winner_player_id != game_players[0]:
                        raise ValueError("Bye winner must be the player receiving the bye.")
                else:
                    if len(game_players) != 2 or game_players[0] == game_players[1]:
                        raise ValueError("A normal game must contain two distinct players.")
                    winner = game.result.winner_player_id
                    if winner is not None and winner not in game_players:
                        raise ValueError("Result winner must be one of the game players.")

        require_unique(game_ids, "game id")

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
            "rounds": [round_obj.to_dict() for round_obj in self.rounds],
            "manual_overrides": self.manual_overrides,
            "audit_log": [entry.to_dict() for entry in self.audit_log],
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "Tournament":
        tournament_data = dict(data["tournament"])  # type: ignore[arg-type]
        tournament = cls(
            id=str(tournament_data["id"]),
            name=str(tournament_data["name"]),
            game_type=str(tournament_data.get("game_type", "go")),
            format=str(tournament_data.get("format", "swiss")),
            status=str(tournament_data.get("status", "draft")),
            schema_version=int(data.get("schema_version", SCHEMA_VERSION)),
            config=TournamentConfig.from_dict(dict(data.get("config", {}))),
            players=[Player.from_dict(dict(player)) for player in data.get("players", [])],  # type: ignore[arg-type]
            teams=[dict(team) for team in data.get("teams", [])],  # type: ignore[arg-type]
            rounds=[Round.from_dict(dict(round_data)) for round_data in data.get("rounds", [])],  # type: ignore[arg-type]
            manual_overrides=[dict(item) for item in data.get("manual_overrides", [])],  # type: ignore[arg-type]
            audit_log=[AuditLogEntry.from_dict(dict(entry)) for entry in data.get("audit_log", [])],  # type: ignore[arg-type]
        )
        tournament.validate()
        return tournament


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
