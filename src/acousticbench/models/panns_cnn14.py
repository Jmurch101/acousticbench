"""Pretrained PANNs Cnn14 tagger, used without training.

The weights are Cnn14_16k from Kong, Cao, Iqbal, Wang, Wang, and Plumbley,
IEEE/ACM TASLP 2020. Zenodo record 3987831. The checkpoint is CC BY 4.0.
The inference code is MIT. This is not a sponsor checkpoint, and the team
did not train it.

The 527 AudioSet scores are collapsed with a fixed name map. That map was
chosen from the AudioSet label names. It was not fit to ACE or to OpenSLR.
"""

from __future__ import annotations

import csv
import shutil
from pathlib import Path

import numpy as np

from acousticbench.models.base import AcousticModel, Prediction
from acousticbench.paths import find_project_root

CHECKPOINT_NAME = "Cnn14_16k_mAP=0.438.pth"
CHECKPOINT_BYTES = 358_668_570
SAMPLE_RATE = 16000
CLASSES = 527

NOISE_GROUPS = {
    "babble": (
        "Speech",
        "Conversation",
        "Babbling",
        "Chatter",
        "Crowd",
        "Hubbub, speech noise, speech babble",
    ),
    "fan": ("Mechanical fan", "Air conditioning"),
    "ambient": (
        "Silence",
        "Inside, small room",
        "Inside, large room or hall",
        "White noise",
        "Pink noise",
    ),
}
ROOM_SMALL = "Inside, small room"
ROOM_LARGE = "Inside, large room or hall"

_CACHE: dict[str, tuple] = {}


class PannsNoiseType(AcousticModel):
    model_id = "panns-noise-type"
    name = "PANNs Cnn14 noise type"
    task = "classification"
    description = (
        "Pretrained AudioSet Cnn14 at 16 kHz. Speech-like tags map to babble, "
        "fan and air-conditioning tags map to fan, and silence, room, or noise "
        "tags map to ambient. The map was not fit to ACE. Not a sponsor checkpoint."
    )

    def load(self) -> None:
        _tagger(find_project_root())

    def get_info(self) -> dict:
        info = super().get_info()
        info.update(_public_info())
        info["label_map"] = "AudioSet names to ambient, babble, fan; not fit to ACE"
        info["classes"] = ["ambient", "babble", "fan"]
        return info

    def predict(self, audio, sample_rate: int) -> Prediction:
        clipwise, _names = _scores(audio, sample_rate)
        label, scores = noise_label(clipwise, load_label_names())
        return Prediction(label=label, scores=scores, extra={"method": self.model_id})


class PannsRoomSize(AcousticModel):
    model_id = "panns-room-size"
    name = "PANNs Cnn14 room size"
    task = "classification"
    description = (
        "Pretrained AudioSet Cnn14 at 16 kHz. Inside-small-room and "
        "inside-large-room tags map to small or large when one score is more "
        "than twice the other. Otherwise the label is medium. AudioSet has no "
        "medium-room tag. The network was trained on YouTube clips, not impulse responses."
    )

    def load(self) -> None:
        _tagger(find_project_root())

    def get_info(self) -> dict:
        info = super().get_info()
        info.update(_public_info())
        info["label_map"] = "Inside small/large room tags; medium when neither leads by 2x"
        info["classes"] = ["small", "medium", "large"]
        return info

    def predict(self, audio, sample_rate: int) -> Prediction:
        clipwise, _names = _scores(audio, sample_rate)
        label, scores = room_label(clipwise, load_label_names())
        return Prediction(label=label, scores=scores, extra={"method": self.model_id})


def load_label_names() -> list[str]:
    path = Path(__file__).with_name("audioset_labels.csv")
    names = [""] * CLASSES
    with path.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            names[int(row["index"])] = row["display_name"]
    if any(not name for name in names):
        raise ValueError(f"{path} does not contain {CLASSES} AudioSet names.")
    return names


def noise_label(clipwise, names: list[str]) -> tuple[str, dict[str, float]]:
    scores = _group_max(clipwise, names, NOISE_GROUPS)
    return _choose(scores, ("ambient", "babble", "fan")), scores


def room_label(clipwise, names: list[str]) -> tuple[str, dict[str, float]]:
    by_name = {name: float(clipwise[index]) for index, name in enumerate(names)}
    small = by_name[ROOM_SMALL]
    large = by_name[ROOM_LARGE]
    if small > 2.0 * large:
        label = "small"
    elif large > 2.0 * small:
        label = "large"
    else:
        label = "medium"
    scores = {"small": small, "large": large, "medium": min(small, large)}
    return label, scores


def _group_max(clipwise, names: list[str], groups: dict[str, tuple[str, ...]]) -> dict[str, float]:
    index = {name: position for position, name in enumerate(names)}
    missing = [name for group in groups.values() for name in group if name not in index]
    if missing:
        raise ValueError(f"AudioSet names missing from the label list: {missing}")
    return {
        label: float(max(clipwise[index[name]] for name in group))
        for label, group in groups.items()
    }


def _choose(scores: dict[str, float], order: tuple[str, ...]) -> str:
    best = order[0]
    for name in order[1:]:
        if scores[name] > scores[best]:
            best = name
    return best


def _scores(audio, sample_rate: int):
    if int(sample_rate) != SAMPLE_RATE:
        raise ValueError(f"PANNs Cnn14_16k expects {SAMPLE_RATE} Hz, got {sample_rate}.")
    signal = np.asarray(audio, dtype=np.float32).reshape(-1)
    if signal.size < 512:
        signal = np.pad(signal, (0, 512 - signal.size))
    model, names = _tagger(find_project_root())
    import torch

    waveform = torch.from_numpy(signal).unsqueeze(0)
    with torch.no_grad():
        output = model(waveform, None)
    clipwise = output["clipwise_output"].detach().cpu().numpy()[0]
    return clipwise, names


def _tagger(project_root: Path):
    path = project_root / "data" / "models" / CHECKPOINT_NAME
    key = str(path.resolve()) if path.exists() else str(path)
    cached = _CACHE.get(key)
    if cached is not None:
        return cached
    if not path.is_file() or path.stat().st_size != CHECKPOINT_BYTES:
        size = path.stat().st_size if path.is_file() else 0
        raise ValueError(
            "PANNs Cnn14_16k checkpoint is missing or incomplete "
            f"({size} bytes, expected {CHECKPOINT_BYTES}). Download "
            "Cnn14_16k_mAP=0.438.pth from https://zenodo.org/records/3987831 "
            f"into {path.parent}. Do not commit the file."
        )
    _ensure_panns_package_labels()
    import torch
    from panns_inference.models import Cnn14

    model = Cnn14(
        sample_rate=SAMPLE_RATE,
        window_size=512,
        hop_size=160,
        mel_bins=64,
        fmin=50,
        fmax=8000,
        classes_num=CLASSES,
    )
    blob = torch.load(path, map_location="cpu", weights_only=False)
    state = blob["model"] if isinstance(blob, dict) and "model" in blob else blob
    state = {
        (key_name[7:] if key_name.startswith("module.") else key_name): value
        for key_name, value in state.items()
    }
    model.load_state_dict(state)
    model.eval()
    for parameter in model.parameters():
        parameter.requires_grad_(False)
    names = load_label_names()
    _CACHE[key] = (model, names)
    return _CACHE[key]


def _ensure_panns_package_labels() -> None:
    """The installed package downloads labels with wget, which Windows does not have."""
    destination = Path.home() / "panns_data" / "class_labels_indices.csv"
    if destination.is_file() and destination.stat().st_size > 1000:
        return
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(Path(__file__).with_name("audioset_labels.csv"), destination)


def _public_info() -> dict:
    return {
        "checkpoint": CHECKPOINT_NAME,
        "checkpoint_bytes": CHECKPOINT_BYTES,
        "sample_rate": SAMPLE_RATE,
        "license": "CC BY 4.0 weights; MIT inference code",
        "url": "https://zenodo.org/records/3987831",
        "citation": "Kong, Cao, Iqbal, Wang, Wang, and Plumbley, IEEE/ACM TASLP, 2020",
        "trained_by_team": False,
        "sponsor_checkpoint": False,
    }
