"""Project paths. Commands are meant to be run from the repository root."""

from __future__ import annotations

import os
import sys
from pathlib import Path


def find_project_root(start: Path | None = None) -> Path:
    env = os.environ.get("ACOUSTIBENCH_HOME")
    if env:
        return Path(env).expanduser().resolve()
    current = (start or Path.cwd()).resolve()
    for candidate in [current, *current.parents]:
        marker = candidate / "pyproject.toml"
        package = candidate / "src" / "acousticbench"
        if marker.is_file() and package.is_dir():
            return candidate
    return current


def data_dir(root: Path | None = None) -> Path:
    path = (root or find_project_root()) / "data"
    path.mkdir(parents=True, exist_ok=True)
    return path


def database_path(root: Path | None = None) -> Path:
    return data_dir(root) / "acousticbench.db"


def runs_dir(root: Path | None = None) -> Path:
    path = data_dir(root) / "runs"
    path.mkdir(parents=True, exist_ok=True)
    return path


def prepare_runtime(project_root: Path) -> None:
    """Allow `user_models` in the project root to be imported by name."""
    root = str(project_root.resolve())
    if root not in sys.path:
        sys.path.insert(0, root)
