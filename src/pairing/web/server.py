from __future__ import annotations

from pathlib import Path
from wsgiref.simple_server import make_server

from pairing.web.app import create_web_app


def serve_tournament(tournament_path: str | Path, *, host: str = "127.0.0.1", port: int = 8000) -> None:
    app = create_web_app(tournament_path)
    with make_server(host, port, app) as httpd:
        url = f"http://{host}:{httpd.server_port}"
        print(f"Serving {Path(tournament_path)} at {url}")
        print("Open /, /players, /pairings, /results, /standings, /exports, or /display")
        httpd.serve_forever()
