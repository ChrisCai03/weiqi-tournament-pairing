from __future__ import annotations

from dataclasses import dataclass
from html import escape
from io import BytesIO
from pathlib import Path
from typing import Callable
from urllib.parse import parse_qs

from pairing.domain.game import Game
from pairing.domain.player import Player
from pairing.domain.tournament import Tournament
from pairing.engine.mcmahon import mcmahon_starting_score
from pairing.engine.round_generation import generate_next_round
from pairing.engine.standings import calculate_standings
from pairing.import_export.csv_export import pairings_to_csv, players_to_csv, results_to_csv, standings_to_csv
from pairing.import_export.csv_import import import_players_from_csv_text
from pairing.storage import load_tournament, save_tournament


@dataclass(slots=True)
class WebResponse:
    status: str
    headers: list[tuple[str, str]]
    body: bytes


def create_web_app(tournament_path: str | Path) -> Callable:
    state = WebState(Path(tournament_path))
    return lambda environ, start_response: _application(state, environ, start_response)


@dataclass(slots=True)
class WebState:
    tournament_path: Path

    def load(self) -> Tournament:
        return load_tournament(self.tournament_path)

    def save(self, tournament: Tournament) -> None:
        save_tournament(tournament, self.tournament_path)


def _application(state: WebState, environ, start_response):
    method = environ.get("REQUEST_METHOD", "GET").upper()
    path = environ.get("PATH_INFO", "/")
    form = _parse_form(environ)

    try:
        if method == "POST" and path == "/players/import":
            tournament = state.load()
            report = import_players_from_csv_text(form.get("csv_text", ""))
            if not report.valid:
                return _respond_html(start_response, 400, _render_page(
                    tournament,
                    "Players",
                    _render_error_list(report.errors),
                    active_tab="players",
                    extra_html=_render_players_section(tournament, report.warnings),
                ))
            tournament.add_players(report.players)
            state.save(tournament)
            return _redirect(start_response, "/players")

        if method == "POST" and path == "/pairings/generate":
            tournament = state.load()
            round_obj = generate_next_round(tournament)
            tournament.rounds.append(round_obj)
            state.save(tournament)
            return _redirect(start_response, "/pairings")

        if method == "POST" and path == "/pairings/regenerate":
            tournament = state.load()
            boundary = int(form.get("round_number", "0") or "0")
            tournament.mark_rounds_stale_after(boundary)
            tournament.purge_stale_rounds()
            if boundary < tournament.config.round_count:
                round_obj = generate_next_round(tournament)
                tournament.rounds.append(round_obj)
            state.save(tournament)
            return _redirect(start_response, "/pairings")

        if method == "POST" and path == "/results/enter":
            tournament = state.load()
            tournament.record_result(
                round_number=int(form.get("round_number", "0") or "0"),
                board_number=int(form.get("board_number", "0") or "0"),
                winner=form.get("winner", "black"),
            )
            state.save(tournament)
            return _redirect(start_response, "/results")

        if path == "/exports/players.csv":
            tournament = state.load()
            return _respond_csv(start_response, players_to_csv(tournament), "players.csv")

        if path == "/exports/pairings.csv":
            tournament = state.load()
            return _respond_csv(start_response, pairings_to_csv(tournament), "pairings.csv")

        if path == "/exports/results.csv":
            tournament = state.load()
            return _respond_csv(start_response, results_to_csv(tournament), "results.csv")

        if path == "/exports/standings.csv":
            tournament = state.load()
            return _respond_csv(start_response, standings_to_csv(tournament), "standings.csv")

        tournament = state.load()
        if path == "/players":
            body = _render_page(tournament, "Players", _render_players_section(tournament), active_tab="players")
        elif path == "/pairings":
            body = _render_page(tournament, "Pairings", _render_pairings_section(tournament), active_tab="pairings")
        elif path == "/results":
            body = _render_page(tournament, "Results", _render_results_section(tournament), active_tab="results")
        elif path == "/standings":
            body = _render_page(tournament, "Standings", _render_standings_section(tournament), active_tab="standings")
        elif path == "/exports":
            body = _render_page(tournament, "Exports", _render_exports_section(), active_tab="exports")
        elif path == "/display":
            body = _render_public_display(tournament)
        else:
            body = _render_page(tournament, "Overview", _render_overview_section(tournament), active_tab="overview")
        return _respond_html(start_response, 200, body)
    except (OSError, ValueError) as exc:
        tournament = state.load() if state.tournament_path.exists() else None
        body = _render_error_page(tournament, str(exc))
        return _respond_html(start_response, 400, body)


def _render_page(tournament: Tournament, title: str, content: str, *, active_tab: str) -> str:
    tabs = [
        ("overview", "Overview", "/"),
        ("players", "Players", "/players"),
        ("pairings", "Pairings", "/pairings"),
        ("results", "Results", "/results"),
        ("standings", "Standings", "/standings"),
        ("exports", "Exports", "/exports"),
        ("display", "Display", "/display"),
    ]
    nav = "".join(
        f'<a class="tab{" active" if key == active_tab else ""}" href="{href}">{label}</a>'
        for key, label, href in tabs
    )
    return f"""
    <!doctype html>
    <html>
      <head>
        <meta charset="utf-8">
        <title>{escape(tournament.name)} - {escape(title)}</title>
        <style>
          :root {{ --bg:#f6f7fb; --panel:#ffffff; --line:#d7dbe3; --text:#1c2430; --muted:#667182; --accent:#2563eb; --accent2:#0f766e; --warn:#b45309; }}
          * {{ box-sizing: border-box; }}
          body {{ margin:0; font-family: Inter, Segoe UI, Arial, sans-serif; background: var(--bg); color: var(--text); }}
          .shell {{ max-width: 1440px; margin: 0 auto; padding: 20px; }}
          .topbar {{ background: var(--panel); border: 1px solid var(--line); border-radius: 12px; padding: 14px 16px; }}
          .title-row {{ display:flex; justify-content:space-between; gap:16px; align-items:flex-start; }}
          h1 {{ margin:0; font-size: 24px; }}
          .subtitle {{ color: var(--muted); margin-top:4px; font-size: 13px; }}
          .tabs {{ display:flex; gap: 8px; flex-wrap:wrap; margin-top: 14px; }}
          .tab {{ text-decoration:none; color: var(--muted); border:1px solid var(--line); padding: 7px 10px; border-radius: 999px; font-size: 13px; }}
          .tab.active {{ color: #fff; background: var(--accent); border-color: var(--accent); }}
          .content {{ margin-top: 18px; display:grid; gap:16px; grid-template-columns: 1.5fr 0.9fr; }}
          .content.single {{ grid-template-columns: 1fr; }}
          .card {{ background: var(--panel); border: 1px solid var(--line); border-radius: 12px; padding: 16px; }}
          .section-title {{ margin: 0 0 12px; font-size: 16px; }}
          .muted {{ color: var(--muted); font-size: 13px; }}
          table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
          th, td {{ padding: 8px 6px; border-bottom: 1px solid #edf0f5; text-align:left; vertical-align:top; }}
          th {{ font-weight: 700; }}
          .actions {{ display:flex; gap: 8px; flex-wrap: wrap; margin-top: 10px; }}
          .button {{ display:inline-block; padding: 8px 12px; border-radius: 8px; border:1px solid var(--line); background:#f8fafc; color: var(--text); text-decoration:none; font-size: 13px; }}
          .button.primary {{ background: var(--accent); border-color: var(--accent); color: #fff; }}
          .button.good {{ background: var(--accent2); border-color: var(--accent2); color: #fff; }}
          .button.warn {{ background: #fff7ed; border-color: #fdba74; color: var(--warn); }}
          textarea, input, select {{ width:100%; padding: 9px 10px; border-radius: 8px; border: 1px solid var(--line); font: inherit; }}
          textarea {{ min-height: 140px; resize: vertical; }}
          .grid-2 {{ display:grid; gap:12px; grid-template-columns: 1fr 1fr; }}
          .grid-3 {{ display:grid; gap:12px; grid-template-columns: 1fr 1fr 1fr; }}
          .pill {{ display:inline-block; padding: 4px 8px; border-radius: 999px; background: #eef2ff; color: #4338ca; font-size: 12px; }}
          .error-box {{ background:#fff7ed; border:1px solid #fdba74; color:#9a3412; padding: 12px; border-radius: 10px; margin-bottom: 12px; }}
          .footer-note {{ margin-top:12px; color: var(--muted); font-size: 12px; }}
        </style>
      </head>
      <body>
        <div class="shell">
          <div class="topbar">
            <div class="title-row">
              <div>
                <h1>{escape(tournament.name)}</h1>
                <div class="subtitle">{escape(tournament.format.title())} • {len(tournament.players)} players • {len(tournament.rounds)} rounds</div>
              </div>
              <div class="pill">Local web app</div>
            </div>
            <div class="tabs">{nav}</div>
          </div>
          <div class="content {'single' if active_tab == 'display' else ''}">
            {content}
          </div>
        </div>
      </body>
    </html>
    """


def _render_overview_section(tournament: Tournament) -> str:
    current_round = _current_round(tournament)
    round_label = f"Round {current_round.number}" if current_round else "No rounds yet"
    current_scoreboard = _render_preview_standings(tournament)
    return f"""
    <div class="card">
      <h2 class="section-title">Workflow</h2>
      <div class="grid-2">
        <div>
          <div class="muted">Current state</div>
          <p>{escape(round_label)}</p>
          <div class="actions">
            <a class="button primary" href="/pairings">Pairings</a>
            <a class="button" href="/results">Results</a>
            <a class="button" href="/standings">Standings</a>
            <a class="button" href="/display">Public display</a>
          </div>
        </div>
        <div>
          <div class="muted">Quick actions</div>
          <form method="post" action="/pairings/generate">
            <button class="button good" type="submit">Generate next round</button>
          </form>
        </div>
      </div>
    </div>
    <div class="card">
      <h2 class="section-title">Preview standings</h2>
      {current_scoreboard}
    </div>
    """


def _render_players_section(tournament: Tournament, warnings: list[str] | None = None) -> str:
    warning_html = ""
    if warnings:
        warning_html = "<div class='error-box'>" + "<br>".join(escape(item) for item in warnings) + "</div>"
    rows = "".join(
        f"<tr><td>{index}</td><td>{escape(player.display_name)}</td><td>{escape(player.rank)}</td><td>{player.seed_number}</td><td>{escape(player.status)}</td></tr>"
        for index, player in enumerate(tournament.players, start=1)
    )
    return f"""
    <div class="card">
      <h2 class="section-title">Players</h2>
      {warning_html}
      <form method="post" action="/players/import">
        <label class="muted">Paste CSV here</label>
        <textarea name="csv_text" placeholder="name,rank&#10;Alice,3d&#10;Bob,1k"></textarea>
        <div class="actions"><button class="button primary" type="submit">Import players</button></div>
      </form>
    </div>
    <div class="card">
      <h2 class="section-title">Roster</h2>
      <table>
        <thead><tr><th>#</th><th>Name</th><th>Rank</th><th>Seed</th><th>Status</th></tr></thead>
        <tbody>{rows or '<tr><td colspan="5" class="muted">No players yet</td></tr>'}</tbody>
      </table>
    </div>
    """


def _render_pairings_section(tournament: Tournament) -> str:
    current_round = _current_round(tournament)
    rows = _render_round_rows(current_round, tournament) if current_round else "<tr><td colspan='5' class='muted'>No pairings yet</td></tr>"
    regen_form = """
      <form method="post" action="/pairings/regenerate">
        <label class="muted">Regenerate from round</label>
        <input name="round_number" type="number" min="1" value="1">
        <div class="actions"><button class="button warn" type="submit">Regenerate</button></div>
      </form>
    """
    return f"""
    <div class="card">
      <h2 class="section-title">Pairings</h2>
      <form method="post" action="/pairings/generate">
        <div class="actions">
          <button class="button good" type="submit">Generate next round</button>
        </div>
      </form>
      <div class="footer-note">Current pairing method: {escape(tournament.format.title())}</div>
    </div>
    <div class="card">
      <h2 class="section-title">Latest round</h2>
      <table>
        <thead><tr><th>Board</th><th>Black</th><th>White</th><th>Result</th><th>Explanation</th></tr></thead>
        <tbody>{rows}</tbody>
      </table>
    </div>
    <div class="card">{regen_form}</div>
    """


def _render_results_section(tournament: Tournament) -> str:
    current_round = _current_round(tournament)
    if not current_round:
        return """
        <div class="card">
          <h2 class="section-title">Results</h2>
          <p class="muted">Generate a round first to enter results.</p>
        </div>
        """
    game_rows = "".join(
        f"""
        <tr>
          <td>{game.board_number}</td>
          <td>{_player_label(tournament, game.black_player_id)}</td>
          <td>{_player_label(tournament, game.white_player_id)}</td>
          <td>{escape(game.result.result_type)}</td>
          <td>
            <form method="post" action="/results/enter">
              <input type="hidden" name="round_number" value="{current_round.number}">
              <input type="hidden" name="board_number" value="{game.board_number}">
              <div class="grid-3">
                <select name="winner">
                  <option value="black">Black</option>
                  <option value="white">White</option>
                </select>
                <button class="button primary" type="submit">Enter result</button>
              </div>
            </form>
          </td>
        </tr>
        """
        for game in current_round.games
    )
    return f"""
    <div class="card">
      <h2 class="section-title">Round {current_round.number} results</h2>
      <table>
        <thead><tr><th>Board</th><th>Black</th><th>White</th><th>Status</th><th>Action</th></tr></thead>
        <tbody>{game_rows}</tbody>
      </table>
    </div>
    """


def _render_standings_section(tournament: Tournament) -> str:
    return f"""
    <div class="card">
      <h2 class="section-title">Standings</h2>
      {_render_preview_standings(tournament)}
    </div>
    """


def _render_exports_section() -> str:
    return """
    <div class="card">
      <h2 class="section-title">Exports</h2>
      <div class="actions">
        <a class="button" href="/exports/players.csv">Players CSV</a>
        <a class="button" href="/exports/pairings.csv">Pairings CSV</a>
        <a class="button" href="/exports/results.csv">Results CSV</a>
        <a class="button" href="/exports/standings.csv">Standings CSV</a>
      </div>
      <p class="footer-note">CSV export is the first Stage 4 report surface. PDF can layer on top later.</p>
    </div>
    """


def _render_public_display(tournament: Tournament) -> str:
    current_round = _current_round(tournament)
    if current_round is None:
        body = "<div class='card'><h2 class='section-title'>Public Display</h2><p class='muted'>No pairings yet.</p></div>"
    else:
        body = f"""
        <div class="card">
          <h2 class="section-title">Public Display</h2>
          <div class="muted">Round {current_round.number} • {escape(tournament.format.title())}</div>
          <table>
            <thead><tr><th>Board</th><th>Black</th><th>White</th></tr></thead>
            <tbody>{''.join(_render_display_row(tournament, game) for game in current_round.games)}</tbody>
          </table>
        </div>
        """
    return _render_page(tournament, "Public Display", body, active_tab="display")


def _render_display_row(tournament: Tournament, game: Game) -> str:
    return f"<tr><td>{game.board_number}</td><td>{_player_label(tournament, game.black_player_id)}</td><td>{_player_label(tournament, game.white_player_id)}</td></tr>"


def _render_round_rows(current_round, tournament: Tournament) -> str:
    if current_round is None:
        return "<tr><td colspan='5' class='muted'>No pairings yet</td></tr>"
    return "".join(
        f"<tr><td>{game.board_number}</td><td>{_player_label(tournament, game.black_player_id)}</td><td>{_player_label(tournament, game.white_player_id)}</td><td>{escape(game.result.result_type)}</td><td>{escape(current_round.explanation_summary[0] if current_round.explanation_summary else '')}</td></tr>"
        for game in current_round.games
    )


def _render_preview_standings(tournament: Tournament) -> str:
    standings = calculate_standings(
        tournament,
        starting_score_provider=(
            lambda player: mcmahon_starting_score(player, tournament)
            if tournament.format == "mcmahon"
            else 0.0
        ),
    )
    rows = "".join(
        f"<tr><td>{index}</td><td>{escape(entry.player.display_name)}</td><td>{entry.starting_score:.1f}</td><td>{entry.game_score:.1f}</td><td>{entry.score:.1f}</td></tr>"
        for index, entry in enumerate(standings, start=1)
    )
    return f"""
    <table>
      <thead><tr><th>Pos</th><th>Player</th><th>Start</th><th>Game</th><th>Total</th></tr></thead>
      <tbody>{rows or '<tr><td colspan="5" class="muted">No standings yet</td></tr>'}</tbody>
    </table>
    """


def _player_label(tournament: Tournament, player_id: str | None) -> str:
    if player_id is None:
        return ""
    for player in tournament.players:
        if player.id == player_id:
            return player.display_name
    return player_id


def _current_round(tournament: Tournament):
    valid_rounds = [round_obj for round_obj in tournament.rounds if round_obj.status != "stale"]
    if not valid_rounds:
        return None
    return max(valid_rounds, key=lambda round_obj: round_obj.number)


def _render_error_list(errors: list[str]) -> str:
    return "<div class='error-box'>" + "<br>".join(escape(item) for item in errors) + "</div>"


def _render_error_page(tournament: Tournament | None, message: str) -> str:
    fake_tournament = tournament or Tournament.create("Temporary")
    return _render_page(
        fake_tournament,
        "Error",
        f"<div class='card'><h2 class='section-title'>Error</h2><div class='error-box'>{escape(message)}</div></div>",
        active_tab="overview",
    )


def _respond_html(start_response, status_code: int, body: str):
    reason = {
        200: "OK",
        303: "See Other",
        400: "Bad Request",
        404: "Not Found",
    }.get(status_code, "OK")
    body_bytes = body.encode("utf-8")
    headers = [("Content-Type", "text/html; charset=utf-8"), ("Content-Length", str(len(body_bytes)))]
    start_response(f"{status_code} {reason}", headers)
    return [body_bytes]


def _respond_csv(start_response, csv_text: str, filename: str):
    body_bytes = csv_text.encode("utf-8-sig")
    headers = [
        ("Content-Type", "text/csv; charset=utf-8"),
        ("Content-Disposition", f'attachment; filename="{filename}"'),
        ("Content-Length", str(len(body_bytes))),
    ]
    start_response("200 OK", headers)
    return [body_bytes]


def _redirect(start_response, location: str):
    start_response("303 See Other", [("Location", location), ("Content-Length", "0")])
    return [b""]


def _parse_form(environ) -> dict[str, str]:
    if environ.get("REQUEST_METHOD", "GET").upper() != "POST":
        return {}
    try:
        length = int(environ.get("CONTENT_LENGTH", "0") or "0")
    except ValueError:
        length = 0
    raw = environ["wsgi.input"].read(length) if length else b""
    parsed = parse_qs(raw.decode("utf-8"), keep_blank_values=True)
    return {key: values[-1] if values else "" for key, values in parsed.items()}
