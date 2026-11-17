"""Read dataset manifests.

class_folders layout:
    root/<label>/**/*.wav

csv layout:
    root/manifest.csv with columns path and label.
    Optional columns: split, domain.
    Paths are relative to the dataset root unless absolute.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

from acousticbench.audio import AUDIO_EXTENSIONS


@dataclass
class AudioItem:
    path: Path
    label: str
    split: str | None
    domain: str | None
    relpath: str
    target: float | None = None
    condition: str | None = None


def load_items(root: Path, layout: str) -> list[AudioItem]:
    root = root.expanduser().resolve()
    if not root.exists():
        raise ValueError(f"Dataset path does not exist: {root}")
    if not root.is_dir():
        raise ValueError(f"Dataset path is not a directory: {root}")
    if layout == "class_folders":
        items = _from_class_folders(root)
    elif layout == "csv":
        items = _from_csv(root)
    else:
        raise ValueError("Layout must be 'class_folders' or 'csv'.")
    if not items:
        raise ValueError(f"No WAV files found in {root} using layout '{layout}'.")
    return items


def summarize_items(items: list[AudioItem]) -> dict:
    counts: dict[str, int] = {}
    missing = 0
    for item in items:
        counts[item.label] = counts.get(item.label, 0) + 1
        if not item.path.is_file():
            missing += 1
    return {
        "n_items": len(items),
        "n_missing_files": missing,
        "label_counts": dict(sorted(counts.items())),
    }


def _from_class_folders(root: Path) -> list[AudioItem]:
    items: list[AudioItem] = []
    for label_dir in sorted(path for path in root.iterdir() if path.is_dir() and not path.name.startswith(".")):
        label = label_dir.name.strip()
        if not label or label.startswith("__"):
            continue
        files = [
            path
            for path in label_dir.rglob("*")
            if path.is_file() and path.suffix.lower() in AUDIO_EXTENSIONS and not path.name.startswith(".")
        ]
        for path in sorted(files):
            items.append(
                AudioItem(
                    path=path.resolve(),
                    label=label,
                    split=None,
                    domain=None,
                    relpath=path.resolve().relative_to(root).as_posix(),
                )
            )
    return items


def _from_csv(root: Path) -> list[AudioItem]:
    manifest = root / "manifest.csv"
    if not manifest.is_file():
        raise ValueError(f"CSV datasets need {manifest}.")
    items: list[AudioItem] = []
    with manifest.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise ValueError(f"{manifest} has no header row.")
        fields = {(name or "").strip().lower(): name for name in reader.fieldnames}
        path_key = _pick(fields, "path", "filepath", "file")
        label_key = _pick(fields, "label", "class", "category")
        target_key = _pick(fields, "t60", "target", "reference", "distance")
        if path_key is None or (label_key is None and target_key is None):
            raise ValueError(f"{manifest} needs a path column and a label or t60/target column.")
        split_key = _pick(fields, "split")
        domain_key = _pick(fields, "domain")
        condition_key = _pick(fields, "condition", "room", "room_type")
        for row in reader:
            raw_path = (row.get(path_key) or "").strip()
            label = (row.get(label_key) or "").strip() if label_key else ""
            raw_target = (row.get(target_key) or "").strip() if target_key else ""
            target = _parse_float(raw_target)
            if not label and target is not None:
                label = f"{target:.6f}"
            if not raw_path or not label:
                continue
            path = Path(raw_path)
            if not path.is_absolute():
                path = root / path
            split = (row.get(split_key) or "").strip() if split_key else ""
            domain = (row.get(domain_key) or "").strip() if domain_key else ""
            condition = (row.get(condition_key) or "").strip() if condition_key else ""
            resolved = path.resolve()
            try:
                relpath = resolved.relative_to(root).as_posix()
            except ValueError:
                relpath = resolved.as_posix()
            items.append(
                AudioItem(
                    path=resolved,
                    label=label,
                    split=split or None,
                    domain=domain or None,
                    relpath=relpath,
                    target=target,
                    condition=condition or None,
                )
            )
    return items


def _parse_float(value: str) -> float | None:
    if not value:
        return None
    try:
        return float(value)
    except ValueError:
        return None


def _pick(fields: dict[str, str], *names: str) -> str | None:
    for name in names:
        if name in fields:
            return fields[name]
    return None
