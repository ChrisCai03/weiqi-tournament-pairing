from pathlib import Path


def test_run_local_launcher_exists_and_uses_expected_commands() -> None:
    root = Path(__file__).resolve().parents[2]
    launcher = root / "run_local.bat"

    assert launcher.exists(), "Expected run_local.bat at the repository root."

    content = launcher.read_text(encoding="utf-8")

    assert "PYTHONPATH=src" in content
    assert ".tmp\\demo.tgo.json" in content
    assert "python -m pairing.cli.main demo" in content
    assert "127.0.0.1" in content
    assert "8123" in content
    assert "--open-browser" in content


def test_run_local_launcher_normalizes_argument_before_changing_directory() -> None:
    root = Path(__file__).resolve().parents[2]
    launcher = (root / "run_local.bat").read_text(encoding="utf-8").splitlines()

    cd_line = next(i for i, line in enumerate(launcher) if line.startswith("cd /d "))
    arg_line = next(i for i, line in enumerate(launcher) if "TOURNAMENT_PATH=%~f1" in line)
    default_line = next(i for i, line in enumerate(launcher) if "TOURNAMENT_PATH=.tmp\\demo.tgo.json" in line)
    web_line = next(i for i, line in enumerate(launcher) if "python -m pairing.cli.main web" in line)

    assert arg_line < cd_line, "The launcher must normalize %~1 before changing directories."
    assert default_line > cd_line, "The default demo path should be chosen after entering the repo root."
    assert "%TOURNAMENT_PATH%" in launcher[web_line]
