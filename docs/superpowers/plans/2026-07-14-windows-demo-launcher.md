# Windows Demo Launcher Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a portable Windows launcher that builds a local environment, installs declared dependencies, creates persistent demo state, and opens the local web UI.

**Architecture:** A minimal root batch file delegates to a PowerShell orchestration script. Contract tests inspect both scripts without networking or browser side effects; existing CLI commands perform demo creation and server startup.

**Tech Stack:** Windows batch, PowerShell 5+, Python 3.12+, pytest, editable pip installation.

## Global Constraints

- Resolve all paths relative to the repository; never embed machine-specific paths.
- Require Python 3.12 or newer through `py` or `python`.
- Install into disposable repository-local `.venv`, never global Python.
- Preserve an existing `demo-data/launcher-demo.tgo.json`.
- Pause the batch window on failure and propagate nonzero exit status.
- Do not download dependencies or open a browser in automated tests.

---

### Task 1: Launcher contract and implementation

**Files:**
- Create: `tests/unit/test_windows_launcher.py`
- Create: `run-demo.bat`
- Create: `scripts/run-demo.ps1`
- Modify: `.gitignore`

**Interfaces:**
- Consumes: existing `pairing demo PATH` and `pairing web PATH --open-browser` CLI commands.
- Produces: `run-demo.bat` double-click entry point and `scripts/run-demo.ps1` orchestration script.

- [ ] **Step 1: Write failing contract tests**

Add tests that read the scripts and assert batch delegation via `%~dp0`, PowerShell root resolution via `$PSScriptRoot`, `.venv` Python use, `py -3.12`/`python` discovery, version validation, conditional demo creation, editable `.[dev]` installation, browser launch, and ignored generated paths.

- [ ] **Step 2: Verify the tests fail**

Run: `python -m pytest tests/unit/test_windows_launcher.py -q`

Expected: FAIL because the launcher files do not exist.

- [ ] **Step 3: Implement the minimal launcher**

Create a batch wrapper that calls PowerShell with execution-policy bypass and pauses only on failure. Create a PowerShell script with strict error handling, repository-relative paths, Python discovery/version validation, venv creation, pip installation, conditional demo creation, and foreground web startup. Add `.venv/` and `demo-data/` to `.gitignore`.

- [ ] **Step 4: Verify the launcher tests pass**

Run: `python -m pytest tests/unit/test_windows_launcher.py -q`

Expected: all launcher contract tests pass.

### Task 2: Portable usage documentation

**Files:**
- Modify: `tests/unit/test_windows_launcher.py`
- Modify: `README.md`
- Modify: `docs/tournament-trial-runbook.md`

**Interfaces:**
- Consumes: launcher paths and reset behavior from Task 1.
- Produces: discoverable instructions for first launch, shutdown, reset, and migration to another PC.

- [ ] **Step 1: Add failing documentation assertions**

Assert the README mentions `run-demo.bat`, Python 3.12, `.venv`, first-run network needs, `Ctrl+C`, and both reset paths; assert the runbook points trial users to the launcher.

- [ ] **Step 2: Verify the new assertions fail**

Run: `python -m pytest tests/unit/test_windows_launcher.py -q`

Expected: FAIL because documentation does not describe the launcher.

- [ ] **Step 3: Document use and portability**

Add a concise quick-launch section to README and an optional launcher path to the trial runbook. Explicitly say not to copy `.venv` between PCs and explain how to rebuild it.

- [ ] **Step 4: Verify focused tests pass**

Run: `python -m pytest tests/unit/test_windows_launcher.py -q`

Expected: all launcher contract and documentation tests pass.

### Task 3: Full verification

**Files:**
- Verify only; no planned production changes.

**Interfaces:**
- Consumes: completed launcher and documentation.
- Produces: current quality-gate evidence.

- [ ] **Step 1: Parse the PowerShell script without running setup**

Run PowerShell's parser against `scripts/run-demo.ps1` and require zero syntax errors.

- [ ] **Step 2: Run all project gates**

Run Ruff format check, Ruff lint, mypy, compileall, and the complete pytest coverage suite.

Expected: formatting and lint pass, mypy reports no issues, compilation passes, all tests pass, and coverage remains at least 90%.

- [ ] **Step 3: Review the final diff and repository state**

Confirm only launcher-related files and approved documentation changed. Preserve the pre-existing deletion of `MAINTENANCE.md` and untracked `opengotha/` tree without modification.
