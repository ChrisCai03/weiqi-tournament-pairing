from __future__ import annotations

from pathlib import Path

from pairing.application import TournamentService
from pairing.web.routes import dispatch_request


def create_web_app(tournament_path: str | Path):
    path = Path(tournament_path)
    service = TournamentService(
        path,
        auto_sign_audit=True,
        audit_key_path=path.parent / ".pairing_audit_key",
    )
    return lambda environ, start_response: dispatch_request(
        service,
        environ,
        start_response,
    )
