from __future__ import annotations

from pathlib import Path

from pairing.application import TournamentService
from pairing.web.routes import dispatch_request


def create_web_app(tournament_path: str | Path):
    service = TournamentService(tournament_path)
    return lambda environ, start_response: dispatch_request(
        service,
        environ,
        start_response,
    )
