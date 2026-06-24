from io import BytesIO
from wsgiref.util import setup_testing_defaults

from pairing.domain import Player, Tournament
from pairing.storage import load_tournament, save_tournament
from pairing.web.app import create_web_app


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
    content = b"".join(result).decode("utf-8")
    return captured["status"], captured["headers"], content


def _write_tournament(path) -> None:
    tournament = Tournament.create("Routing Open")
    tournament.players.extend(
        [
            Player.create("Alice", rank="1d", seed_number=1),
            Player.create("Bob", rank="1k", seed_number=2),
        ]
    )
    save_tournament(tournament, path)


def test_unknown_route_returns_404(tmp_path) -> None:
    path = tmp_path / "event.tgo.json"
    _write_tournament(path)

    status, _headers, body = _call_app(create_web_app(path), "GET", "/missing")

    assert status.startswith("404")
    assert "Page not found" in body


def test_unsupported_method_returns_405_and_allow_header(tmp_path) -> None:
    path = tmp_path / "event.tgo.json"
    _write_tournament(path)

    status, headers, _body = _call_app(create_web_app(path), "POST", "/standings")

    assert status.startswith("405")
    assert headers["Allow"] == "GET"


def test_invalid_form_returns_400_without_mutation(tmp_path) -> None:
    path = tmp_path / "event.tgo.json"
    _write_tournament(path)
    before = path.read_bytes()

    status, _headers, body = _call_app(
        create_web_app(path),
        "POST",
        "/results/enter",
        "round_number=abc&board_number=1&winner=black",
    )

    assert status.startswith("400")
    assert "invalid literal" in body
    assert path.read_bytes() == before


def test_web_pairing_mutation_persists_service_audit_actor(tmp_path) -> None:
    path = tmp_path / "event.tgo.json"
    _write_tournament(path)

    status, headers, _body = _call_app(
        create_web_app(path),
        "POST",
        "/pairings/generate",
    )

    loaded = load_tournament(path)
    assert status.startswith("303")
    assert headers["Location"] == "/pairings"
    assert loaded.audit_log[-1].event_type == "round_pairings_generated"
    assert loaded.audit_log[-1].actor == "web"
