from __future__ import annotations

from urllib.parse import parse_qs


def parse_urlencoded_form(environ) -> dict[str, str]:
    length = int(environ.get("CONTENT_LENGTH", "0") or "0")
    raw = environ["wsgi.input"].read(length) if length else b""
    parsed = parse_qs(raw.decode("utf-8"), keep_blank_values=True)
    return {key: values[-1] if values else "" for key, values in parsed.items()}
