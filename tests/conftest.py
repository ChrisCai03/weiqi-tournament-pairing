import os
import tempfile
from pathlib import Path


def pytest_configure(config):
    temp_root = Path(__file__).resolve().parents[1] / ".tmp" / "pytest-temp" / str(os.getpid())
    temp_root.mkdir(parents=True, exist_ok=True)
    os.environ["TMP"] = str(temp_root)
    os.environ["TEMP"] = str(temp_root)
    tempfile.tempdir = None
