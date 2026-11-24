"""Synthesized ambient, babble, and fan clips for the simulated side.

These are not room recordings and not a sponsor simulator. They only check
that the noise-type rule fires on signals built from its class definitions.
"""

from __future__ import annotations

import csv
from pathlib import Path

import numpy as np

from acousticbench.audio import write_wav
from acousticbench.eval.store import Store
from acousticbench.service import add_dataset

SAMPLE_RATE = 16000
SECONDS = 2.0
PER_CLASS = 8
DATASET_ID = "synth-noise-types"
CLASSES = ("ambient", "babble", "fan")


def generate_noise_dataset(project_root: Path, store: Store, seed: int = 7) -> dict:
    folder = project_root / "data" / "simulated" / DATASET_ID
    audio_dir = folder / "audio"
    audio_dir.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(seed)
    rows = []
    for label in CLASSES:
        for index in range(1, PER_CLASS + 1):
            audio = _clip(label, rng)
            name = f"{label}_{index:02d}.wav"
            write_wav(audio_dir / name, audio, SAMPLE_RATE)
            rows.append((f"audio/{name}", label))
    manifest = folder / "manifest.csv"
    with manifest.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["path", "label", "condition", "split"])
        for path, label in rows:
            writer.writerow([path, label, label, "dev"])
    (folder / "SIMULATED.txt").write_text(
        "SYNTHESIZED DEVELOPMENT AUDIO\n"
        "Ambient, babble, and fan clips generated in NumPy.\n"
        "Not a room recording, not Pyroomacoustics, and not a sponsor export.\n"
        "The labels are the class the generator was asked to make.\n"
        f"sample rate {SAMPLE_RATE}; seed {seed}; {PER_CLASS} files per class.\n",
        encoding="utf-8",
    )
    return add_dataset(
        store,
        {
            "id": DATASET_ID,
            "name": "Synthesized noise-type clips",
            "domain": "simulated",
            "layout": "csv",
            "root_path": folder,
            "description": (
                "Short synthesized ambient, babble, and fan clips. The label is the "
                "class the generator created. This is the simulated side of the sound-type "
                "task. It is not a measured room and not SoundSpaces, Steam Audio, or Unreal."
            ),
            "is_example": False,
            "synthetic_stand_in": False,
            "metadata": {
                "simulator": "numpy",
                "sample_rate": SAMPLE_RATE,
                "seed": seed,
                "synthetic": True,
                "classes": list(CLASSES),
            },
        },
        allow_example_flags=True,
    )


def _clip(label: str, rng: np.random.Generator) -> np.ndarray:
    count = int(SAMPLE_RATE * SECONDS)
    noise = rng.normal(0.0, 1.0, count)
    if label == "babble":
        audio = noise
    elif label == "ambient":
        audio = _bandlimit(noise, SAMPLE_RATE, 120.0)
    elif label == "fan":
        audio = _bandlimit(noise, SAMPLE_RATE, 450.0)
    else:
        raise ValueError(f"Unknown noise class '{label}'.")
    peak = float(np.max(np.abs(audio))) or 1.0
    return 0.5 * audio / peak


def _bandlimit(signal: np.ndarray, sample_rate: int, high_hz: float) -> np.ndarray:
    spectrum = np.fft.rfft(signal)
    freqs = np.fft.rfftfreq(signal.size, d=1.0 / float(sample_rate))
    spectrum[freqs > high_hz] = 0.0
    return np.fft.irfft(spectrum, n=signal.size)
