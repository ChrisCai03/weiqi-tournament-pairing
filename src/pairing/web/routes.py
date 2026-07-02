from __future__ import annotations

from pairing.application import TournamentService
from pairing.web import views
from pairing.web.forms import parse_urlencoded_form
from pairing.web.responses import csv_response, html_response, redirect_response

GET_ROUTES = {
    "/": ("Overview", "overview", views._render_overview_section),
    "/players": ("Players", "players", views._render_players_section),
    "/pairings": ("Pairings", "pairings", views._render_pairings_section),
    "/results": ("Results", "results", views._render_results_section),
    "/standings": ("Standings", "standings", views._render_standings_section),
    "/audit": ("Audit", "audit", None),
    "/exports": ("Exports", "exports", lambda _tournament: views._render_exports_section()),
    "/reports": ("Reports", "reports", views._render_reports_section),
    "/reports/pairings": ("Pairings Report", "reports", views._render_pairings_report),
    "/reports/results": ("Results Report", "reports", views._render_results_report),
    "/reports/standings": ("Standings Report", "reports", views._render_standings_report),
}
CSV_ROUTES = {
    "/exports/players.csv": ("players", "players.csv"),
    "/exports/pairings.csv": ("pairings", "pairings.csv"),
    "/exports/results.csv": ("results", "results.csv"),
    "/exports/standings.csv": ("standings", "standings.csv"),
}
POST_ROUTES = {
    "/players/import",
    "/pairings/generate",
    "/pairings/regenerate",
    "/results/enter",
    "/results/correct",
    "/audit/sign",
}


def dispatch_request(service: TournamentService, environ, start_response):
    method = environ.get("REQUEST_METHOD", "GET").upper()
    path = environ.get("PATH_INFO", "/")
    allowed = _allowed_methods(path)
    if not allowed:
        tournament = service.load()
        return html_response(
            start_response,
            404,
            views._render_error_page(tournament, "Page not found."),
        )
    if method not in allowed:
        tournament = service.load()
        return html_response(
            start_response,
            405,
            views._render_error_page(tournament, "Method not allowed."),
            headers=[("Allow", ", ".join(sorted(allowed)))],
        )

    try:
        if method == "POST":
            return _dispatch_post(service, path, environ, start_response)
        return _dispatch_get(service, path, start_response)
    except (OSError, ValueError) as exc:
        error_tournament = service.load() if service.path.exists() else None
        return html_response(
            start_response,
            400,
            views._render_error_page(error_tournament, str(exc)),
        )
    except Exception:
        error_tournament = service.load() if service.path.exists() else None
        return html_response(
            start_response,
            500,
            views._render_error_page(error_tournament, "Unexpected server error."),
        )


def _allowed_methods(path: str) -> set[str]:
    allowed = set()
    if path in GET_ROUTES or path in CSV_ROUTES or path == "/display":
        allowed.add("GET")
    if path in POST_ROUTES:
        allowed.add("POST")
    return allowed


def _dispatch_get(service, path, start_response):
    if path in CSV_ROUTES:
        report, filename = CSV_ROUTES[path]
        return csv_response(start_response, service.export_csv(report), filename)
    tournament = service.load()
    if path == "/display":
        return html_response(start_response, 200, views._render_public_display(tournament))
    if path == "/audit":
        report = service.verify_audit()
        return html_response(
            start_response,
            200,
            views._render_page(
                tournament,
                "Audit",
                views._render_audit_section(tournament, report),
                active_tab="audit",
            ),
        )
    title, tab, renderer = GET_ROUTES[path]
    if renderer is None:
        raise ValueError(f"Route {path} has no renderer.")
    return html_response(
        start_response,
        200,
        views._render_page(tournament, title, renderer(tournament), active_tab=tab),
    )


def _dispatch_post(service, path, environ, start_response):
    form = parse_urlencoded_form(environ)
    if path == "/players/import":
        service.import_players_text(form.get("csv_text", ""), actor="web")
        return redirect_response(start_response, "/players")
    if path == "/pairings/generate":
        service.generate_next_round(actor="web")
        return redirect_response(start_response, "/pairings")
    if path == "/pairings/regenerate":
        service.regenerate_from(int(form.get("round_number", "0") or "0"), actor="web")
        return redirect_response(start_response, "/pairings")
    if path == "/audit/sign":
        service.sign_audit()
        return redirect_response(start_response, "/audit")
    result_args = {
        "round_number": int(form.get("round_number", "0") or "0"),
        "board_number": int(form.get("board_number", "0") or "0"),
        "winner": form.get("winner", "black"),
        "actor": "web",
    }
    if path == "/results/correct":
        service.correct_result(**result_args)
    else:
        service.record_result(**result_args)
    return redirect_response(start_response, "/results")
