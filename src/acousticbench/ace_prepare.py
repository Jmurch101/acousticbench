"""Build a local ACE T60 manifest without copying or modifying the audio.

The single-channel archive is the cruciform channel-1 recording. Fullband T60
labels come from the corpus mean table, Crucif channel 1. Audio stays in
data/ace, which is gitignored.
"""

from __future__ import annotations

import csv
import re
import tarfile
from pathlib import Path

from acousticbench.audio import AUDIO_EXTENSIONS
from acousticbench.eval.store import Store
from acousticbench.service import add_dataset

DATASET_ID = "ace-single-rir"
NOISE_DATASET_ID = "ace-noise-types"
MEAN_TABLE = "20150814T154139_Corpus_Mean_DRRs_and_T60s.csv"
ARCHIVE_NAME = "ACE_Corpus_RIRN_Single.tbz2"
NOISE_WORDS = ("ambient", "babble", "fan", "noise")


def prepare_ace_dataset(project_root: Path, store: Store) -> dict:
    downloads = project_root / "data" / "ace" / "downloads"
    archive = downloads / ARCHIVE_NAME
    if not archive.is_file() or archive.stat().st_size < 400_000_000:
        raise ValueError(
            "ACE single-channel archive is missing. Download "
            "ACE_Corpus_RIRN_Single.tbz2 from https://doi.org/10.5281/zenodo.6257551 "
            f"into {downloads}."
        )
    extracted = project_root / "data" / "ace" / "single"
    if not any(extracted.rglob("*.wav")):
        extracted.mkdir(parents=True, exist_ok=True)
        with tarfile.open(archive, "r:bz2") as tar:
            tar.extractall(extracted, filter="data")
    table = _find_mean_table(project_root)
    labels = load_crucif_channel1_t60(table)
    wavs = [
        path
        for path in extracted.rglob("*")
        if path.is_file() and path.suffix.lower() in AUDIO_EXTENSIONS and "rir" in path.stem.lower()
    ]
    matched = []
    unmatched = []
    for path in sorted(wavs):
        label = match_rir_filename(path.name, labels)
        if label is None:
            unmatched.append(path.name)
            continue
        matched.append((path, label))
    if not matched:
        preview = ", ".join(unmatched[:8]) or "no wav files contained 'rir'"
        raise ValueError(f"No ACE impulse responses matched the T60 table. Examples: {preview}")
    prepared = project_root / "data" / "ace" / "prepared"
    prepared.mkdir(parents=True, exist_ok=True)
    manifest = prepared / "manifest.csv"
    with manifest.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["path", "t60", "label", "condition", "split"])
        writer.writeheader()
        for path, label in matched:
            writer.writerow(
                {
                    "path": path.resolve().as_posix(),
                    "t60": f"{label['t60']:.6f}",
                    "label": room_family(label["room_name"]),
                    "condition": label["room_name"],
                    "split": "corpus",
                }
            )
    (prepared / "ACE_LICENSE.txt").write_text(
        "ACE Challenge corpus\n"
        "Zenodo: https://doi.org/10.5281/zenodo.6257551\n"
        "The Zenodo record lists CC BY 4.0. The Imperial College project page states CC BY-ND 4.0.\n"
        "This folder does not copy the audio. The manifest points at the extracted original files.\n"
        "Do not commit the audio. Cite Eaton, Gaubitch, Moore, and Naylor, IEEE/ACM TASLP, 2016.\n"
        "Labels are fullband T60 for Crucif channel 1 from "
        "20150814T154139_Corpus_Mean_DRRs_and_T60s.csv.\n"
        "The single-channel archive is the cruciform channel-1 set.\n",
        encoding="utf-8",
    )
    return add_dataset(
        store,
        {
            "id": DATASET_ID,
            "name": "ACE single-channel measured impulse responses",
            "domain": "real",
            "layout": "csv",
            "root_path": prepared,
            "description": (
                "Measured ACE Challenge impulse responses from the single-channel archive. "
                "Targets are published fullband T60 values for cruciform channel 1. "
                "The label column is the room family derived from the published room name. "
                "The mean table does not include source-to-microphone distance in meters. "
                "Cite Eaton et al. 2016. Audio is local only and is not part of the git repository."
            ),
            "metadata": {
                "source": "ACE Challenge",
                "doi": "10.5281/zenodo.6257551",
                "license_note": "Zenodo lists CC BY 4.0. Imperial College states CC BY-ND 4.0.",
                "microphone": "single, cruciform channel 1",
                "target": "fullband T60 seconds",
                "t60_table": MEAN_TABLE,
                "room_label": "family from Room decode: office, meeting, lecture, lobby",
                "distance_reference": "not in the ACE mean table",
            },
        },
        allow_example_flags=True,
    )


def prepare_ace_noise_dataset(project_root: Path, store: Store) -> dict:
    extracted = project_root / "data" / "ace" / "single"
    wavs = [
        path
        for path in extracted.rglob("*")
        if path.is_file() and path.suffix.lower() in AUDIO_EXTENSIONS and _noise_class(path.name)
    ]
    if not wavs:
        raise ValueError(
            "ACE noise files were not found. Run prepare-ace after the single-channel archive is extracted."
        )
    prepared = project_root / "data" / "ace" / "prepared-noise"
    prepared.mkdir(parents=True, exist_ok=True)
    manifest = prepared / "manifest.csv"
    with manifest.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["path", "label", "condition", "split"])
        writer.writeheader()
        for path in sorted(wavs):
            label = _noise_class(path.name)
            folder = path.parent.parent.name if path.parent.parent else path.parent.name
            writer.writerow(
                {
                    "path": path.resolve().as_posix(),
                    "label": label,
                    "condition": room_family(folder),
                    "split": "corpus",
                }
            )
    (prepared / "ACE_LICENSE.txt").write_text(
        "ACE Challenge noise clips from the single-channel archive.\n"
        "Labels are the filename classes ambient, babble, and fan. "
        "The archive does not provide event start and end times.\n"
        "Cite Eaton, Gaubitch, Moore, and Naylor, IEEE/ACM TASLP, 2016.\n"
        "Do not commit the audio.\n",
        encoding="utf-8",
    )
    return add_dataset(
        store,
        {
            "id": NOISE_DATASET_ID,
            "name": "ACE noise-type clips",
            "domain": "real",
            "layout": "csv",
            "root_path": prepared,
            "description": (
                "ACE ambient, babble, and fan recordings from the single-channel archive. "
                "The label is the class in the filename. These clips have no event times. "
                "Cite Eaton et al. 2016. Audio is local only."
            ),
            "metadata": {
                "source": "ACE Challenge",
                "doi": "10.5281/zenodo.6257551",
                "t60_table": "not used",
                "room_label": "folder name collapsed to office, meeting, lecture, lobby",
                "classes": "ambient, babble, fan",
            },
        },
        allow_example_flags=True,
    )


def _noise_class(filename: str) -> str | None:
    stem = Path(filename).stem.lower()
    if "rir" in stem:
        return None
    if "babble" in stem:
        return "babble"
    if "ambient" in stem:
        return "ambient"
    if "fan" in stem:
        return "fan"
    return None


def room_family(room_name: str) -> str:
    name = room_name.lower()
    if "office" in name:
        return "office"
    if "meeting" in name:
        return "meeting"
    if "lecture" in name:
        return "lecture"
    if "lobby" in name:
        return "lobby"
    return room_name


def load_crucif_channel1_t60(path: Path) -> list[dict]:
    labels = []
    seen = set()
    with path.open(encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            if _cell(row, "Mic config:") != "Crucif" or _cell(row, "Chan:") != "1":
                continue
            key = (_cell(row, "Room:"), _cell(row, "Room config:"))
            if key in seen:
                continue
            seen.add(key)
            labels.append(
                {
                    "room_code": key[0],
                    "room_name": _cell(row, "Room decode:"),
                    "config": key[1],
                    "t60": float(_cell(row, "FB T60:")),
                }
            )
    if not labels:
        raise ValueError(f"{path} has no Crucif channel-1 fullband T60 rows.")
    return labels


def match_rir_filename(filename: str, labels: list[dict]) -> dict | None:
    stem = Path(filename).stem.lower()
    if "rir" not in stem:
        return None
    if any(word in stem for word in NOISE_WORDS):
        return None
    compact = re.sub(r"[^a-z0-9]", "", stem)
    hits = []
    for label in labels:
        code = re.sub(r"[^a-z0-9]", "", label["room_code"].lower())
        name = re.sub(r"[^a-z0-9]", "", label["room_name"].lower())
        if code not in compact and name not in compact:
            continue
        if not re.search(rf"(^|[^a-z0-9]){re.escape(label['config'])}([^0-9]|$)", stem):
            continue
        hits.append(label)
    if len(hits) == 1:
        return hits[0]
    return None


def _find_mean_table(project_root: Path) -> Path:
    matches = list((project_root / "data" / "ace").rglob(MEAN_TABLE))
    if not matches:
        raise ValueError(
            "ACE mean T60 table is missing. Download ACE_Corpus_Data.tbz2 from Zenodo and extract it under data/ace."
        )
    return matches[0]


def _cell(row: dict, name: str) -> str:
    for key, value in row.items():
        if key and key.strip().rstrip(":") == name.rstrip(":"):
            return (value or "").strip()
    return ""
