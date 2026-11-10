"""Shared locations for test output. Everything a test writes goes under tasks/test-artifacts/ (git-ignored),
so running the gate never rewrites tracked files."""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "tasks" / "test-artifacts"


def artifact_dir(name):
    path = ARTIFACTS / name
    path.mkdir(parents=True, exist_ok=True)
    return path


def require_current_build():
    """Tests run against the committed build; they never rebuild index.html themselves."""
    subprocess.run([sys.executable, str(ROOT / "tasks" / "build.py"), "--check"], cwd=ROOT, check=True)


def relative(path):
    try:
        return str(Path(path).resolve().relative_to(ROOT))
    except ValueError:
        return Path(path).name
