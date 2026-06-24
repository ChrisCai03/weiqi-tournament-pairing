from __future__ import annotations

REASONS = {
    200: "OK",
    303: "See Other",
    400: "Bad Request",
    404: "Not Found",
    405: "Method Not Allowed",
    500: "Internal Server Error",
}


def html_response(start_response, status_code: int, body: str, headers=None):
    body_bytes = body.encode("utf-8")
    response_headers = [
        ("Content-Type", "text/html; charset=utf-8"),
        ("Content-Length", str(len(body_bytes))),
    ]
    response_headers.extend(headers or [])
    start_response(f"{status_code} {REASONS[status_code]}", response_headers)
    return [body_bytes]


def csv_response(start_response, csv_text: str, filename: str):
    body_bytes = csv_text.encode("utf-8-sig")
    start_response(
        "200 OK",
        [
            ("Content-Type", "text/csv; charset=utf-8"),
            ("Content-Disposition", f'attachment; filename="{filename}"'),
            ("Content-Length", str(len(body_bytes))),
        ],
    )
    return [body_bytes]


def redirect_response(start_response, location: str):
    start_response("303 See Other", [("Location", location), ("Content-Length", "0")])
    return [b""]
