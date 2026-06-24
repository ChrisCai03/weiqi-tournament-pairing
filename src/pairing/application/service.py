from __future__ import annotations

from pathlib import Path

from pairing.application.results import (
    CreateOutcome,
    ImportOutcome,
    ResultOutcome,
    RoundOutcome,
)
from pairing.domain.audit import AuditLogEntry
from pairing.domain.tournament import Tournament
from pairing.engine.mcmahon import mcmahon_starting_score
from pairing.engine.round_generation import generate_next_round
from pairing.engine.standings import StandingEntry, calculate_standings
from pairing.import_export.csv_export import (
    pairings_to_csv,
    players_to_csv,
    results_to_csv,
    standings_to_csv,
)
from pairing.import_export.csv_import import (
    import_players_from_csv,
    import_players_from_csv_text,
)
from pairing.storage import load_tournament, save_tournament


class TournamentService:
    def __init__(self, tournament_path: str | Path) -> None:
        self.path = Path(tournament_path)

    @classmethod
    def create(
        cls,
        tournament_path: str | Path,
        *,
        name: str,
        round_count: int = 5,
        format: str = "swiss",
        actor: str = "cli",
    ) -> CreateOutcome:
        path = Path(tournament_path)
        tournament = Tournament.create(name, round_count=round_count, format=format)
        tournament.audit_log[-1].actor = actor
        save_tournament(tournament, path)
        return CreateOutcome(path=path)

    def import_players_file(
        self,
        csv_path: str | Path,
        *,
        actor: str = "cli",
    ) -> ImportOutcome:
        tournament = load_tournament(self.path)
        report = import_players_from_csv(csv_path)
        return self._apply_player_import(report, tournament=tournament, actor=actor)

    def import_players_text(
        self,
        csv_text: str,
        *,
        actor: str = "cli",
    ) -> ImportOutcome:
        tournament = load_tournament(self.path)
        report = import_players_from_csv_text(csv_text)
        return self._apply_player_import(report, tournament=tournament, actor=actor)

    def generate_next_round(self, *, actor: str = "cli") -> RoundOutcome:
        tournament = load_tournament(self.path)
        round_obj = generate_next_round(tournament)
        tournament.rounds.append(round_obj)
        tournament.audit_log.append(
            AuditLogEntry.create(
                "round_pairings_generated",
                (
                    f"Generated {round_obj.pairing_method} pairings for round "
                    f"{round_obj.number}."
                ),
                actor=actor,
                round_number=round_obj.number,
                details={
                    "format": round_obj.pairing_method,
                    "game_count": len(round_obj.games),
                    "warnings": [
                        item
                        for item in round_obj.explanation_summary
                        if item.startswith("Warning:")
                    ],
                },
            )
        )
        save_tournament(tournament, self.path)
        return RoundOutcome(
            round_number=round_obj.number,
            game_count=len(round_obj.games),
            warnings=tuple(
                item
                for item in round_obj.explanation_summary
                if item.startswith("Warning:")
            ),
        )

    def record_result(
        self,
        *,
        round_number: int,
        board_number: int,
        winner: str,
        actor: str = "cli",
    ) -> ResultOutcome:
        tournament = load_tournament(self.path)
        invalidated_rounds = tournament.record_result(
            round_number=round_number,
            board_number=board_number,
            winner=winner,
            actor=actor,
        )
        save_tournament(tournament, self.path)
        return ResultOutcome(
            round_number=round_number,
            board_number=board_number,
            corrected=False,
            invalidated_rounds=tuple(item.number for item in invalidated_rounds),
        )

    def regenerate_from(
        self,
        boundary_round: int,
        *,
        actor: str = "cli",
    ) -> RoundOutcome | None:
        tournament = load_tournament(self.path)
        removed_rounds = tournament.mark_rounds_stale_after(boundary_round)
        stale_rounds = tournament.purge_stale_rounds()
        if boundary_round >= tournament.config.round_count:
            save_tournament(tournament, self.path)
            return None

        round_obj = generate_next_round(tournament)
        tournament.rounds.append(round_obj)
        tournament.audit_log.append(
            AuditLogEntry.create(
                "rounds_regenerated",
                f"Regenerated round {round_obj.number} from boundary {boundary_round}.",
                actor=actor,
                round_number=round_obj.number,
                details={
                    "boundary_round": boundary_round,
                    "removed_round_numbers": [
                        item.number for item in (removed_rounds or stale_rounds)
                    ],
                },
            )
        )
        save_tournament(tournament, self.path)
        return RoundOutcome(
            round_number=round_obj.number,
            game_count=len(round_obj.games),
        )

    def standings(self) -> list[StandingEntry]:
        tournament = load_tournament(self.path)
        if tournament.format == "mcmahon":
            return calculate_standings(
                tournament,
                starting_score_provider=lambda player: mcmahon_starting_score(
                    player,
                    tournament,
                ),
            )
        return calculate_standings(tournament)

    def export_csv(self, report: str) -> str:
        tournament = load_tournament(self.path)
        exporters = {
            "players": players_to_csv,
            "pairings": pairings_to_csv,
            "results": results_to_csv,
            "standings": standings_to_csv,
        }
        try:
            exporter = exporters[report]
        except KeyError as exc:
            raise ValueError(f"Unknown CSV report: {report}.") from exc
        return exporter(tournament)

    def load(self) -> Tournament:
        return load_tournament(self.path)

    def _apply_player_import(
        self,
        report,
        *,
        tournament: Tournament,
        actor: str,
    ) -> ImportOutcome:
        if not report.valid:
            raise ValueError("\n".join(report.errors))
        tournament.add_players(report.players, actor=actor)
        save_tournament(tournament, self.path)
        return ImportOutcome(
            imported_count=len(report.players),
            warnings=tuple(report.warnings),
        )
