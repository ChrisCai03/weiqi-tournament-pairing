from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def read_repo_file(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


def test_batch_launcher_delegates_from_its_own_directory() -> None:
    launcher = read_repo_file("run-demo.bat")

    assert "%~dp0" in launcher
    assert "scripts\\run-demo.ps1" in launcher
    assert "-ExecutionPolicy Bypass" in launcher
    assert "pause" in launcher.lower()


def test_powershell_launcher_uses_portable_local_environment() -> None:
    launcher = read_repo_file("scripts/run-demo.ps1")

    assert "$PSScriptRoot" in launcher
    assert 'Join-Path $repoRoot ".venv"' in launcher
    assert 'Join-Path $venvPath "Scripts\\python.exe"' in launcher
    assert '"-3.12"' in launcher
    assert 'Get-Command "python"' in launcher
    assert "sys.version_info" in launcher
    assert "Python 3.12 or newer" in launcher


def test_powershell_launcher_installs_and_preserves_demo_state() -> None:
    launcher = read_repo_file("scripts/run-demo.ps1")

    assert '"-m", "pip", "install", "-e", ".[dev]"' in launcher
    assert 'Join-Path $repoRoot "demo-data\\launcher-demo.tgo.json"' in launcher
    assert "if (-not (Test-Path -LiteralPath $demoPath))" in launcher
    assert '"-m", "pairing.cli.main", "demo", $demoPath' in launcher
    assert '"-m", "pairing.cli.main", "web", $demoPath, "--open-browser"' in launcher


def test_generated_launcher_state_is_ignored() -> None:
    gitignore = read_repo_file(".gitignore")

    assert ".venv/" in gitignore.splitlines()
    assert "demo-data/" in gitignore.splitlines()


def test_readme_documents_click_run_portability_and_reset() -> None:
    readme = read_repo_file("README.md")

    for expected in (
        "run-demo.bat",
        "Python 3.12",
        ".venv",
        "network connection",
        "Ctrl+C",
        "demo-data/launcher-demo.tgo.json",
        "another PC",
    ):
        assert expected in readme


def test_trial_runbook_points_to_the_windows_launcher() -> None:
    runbook = read_repo_file("docs/tournament-trial-runbook.md")

    assert "run-demo.bat" in runbook
    assert "launcher-demo.tgo.json" in runbook
