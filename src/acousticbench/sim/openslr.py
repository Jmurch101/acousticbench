"""Register a subset of the OpenSLR simulated room impulse responses.

Ko, Peddinti, Povey, Seltzer, and Khudanpur, ICASSP 2017. The archive is
OpenSLR 26, Apache 2.0. Rooms are grouped by floor size: small (1–10 m),
medium (10–30 m), and large (30–50 m). The archive publishes length, width,
height, and one absorption coefficient per room. It does not publish T60.
The t60 column here is Sabine's formula on those published numbers.

Only 12 rooms from each size group are extracted. The full archive is about
2.2 GB uncompressed and stays in the zip.
"""

from __future__ import annotations

import csv
import json
import zipfile
from pathlib import Path

from acousticbench.eval.store import Store
from acousticbench.service import add_dataset
from acousticbench.sim.sabine import sabine_t60

DATASET_ID = "openslr-sim-rir"
ARCHIVE_NAME = "sim_rir_16k.zip"
PER_SIZE = 12
SIZES = (
    ("small", "smallroom"),
    ("medium", "mediumroom"),
    ("large", "largeroom"),
)


def prepare_openslr_dataset(project_root: Path, store: Store) -> dict:
    archive = project_root / "data" / "simulated" / "downloads" / ARCHIVE_NAME
    if not archive.is_file() or not zipfile.is_zipfile(archive):
        raise ValueError(
            "OpenSLR simulated impulse responses are missing. Download "
            "sim_rir_16k.zip from https://www.openslr.org/26/ "
            f"into {archive.parent}."
        )
    folder = project_root / "data" / "simulated" / DATASET_ID
    rows = _extract_subset(archive, folder)
    manifest = folder / "manifest.csv"
    with manifest.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["path", "t60", "label", "condition", "split"])
        for path, t60, label in rows:
            writer.writerow([path, f"{t60:.6f}", label, label, "dev"])
    (folder / "SIMULATED.txt").write_text(
        "SIMULATED ROOM IMPULSE RESPONSES\n"
        "OpenSLR 26, Apache 2.0.\n"
        "Ko, Peddinti, Povey, Seltzer, and Khudanpur, ICASSP 2017.\n"
        "https://www.openslr.org/26/\n"
        "Image method: Allen and Berkley, JASA, 1979, via Habets' RIR generator.\n"
        "The label is the archive size group: small, medium, or large.\n"
        "The t60 column is Sabine's formula from the published room length, width,\n"
        "height, and absorption coefficient. The archive does not print T60.\n"
        f"This manifest keeps the first impulse response from rooms 1 through {PER_SIZE} in each size group.\n"
        "The full archive is not extracted. Audio stays outside git.\n"
        "Not a sponsor SoundSpaces, Steam Audio, or Unreal export.\n",
        encoding="utf-8",
    )
    (folder / "metadata.json").write_text(
        json.dumps(
            {
                "simulator": "image-source, Habets RIR generator",
                "source": "OpenSLR 26",
                "license": "Apache-2.0",
                "url": "https://www.openslr.org/26/",
                "sample_rate": 16000,
                "room_label": "small, medium, large",
                "t60_reference": "sabine from published dimensions and absorption",
                "files": len(rows),
                "not_sponsor_dataset": True,
                "citation": "Ko, Peddinti, Povey, Seltzer, and Khudanpur, ICASSP 2017",
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return add_dataset(
        store,
        {
            "id": DATASET_ID,
            "name": "OpenSLR simulated room impulse responses",
            "domain": "simulated",
            "layout": "csv",
            "root_path": folder,
            "description": (
                "Image-source room impulse responses from OpenSLR 26. "
                "Labels are small, medium, and large. The t60 column is Sabine "
                "from the published dimensions and absorption. Apache 2.0. "
                "Cite Ko et al., ICASSP 2017. Not a sponsor SoundSpaces or Steam Audio export."
            ),
            "is_example": False,
            "synthetic_stand_in": False,
            "metadata": {
                "simulator": "image-source, Habets RIR generator",
                "source": "OpenSLR 26",
                "license": "Apache-2.0",
                "url": "https://www.openslr.org/26/",
                "sample_rate": 16000,
                "room_label": "small, medium, large",
                "t60_reference": "sabine from published dimensions and absorption",
            },
        },
        allow_example_flags=True,
    )


def _extract_subset(archive: Path, folder: Path) -> list[tuple[str, float, str]]:
    audio = folder / "rir"
    audio.mkdir(parents=True, exist_ok=True)
    rows: list[tuple[str, float, str]] = []
    with zipfile.ZipFile(archive) as bundle:
        for label, group in SIZES:
            rooms = _room_table(bundle.read(f"simulated_rirs_16k/{group}/room_info").decode())
            for number in range(1, PER_SIZE + 1):
                room = f"Room{number:03d}"
                key = f"{label}-{room}"
                if key not in rooms:
                    raise ValueError(f"OpenSLR room_info has no entry for {key}.")
                member = f"simulated_rirs_16k/{group}/{room}/{room}-00001.wav"
                dest_name = f"{label}_{room}.wav"
                dest = audio / dest_name
                if not dest.is_file() or dest.stat().st_size < 44:
                    dest.write_bytes(bundle.read(member))
                length, width, height, absorption = rooms[key]
                t60 = sabine_t60((length, width, height), absorption)
                rows.append((f"rir/{dest_name}", t60, label))
    if len(rows) != PER_SIZE * len(SIZES):
        raise ValueError(f"Expected {PER_SIZE * len(SIZES)} OpenSLR files, wrote {len(rows)}.")
    return rows


def _room_table(text: str) -> dict[str, tuple[float, float, float, float]]:
    rooms: dict[str, tuple[float, float, float, float]] = {}
    for line in text.splitlines():
        parts = line.split()
        if len(parts) < 8 or parts[0].startswith("#"):
            continue
        length, width, height = (float(parts[1]), float(parts[2]), float(parts[3]))
        absorption = float(parts[7])
        rooms[parts[0]] = (length, width, height, absorption)
    return rooms
