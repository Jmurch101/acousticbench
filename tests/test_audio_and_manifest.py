from __future__ import annotations

from pathlib import Path

import numpy as np

from acousticbench.audio import load_wav, resample_linear, write_wav
from acousticbench.datasets.manifest import load_items


def test_wav_roundtrip(tmp_path: Path):
    source = np.array([0.0, 0.5, -0.5, 0.25], dtype=np.float64)
    path = tmp_path / "tone.wav"
    write_wav(path, source, 16000)
    loaded, sample_rate = load_wav(path)
    assert sample_rate == 16000
    assert loaded.shape == source.shape
    assert np.allclose(loaded, source, atol=1 / 32768)


def test_resample_keeps_duration():
    audio = np.ones(16000)
    resampled = resample_linear(audio, 16000, 8000)
    assert resampled.shape == (8000,)
    assert np.allclose(resampled, 1.0)


def test_class_folders_use_directory_names_as_labels(tmp_path: Path):
    write_wav(tmp_path / "tone" / "a.wav", np.array([0.1, -0.1]), 8000)
    write_wav(tmp_path / "noise" / "nested" / "b.wav", np.array([0.2, -0.2]), 8000)
    (tmp_path / "EXAMPLE.txt").write_text("not a class", encoding="utf-8")
    items = load_items(tmp_path, "class_folders")
    assert {(item.label, item.relpath) for item in items} == {
        ("tone", "tone/a.wav"),
        ("noise", "noise/nested/b.wav"),
    }


def test_csv_manifest(tmp_path: Path):
    write_wav(tmp_path / "audio" / "a.wav", np.array([0.1, 0.0]), 8000)
    (tmp_path / "manifest.csv").write_text(
        "path,label,split\naudio/a.wav,chirp,test\n",
        encoding="utf-8",
    )
    items = load_items(tmp_path, "csv")
    assert len(items) == 1
    assert items[0].label == "chirp"
    assert items[0].split == "test"
    assert items[0].path.is_file()
