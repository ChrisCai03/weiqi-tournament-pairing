# Local Launcher and Audit Integrity Design

## Scope

This slice pauses the wider Stage 6 queue and prioritises two operator-facing needs:

1. A Windows `run_local.bat` that starts the prototype web app with minimal setup.
2. A tamper-evident audit integrity layer that allows manual file edits but makes them detectable and recordable.

## Launcher design

`run_local.bat` lives at the repository root. It creates `.tmp\demo.tgo.json` if no tournament file is supplied, then starts the local web console on `127.0.0.1:8123` with browser opening enabled. A user can also pass an existing `.tgo.json` path as `%1`.

The script uses `python -m pairing.cli.main` with `PYTHONPATH=src` so it works from a source checkout without requiring installation.

## Audit integrity design

The first implementation uses a local HMAC-SHA256 key stored in `.pairing_audit_key`, which is ignored by git. The crypto boundary is intentionally small:

- key management lives behind a local key-provider function;
- canonical JSON hashing lives in an audit integrity module;
- tournament save/load paths can ask for verification and signing without knowing key details.

Future iterations can replace the local key provider with a passphrase, OS keychain, hardware key, or external signing service without changing the audit event schema.

Audit entries become hash-chained:

- each entry records `state_hash_before`, `state_hash_after`, and an HMAC `signature`;
- the signature covers the previous audit signature, the audit event content, and the canonical tournament state hashes;
- verification recomputes the chain and reports missing, invalid, or externally modified state.

Manual edits remain allowed. If a file changes outside audited workflows, verification should report the mismatch. A later workflow may append an explicit `external_file_change_detected` audit event after director acknowledgement; this slice focuses on detection, signing, and CLI visibility.

## CLI design

Add audit commands:

- `pairing audit-sign <path>` signs existing audit entries and the current state.
- `pairing audit-verify <path>` verifies the audit chain and current file state.

These commands are deliberately simple and local-first. They do not encrypt tournament contents; they provide tamper evidence. The term “encryption system” is implemented as keyed integrity signing in this slice, because that directly addresses malicious edits while keeping manual source-file edits possible.

## Testing

Tests cover:

- launcher script exists and references the expected CLI commands and port;
- key generation is local and git-ignored;
- canonical state hashes are deterministic;
- signatures verify after normal save/sign;
- manual JSON edits are detected;
- existing unsigned files can be signed for bootstrapping.
