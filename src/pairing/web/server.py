from __future__ import annotations

from pathlib import Path
import webbrowser
from wsgiref.simple_server import make_server

from pairing.web.app import create_web_app


def create_server(
    tournament_path: str | Path,
    *,
    host: str = "127.0.0.1",
    port: int = 8000,
):
    app = create_web_app(tournament_path)
    try:
        httpd = make_server(host, port, app)
    except OSError as exc:
        raise OSError(
            f"Cannot start local web server on {host}:{port}: "
            "the port is already in use."
        ) from exc
    return httpd, f"http://{host}:{httpd.server_port}"


def serve_tournament(
    tournament_path: str | Path,
    *,
    host: str = "127.0.0.1",
    port: int = 8000,
    open_browser: bool = False,
) -> None:
    httpd, url = create_server(tournament_path, host=host, port=port)
    with httpd:
        print(f"Serving {Path(tournament_path).resolve()} at {url}")
        print("Open /, /players, /pairings, /results, /standings, /exports, or /display")
        if open_browser:
            webbrowser.open(url)
        httpd.serve_forever()
