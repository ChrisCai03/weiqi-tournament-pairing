from __future__ import annotations

from io import BytesIO
from wsgiref.util import setup_testing_defaults

from pairing.domain.game import Game
from pairing.domain.player import Player
from pairing.domain.result import Result
from pairing.domain.round import Round
from pairing.domain.tournament import Tournament
from pairing.engine.swiss import generate_next_round
from pairing.storage.json_store import load_tournament, save_tournament
from pairing.web.app import create_web_app


def test_web_console_page_renders_tournament_tabs(tmp_path) -> None:
    tournament_path = tmp_path / "example.tgo.json"
    tournament = Tournament.create("Example Weiqi Open")
    tournament.players.extend(
        [
            Player.create("Alice", rank="4d", seed_number=1),
            Player.create("Bob", rank="3d", seed_number=2),
        ]
    )
    save_tournament(tournament, tournament_path)

    status, headers, body = _call_app(create_web_app(tournament_path), "GET", "/")

    assert status.startswith("200")
    assert headers["Content-Type"].startswith("text/html")
    assert "Example Weiqi Open" in body
    assert "Players" in body
    assert "Pairings" in body
    assert "Display" in body


def test_web_pairings_post_generates_round_and_redirects(tmp_path) -> None:
    tournament_path = tmp_path / "example.tgo.json"
    tournament = Tournament.create("Example Weiqi Open")
    tournament.players.extend(
        [
            Player.create("Alice", rank="4d", seed_number=1),
            Player.create("Bob", rank="3d", seed_number=2),
            Player.create("Charlie", rank="1d", seed_number=3),
            Player.create("Diana", rank="1k", seed_number=4),
        ]
    )
    save_tournament(tournament, tournament_path)

    status, headers, _body = _call_app(
        create_web_app(tournament_path),
        "POST",
        "/pairings/generate",
    )

    assert status.startswith("303")
    assert headers["Location"] == "/pairings"

    saved = load_tournament(tournament_path)
    assert [round_obj.number for round_obj in saved.rounds] == [1]
    assert saved.rounds[0].pairing_method == "swiss"


def test_web_public_display_renders_latest_pairing(tmp_path) -> None:
    tournament_path = tmp_path / "example.tgo.json"
    tournament = Tournament.create("Example Weiqi Open")
    tournament.players.extend(
        [
            Player.create("Alice", rank="4d", seed_number=1),
            Player.create("Bob", rank="3d", seed_number=2),
            Player.create("Charlie", rank="1d", seed_number=3),
            Player.create("Diana", rank="1k", seed_number=4),
        ]
    )
    tournament.rounds.append(generate_next_round(tournament))
    save_tournament(tournament, tournament_path)

    status, headers, body = _call_app(create_web_app(tournament_path), "GET", "/display")

    assert status.startswith("200")
    assert headers["Content-Type"].startswith("text/html")
    assert "Public Display" in body
    assert "Round 1" in body
    assert "Alice" in body or "Bob" in body


def test_web_standings_csv_export_contains_headers(tmp_path) -> None:
    tournament_path = tmp_path / "example.tgo.json"
    tournament = Tournament.create("Example Weiqi Open")
    alice = Player.create("Alice", rank="4d", seed_number=1)
    bob = Player.create("Bob", rank="3d", seed_number=2)
    tournament.players.extend([alice, bob])

    game = Game.create(
        round_number=1,
        board_number=1,
        black_player_id=alice.id,
        white_player_id=bob.id,
        pairing_explanation=[],
    )
    game.result = Result.completed(result_type="normal", winner_player_id=alice.id)
    round_one = Round.create(number=1, games=[game], pairing_method="swiss", pairing_seed=1)
    round_one.status = "completed"
    tournament.rounds.append(round_one)
    save_tournament(tournament, tournament_path)

    status, headers, body = _call_app(
        create_web_app(tournament_path), "GET", "/exports/standings.csv"
    )

    assert status.startswith("200")
    assert headers["Content-Type"].startswith("text/csv")
    assert "Player,Starting Score,Game Score,Total Score" in body
    assert "Alice" in body


def test_web_reports_hub_lists_print_friendly_views(tmp_path) -> None:
    tournament_path = tmp_path / "example.tgo.json"
    tournament = Tournament.create("Example Weiqi Open")
    tournament.players.extend(
        [
            Player.create("Alice", rank="4d", seed_number=1),
            Player.create("Bob", rank="3d", seed_number=2),
        ]
    )
    save_tournament(tournament, tournament_path)

    status, headers, body = _call_app(create_web_app(tournament_path), "GET", "/reports")

    assert status.startswith("200")
    assert headers["Content-Type"].startswith("text/html")
    assert "Print-friendly reports" in body
    assert "/reports/pairings" in body
    assert "/reports/results" in body
    assert "/reports/standings" in body


def test_web_audit_page_reports_unsigned_tournament_without_creating_key(tmp_path, monkeypatch) -> None:
    tournament_path = tmp_path / "example.tgo.json"
    key_path = tmp_path / ".pairing_audit_key"
    monkeypatch.chdir(tmp_path)
    tournament = Tournament.create("Example Weiqi Open")
    save_tournament(tournament, tournament_path)

    status, headers, body = _call_app(create_web_app(tournament_path), "GET", "/audit")

    assert status.startswith("200")
    assert headers["Content-Type"].startswith("text/html")
    assert "Audit integrity" in body
    assert "Audit verification failed" in body
    assert "Audit key not found" in body
    assert "/audit/sign" in body
    assert not key_path.exists()


def test_web_audit_sign_post_signs_file_and_redirects(tmp_path, monkeypatch) -> None:
    tournament_path = tmp_path / "example.tgo.json"
    key_path = tmp_path / ".pairing_audit_key"
    monkeypatch.chdir(tmp_path)
    tournament = Tournament.create("Example Weiqi Open")
    save_tournament(tournament, tournament_path)

    status, headers, _body = _call_app(create_web_app(tournament_path), "POST", "/audit/sign")

    saved = load_tournament(tournament_path)
    assert status.startswith("303")
    assert headers["Location"] == "/audit"
    assert key_path.exists()
    assert all(entry.signature for entry in saved.audit_log)


def test_web_pairings_print_report_renders_current_round(tmp_path) -> None:
    tournament_path = tmp_path / "example.tgo.json"
    tournament = Tournament.create("Example Weiqi Open")
    tournament.players.extend(
        [
            Player.create("Alice", rank="4d", seed_number=1),
            Player.create("Bob", rank="3d", seed_number=2),
            Player.create("Charlie", rank="1d", seed_number=3),
            Player.create("Diana", rank="1k", seed_number=4),
        ]
    )
    tournament.rounds.append(generate_next_round(tournament))
    save_tournament(tournament, tournament_path)

    status, headers, body = _call_app(create_web_app(tournament_path), "GET", "/reports/pairings")

    assert status.startswith("200")
    assert headers["Content-Type"].startswith("text/html")
    assert "Print pairings" in body
    assert "Pairings Report" in body
    assert "Board" in body
    assert "Explanation" in body


def _call_app(app, method: str, path: str, body: str = ""):
    environ = {}
    setup_testing_defaults(environ)
    environ["REQUEST_METHOD"] = method
    environ["PATH_INFO"] = path
    environ["wsgi.input"] = BytesIO(body.encode("utf-8"))
    environ["CONTENT_LENGTH"] = str(len(body.encode("utf-8")))
    environ["CONTENT_TYPE"] = "application/x-www-form-urlencoded"

    captured = {}

    def start_response(status, headers):
        captured["status"] = status
        captured["headers"] = dict(headers)

    result = app(environ, start_response)
    body_text = b"".join(result).decode("utf-8")
    if hasattr(result, "close"):
        result.close()
    return captured["status"], captured["headers"], body_text
