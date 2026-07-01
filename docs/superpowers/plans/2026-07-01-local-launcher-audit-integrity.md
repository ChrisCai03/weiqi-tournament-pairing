# Local Launcher and Audit Integrity Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a click-and-go Windows launcher and a local tamper-evident audit signing/verification layer.

**Architecture:** Keep the launcher as a root batch file and keep audit integrity in a focused module. Use a local git-ignored HMAC key provider now, with signatures isolated behind functions so future passphrase/keychain/external signing backends can replace it.

**Tech Stack:** Windows batch, Python 3.12 standard library, HMAC-SHA256, JSON canonicalization, pytest, Ruff.

---

## File Structure

- Create: `run_local.bat` — click-and-go local web startup.
- Modify: `.gitignore` — ignore `.pairing_audit_key`.
- Create: `src/pairing/application/audit_integrity.py` — canonical hashing, local key, signing, verification.
- Modify: `src/pairing/domain/audit.py` — persist audit signature field.
- Modify: `src/pairing/application/service.py` — expose audit sign/verify methods.
- Modify: `src/pairing/cli/main.py` — add `audit-sign` and `audit-verify`.
- Test: `tests/unit/test_run_local.py`.
- Test: `tests/unit/test_audit_integrity.py`.
- Test: `tests/unit/test_cli.py`.

## Task 1: Add click-and-go launcher

- [ ] Write `tests/unit/test_run_local.py` asserting `run_local.bat` exists, uses `PYTHONPATH=src`, creates `.tmp\demo.tgo.json`, serves port `8123`, and opens browser.
- [ ] Verify RED with `python -m pytest tests/unit/test_run_local.py -q`.
- [ ] Create `run_local.bat` with source-checkout friendly commands.
- [ ] Verify GREEN with `python -m pytest tests/unit/test_run_local.py -q`.
- [ ] Run `python -m ruff check tests/unit/test_run_local.py`.
- [ ] Commit `Add local web launcher script`.

## Task 2: Add audit integrity module

- [ ] Write `tests/unit/test_audit_integrity.py` for deterministic canonical hashes, git-ignored local key creation, signing existing audit entries, verification success, and tamper detection after manual JSON edits.
- [ ] Verify RED with `python -m pytest tests/unit/test_audit_integrity.py -q`.
- [ ] Add `signature` to `AuditLogEntry`.
- [ ] Implement `src/pairing/application/audit_integrity.py` with local HMAC key provider, state hashing, signing, and verification report.
- [ ] Verify GREEN with `python -m pytest tests/unit/test_audit_integrity.py -q`.
- [ ] Run `python -m ruff check src/pairing/application/audit_integrity.py src/pairing/domain/audit.py tests/unit/test_audit_integrity.py`.
- [ ] Commit `Add tamper-evident audit integrity`.

## Task 3: Expose audit sign/verify through service and CLI

- [ ] Write failing tests in `tests/unit/test_cli.py` for `audit-sign` and `audit-verify`.
- [ ] Verify RED with `python -m pytest tests/unit/test_cli.py -q -k audit`.
- [ ] Add `TournamentService.sign_audit()` and `TournamentService.verify_audit()`.
- [ ] Add `pairing audit-sign <path>` and `pairing audit-verify <path>`.
- [ ] Verify GREEN with `python -m pytest tests/unit/test_cli.py tests/unit/test_audit_integrity.py -q`.
- [ ] Run focused Ruff.
- [ ] Commit `Expose audit integrity commands`.

## Task 4: Final verification and handoff

- [ ] Run `python -m pytest tests/unit/test_run_local.py tests/unit/test_audit_integrity.py tests/unit/test_cli.py tests/unit/test_json_store.py -q`.
- [ ] Run `python -m pytest -q` if time allows.
- [ ] Run `python -m ruff check src tests`.
- [ ] Confirm `git status --short --branch` is clean.
- [ ] Push `codex/stage-6-director-workflow`.
