"""Runtime details stored with every evaluation run."""

from __future__ import annotations

import platform
import subprocess
import sys
from pathlib import Path

from acousticbench import __version__


def collect_provenance(project_root: Path) -> dict:
    return {
        "acousticbench_version": __version__,
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "git_revision": _git_revision(project_root),
    }


def _git_revision(project_root: Path) -> str | None:
    try:
        completed = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=project_root,
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    revision = completed.stdout.strip()
    return revision or None
