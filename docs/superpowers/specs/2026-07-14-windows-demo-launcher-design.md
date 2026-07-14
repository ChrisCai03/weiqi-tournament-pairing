# Windows Demo Launcher Design

## Goal

Provide a portable, click-and-run Windows launcher for testing the Weiqi
tournament application from a fresh checkout on another PC.

## User Workflow

The user double-clicks `run-demo.bat` in the repository root. The launcher:

1. locates Python 3.12 or newer;
2. creates a repository-local `.venv` when needed;
3. installs the project and development dependencies into that environment;
4. creates a demo tournament when the launcher demo file does not exist;
5. starts the local web server and opens it in the default browser; and
6. leaves useful diagnostics visible if setup or startup fails.

Subsequent launches reuse both the virtual environment and demo tournament.
This preserves test progress while still allowing the environment to be
recreated by deleting `.venv`.

## Portability

The launcher must not contain usernames, drive letters, absolute repository
paths, or assumptions about the current working directory. All paths are
resolved relative to the launcher itself.

The only host prerequisite is a supported Windows installation with Python
3.12 or newer available through the Python launcher (`py`) or `python` on
`PATH`. Dependencies are installed into `.venv`; the launcher does not modify
the user's global Python environment.

The environment is intentionally disposable and must remain excluded from
Git. Moving to another PC requires copying or cloning the repository and
running the batch file again. The new PC creates its own environment rather
than copying `.venv` from the old PC.

## Components

- `run-demo.bat`: minimal double-click entry point. It changes to the
  repository directory, invokes the PowerShell setup script, propagates the
  exit status, and pauses when an error would otherwise close the window.
- `scripts/run-demo.ps1`: readable setup and launch orchestration, including
  Python discovery, version validation, virtual-environment creation,
  dependency installation, demo creation, and application startup.
- `demo-data/launcher-demo.tgo.json`: generated local test state. The launcher
  creates it on first use and reuses it afterward.
- README and trial-runbook notes: explain the one-click path, prerequisites,
  reset procedure, and how to move the project to another PC.

## Dependency Behavior

The launcher runs editable installation with development dependencies from the
repository's `pyproject.toml`. This keeps the launcher aligned with the
project's declared dependencies and avoids maintaining a second dependency
list.

Installation runs on every launch so changes to project metadata are picked
up. Pip normally reuses already installed packages, making later launches much
faster than the first. A network connection may be required on first launch or
when dependencies change.

## Demo State and Reset

The launcher never overwrites an existing demo tournament. To reset the demo,
the user deletes `demo-data/launcher-demo.tgo.json` and launches again. To
rebuild dependencies, the user deletes `.venv` and launches again.

Generated demo data and `.venv` must be covered by `.gitignore` so testing
does not dirty the repository.

## Error Handling

Failures must identify the failed stage and return a nonzero exit code. The
launcher provides actionable messages for:

- Python missing or older than 3.12;
- virtual-environment creation failure;
- dependency installation failure;
- demo creation failure; and
- web-server startup failure.

The batch window pauses on failure. During a successful run, the terminal
remains attached to the server and tells the user to press `Ctrl+C` to stop it.

## Testing

Automated tests inspect the launcher contract without downloading packages or
opening a browser. They verify that the batch entry point delegates safely,
that the PowerShell script uses relative paths and a local virtual environment,
that it preserves existing demo data, and that documentation describes setup
and reset behavior.

Manual verification uses a temporary demo path or disposable checkout to
confirm first-run setup, browser launch, server shutdown, repeat launch, and
clear failure output. The existing Python formatting, lint, typing, compilation,
and test gates must continue to pass.

## Non-goals

- Bundling Python with the repository
- Copying a virtual environment between computers
- Packaging a standalone executable or installer
- Supporting macOS or Linux launchers in this change
- Automatically deleting or overwriting tournament data
