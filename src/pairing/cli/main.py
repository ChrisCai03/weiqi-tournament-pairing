from __future__ import annotations

import argparse
import sys
from pathlib import Path

from pairing.application import TournamentService
from pairing.storage import TournamentStoreError
from pairing.web.server import serve_tournament


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="pairing")
    subparsers = parser.add_subparsers(dest="command", required=True)

    create_parser = subparsers.add_parser("create", help="Create a tournament file.")
    create_parser.add_argument("path", help="Output .tgo.json path.")
    create_parser.add_argument("--name", required=True, help="Tournament name.")
    create_parser.add_argument("--rounds", type=int, default=5, help="Number of rounds.")
    create_parser.add_argument("--format", default="swiss", choices=("swiss", "mcmahon"), help="Tournament format.")

    demo_parser = subparsers.add_parser("demo", help="Create a sample tournament file.")
    demo_parser.add_argument("path", help="Output .tgo.json path.")

    import_parser = subparsers.add_parser("import-players", help="Import players from CSV.")
    import_parser.add_argument("tournament_path", help="Existing .tgo.json tournament file.")
    import_parser.add_argument("csv_path", help="Player CSV file.")

    pair_round_parser = subparsers.add_parser("pair-round", help="Generate and append the next round.")
    pair_round_parser.add_argument("tournament_path", help="Existing .tgo.json tournament file.")

    standings_parser = subparsers.add_parser("standings", help="Print current standings.")
    standings_parser.add_argument("tournament_path", help="Existing .tgo.json tournament file.")

    regenerate_parser = subparsers.add_parser(
        "regenerate-from",
        help="Remove later rounds and rebuild the next round from a boundary.",
    )
    regenerate_parser.add_argument("tournament_path", help="Existing .tgo.json tournament file.")
    regenerate_parser.add_argument(
        "--round",
        dest="round_number",
        required=True,
        type=int,
        help="Round number to keep as the regeneration boundary.",
    )

    web_parser = subparsers.add_parser("web", help="Start the local web console.")
    web_parser.add_argument("tournament_path", help="Existing .tgo.json tournament file.")
    web_parser.add_argument("--host", default="127.0.0.1", help="Listen host.")
    web_parser.add_argument("--port", type=int, default=8000, help="Listen port.")
    web_parser.add_argument(
        "--open-browser",
        action="store_true",
        help="Open the local URL after the server binds successfully.",
    )

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

    correct_result_parser = subparsers.add_parser(
        "correct-result",
        help="Correct an existing game result and invalidate later rounds.",
    )
    correct_result_parser.add_argument(
        "tournament_path",
        help="Existing .tgo.json tournament file.",
    )
    correct_result_parser.add_argument(
        "--round",
        dest="round_number",
        required=True,
        type=int,
        help="Round number.",
    )
    correct_result_parser.add_argument(
        "--board",
        dest="board_number",
        required=True,
        type=int,
        help="Board number.",
    )
    correct_result_parser.add_argument(
        "--winner",
        required=True,
        choices=("black", "white"),
        help="Correct winning colour.",
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        if args.command == "create":
            TournamentService.create(
                Path(args.path),
                name=args.name,
                round_count=args.rounds,
                format=args.format,
                actor="cli",
            )
            print(f"Created tournament: {args.path}")
            return 0

        if args.command == "demo":
            TournamentService.create_demo(args.path, actor="cli")
            print(f"Created demo tournament: {args.path}")
            return 0

        if args.command == "import-players":
            outcome = TournamentService(args.tournament_path).import_players_file(
                args.csv_path,
                actor="cli",
            )
            for warning in outcome.warnings:
                print(f"Warning: {warning}", file=sys.stderr)
            print(f"Imported {outcome.imported_count} players.")
            return 0

        if args.command == "pair-round":
            outcome = TournamentService(args.tournament_path).generate_next_round(actor="cli")
            for warning in outcome.warnings:
                print(f"Warning: {warning}", file=sys.stderr)
            print(f"Paired round {outcome.round_number} with {outcome.game_count} games.")
            return 0

        if args.command == "standings":
            service = TournamentService(args.tournament_path)
            tournament = service.load()
            standings = service.standings()
            print(f"Standings for {tournament.name} ({tournament.format})")
            print("Pos\tPlayer\tStart\tGame\tTotal\tW\tL\tSOS\tSOSOS")
            for index, entry in enumerate(standings, start=1):
                print(
                    f"{index}\t{entry.player.display_name}\t"
                    f"{entry.starting_score:.1f}\t{entry.game_score:.1f}\t{entry.score:.1f}\t"
                    f"{entry.wins}\t{entry.losses}\t{entry.sos:.1f}\t{entry.sosos:.1f}"
                )
            return 0

        if args.command == "regenerate-from":
            outcome = TournamentService(args.tournament_path).regenerate_from(
                args.round_number,
                actor="cli",
            )
            if outcome is None:
                print(f"No later rounds to regenerate after round {args.round_number}.")
                return 0

            print(f"Generated round {outcome.round_number}.")
            return 0

        if args.command == "enter-result":
            TournamentService(args.tournament_path).record_result(
                round_number=args.round_number,
                board_number=args.board_number,
                winner=args.winner,
                actor="cli",
            )
            print(
                f"Recorded {args.winner} win for round {args.round_number} board {args.board_number}."
            )
            return 0

        if args.command == "correct-result":
            TournamentService(args.tournament_path).correct_result(
                round_number=args.round_number,
                board_number=args.board_number,
                winner=args.winner,
                actor="cli",
            )
            print(
                f"Corrected result to {args.winner} win for round "
                f"{args.round_number} board {args.board_number}."
            )
            return 0

        if args.command == "web":
            serve_tournament(
                Path(args.tournament_path),
                host=args.host,
                port=args.port,
                open_browser=args.open_browser,
            )
            return 0
    except (TournamentStoreError, OSError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    parser.error(f"Unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
