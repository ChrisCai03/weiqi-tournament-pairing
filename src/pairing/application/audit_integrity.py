from __future__ import annotations

import hashlib
import hmac
import json
import os
from dataclasses import dataclass
from pathlib import Path

from pairing.domain.audit import AuditLogEntry
from pairing.domain.tournament import Tournament
from pairing.storage.json_store import load_tournament

_INTEGRITY_FIELDS = frozenset({"signature", "state_hash_before", "state_hash_after"})


@dataclass(frozen=True, slots=True)
class AuditVerificationReport:
    valid: bool
    errors: tuple[str, ...]
    current_state_hash: str


def load_or_create_local_audit_key(path: Path = Path(".pairing_audit_key")) -> bytes:
    if path.exists():
        return load_local_audit_key(path)

    key = os.urandom(32)
    path.write_text(key.hex(), encoding="utf-8")
    try:
        path.chmod(0o600)
    except OSError:
        pass
    return key


def load_local_audit_key(path: Path = Path(".pairing_audit_key")) -> bytes:
    if not path.exists():
        raise FileNotFoundError(f"Audit key not found: {path}")
    return bytes.fromhex(path.read_text(encoding="utf-8").strip())


def state_hash(tournament_or_payload: Tournament | dict[str, object]) -> str:
    payload = _tournament_payload(tournament_or_payload)
    canonical_payload = _state_hash_payload(payload)
    return hashlib.sha256(_canonical_json_bytes(canonical_payload)).hexdigest()


def sign_audit_log(
    tournament: Tournament,
    *,
    key: bytes | None = None,
    key_path: Path | None = None,
) -> Tournament:
    signing_key = _resolve_key(key=key, key_path=key_path)
    current_hash = state_hash(tournament)
    previous_signature = ""
    previous_state_hash: str | None = None

    for entry in tournament.audit_log:
        entry.state_hash_before = previous_state_hash
        entry.state_hash_after = current_hash
        entry.signature = _entry_signature(
            entry=entry,
            previous_signature=previous_signature,
            key=signing_key,
        )
        previous_signature = entry.signature
        previous_state_hash = entry.state_hash_after

    return tournament


def verify_audit_log(
    tournament_or_path: Tournament | dict[str, object] | str | Path,
    *,
    key: bytes | None = None,
    key_path: Path | None = None,
) -> AuditVerificationReport:
    try:
        tournament = _coerce_tournament(tournament_or_path)
    except Exception as exc:
        return AuditVerificationReport(
            valid=False,
            errors=(f"Unable to load tournament for audit verification: {exc}",),
            current_state_hash="",
        )

    current_hash = state_hash(tournament)
    errors: list[str] = []
    previous_signature = ""
    previous_state_hash: str | None = None

    try:
        signing_key = _resolve_key(key=key, key_path=key_path, create=False)
    except (FileNotFoundError, ValueError) as exc:
        return AuditVerificationReport(
            valid=False,
            errors=(str(exc),),
            current_state_hash=current_hash,
        )

    if not tournament.audit_log:
        errors.append("Audit log is empty; nothing to verify.")

    for index, entry in enumerate(tournament.audit_log, start=1):
        if not entry.signature:
            errors.append(f"Audit entry {index} is unsigned.")

        expected_before = previous_state_hash
        if entry.state_hash_before != expected_before:
            if not (
                index == 1
                and entry.state_hash_before is None
                and expected_before is None
            ):
                errors.append(
                    f"Audit entry {index} has state_hash_before mismatch: "
                    f"expected {expected_before!r}, got {entry.state_hash_before!r}."
                )

        if entry.state_hash_after != current_hash:
            errors.append(
                f"Audit entry {index} has state hash mismatch: "
                f"expected {current_hash}, got {entry.state_hash_after!r}."
            )

        if entry.signature:
            expected_signature = _entry_signature(
                entry=entry,
                previous_signature=previous_signature,
                key=signing_key,
            )
            if not hmac.compare_digest(entry.signature, expected_signature):
                errors.append(f"Audit entry {index} has signature mismatch.")

        previous_signature = entry.signature or ""
        previous_state_hash = entry.state_hash_after

    return AuditVerificationReport(
        valid=not errors,
        errors=tuple(errors),
        current_state_hash=current_hash,
    )


def _resolve_key(*, key: bytes | None, key_path: Path | None, create: bool = True) -> bytes:
    if key is not None:
        return key
    path = key_path or Path(".pairing_audit_key")
    if create:
        return load_or_create_local_audit_key(path)
    return load_local_audit_key(path)


def _coerce_tournament(tournament_or_path: Tournament | dict[str, object] | str | Path) -> Tournament:
    if isinstance(tournament_or_path, Tournament):
        return tournament_or_path
    if isinstance(tournament_or_path, (str, Path)):
        return load_tournament(tournament_or_path)
    return Tournament.from_dict(tournament_or_path)


def _tournament_payload(tournament_or_payload: Tournament | dict[str, object]) -> dict[str, object]:
    if isinstance(tournament_or_payload, Tournament):
        return tournament_or_payload.to_dict()
    return tournament_or_payload


def _state_hash_payload(payload: dict[str, object]) -> dict[str, object]:
    normalized = _normalize_structure(payload)
    audit_log = normalized.get("audit_log")
    if isinstance(audit_log, list):
        normalized["audit_log"] = [
            {
                key: value
                for key, value in entry.items()
                if key not in _INTEGRITY_FIELDS
            }
            if isinstance(entry, dict)
            else entry
            for entry in audit_log
        ]
    return normalized


def _normalize_structure(value: object) -> object:
    if isinstance(value, dict):
        return {key: _normalize_structure(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_normalize_structure(item) for item in value]
    return value


def _entry_signature(*, entry: AuditLogEntry, previous_signature: str, key: bytes) -> str:
    payload = entry.to_dict()
    payload.pop("signature", None)
    message = previous_signature.encode("utf-8") + _canonical_json_bytes(payload)
    return hmac.new(key, message, hashlib.sha256).hexdigest()


def _canonical_json_bytes(payload: object) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode(
        "utf-8"
    )
