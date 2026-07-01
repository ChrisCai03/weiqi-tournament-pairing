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
