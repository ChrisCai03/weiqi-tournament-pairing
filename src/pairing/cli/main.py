from __future__ import annotations

import argparse
import sys
from pathlib import Path

from pairing.domain.tournament import Tournament
from pairing.engine.swiss import generate_next_round
from pairing.import_export.csv_import import import_players_from_csv
from pairing.storage import TournamentStoreError, load_tournament, save_tournament


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="pairing")
    subparsers = parser.add_subparsers(dest="command", required=True)

    create_parser = subparsers.add_parser("create", help="Create a tournament file.")
    create_parser.add_argument("path", help="Output .tgo.json path.")
    create_parser.add_argument("--name", required=True, help="Tournament name.")
    create_parser.add_argument("--rounds", type=int, default=5, help="Number of rounds.")

    import_parser = subparsers.add_parser("import-players", help="Import players from CSV.")
    import_parser.add_argument("tournament_path", help="Existing .tgo.json tournament file.")
    import_parser.add_argument("csv_path", help="Player CSV file.")

    pair_round_parser = subparsers.add_parser("pair-round", help="Generate and append the next round.")
    pair_round_parser.add_argument("tournament_path", help="Existing .tgo.json tournament file.")

    enter_result_parser = subparsers.add_parser("enter-result", help="Record a game result.")
    enter_result_parser.add_argument("tournament_path", help="Existing .tgo.json tournament file.")
    enter_result_parser.add_argument("--round", dest="round_number", required=True, type=int, help="Round number.")
    enter_result_parser.add_argument("--board", dest="board_number", required=True, type=int, help="Board number.")
    enter_result_parser.add_argument(
        "--winner",
        required=True,
        choices=("black", "white"),
        help="Winning colour.",
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        if args.command == "create":
            tournament = Tournament.create(args.name, round_count=args.rounds)
            save_tournament(tournament, Path(args.path))
            print(f"Created tournament: {args.path}")
            return 0

        if args.command == "import-players":
            tournament = load_tournament(Path(args.tournament_path))
            report = import_players_from_csv(Path(args.csv_path))
            for warning in report.warnings:
                print(f"Warning: {warning}", file=sys.stderr)
            if not report.valid:
                for error in report.errors:
                    print(f"Error: {error}", file=sys.stderr)
                return 1
            tournament.add_players(report.players)
            save_tournament(tournament, Path(args.tournament_path))
            print(f"Imported {len(report.players)} players.")
            return 0

        if args.command == "pair-round":
            tournament = load_tournament(Path(args.tournament_path))
            round_obj = generate_next_round(tournament)
            tournament.rounds.append(round_obj)
            save_tournament(tournament, Path(args.tournament_path))
            print(f"Paired round {round_obj.number} with {len(round_obj.games)} games.")
            return 0

        if args.command == "enter-result":
            tournament = load_tournament(Path(args.tournament_path))
            tournament.record_result(
                round_number=args.round_number,
                board_number=args.board_number,
                winner=args.winner,
            )
            save_tournament(tournament, Path(args.tournament_path))
            print(
                f"Recorded {args.winner} win for round {args.round_number} board {args.board_number}."
            )
            return 0
    except (TournamentStoreError, OSError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    parser.error(f"Unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
