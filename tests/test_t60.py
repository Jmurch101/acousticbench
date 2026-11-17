from __future__ import annotations

from pathlib import Path

import numpy as np

from acousticbench.audio import write_wav
from acousticbench.eval.runner import execute_run
from acousticbench.eval.store import Store
from acousticbench.metrics import regression_metrics
from acousticbench.models.schroeder_t60 import SchroederT60Model, estimate_t60
from acousticbench.paths import database_path
from acousticbench.service import add_dataset, queue_run


def _exponential(t60: float, sample_rate: int = 16000, seconds: float = 1.5) -> np.ndarray:
    times = np.arange(int(sample_rate * seconds), dtype=np.float64) / sample_rate
    # Amplitude decay of 60 dB over t60 seconds.
    return np.exp(-6.90775527898 * times / t60)


def test_schroeder_recovers_a_known_exponential_decay():
    estimate = estimate_t60(_exponential(0.4), 16000)
    assert abs(estimate - 0.4) < 0.03


def test_regression_metrics_match_hand_calculation():
    summary = regression_metrics([1.0, 2.0], [1.5, 2.0], task="t60", unit="seconds")
    assert summary["mae"] == 0.25
    assert abs(summary["rmse"] - (0.125 ** 0.5)) < 1e-12
    assert summary["task"] == "t60"


def test_t60_run_records_mae(tmp_path: Path):
    root = tmp_path / "project"
    audio_root = root / "rirs"
    write_wav(audio_root / "a.wav", _exponential(0.3), 16000)
    write_wav(audio_root / "b.wav", _exponential(0.6), 16000)
    (audio_root / "manifest.csv").write_text(
        "path,t60,condition\na.wav,0.3,small\nb.wav,0.6,large\n",
        encoding="utf-8",
    )
    store = Store(database_path(root))
    add_dataset(
        store,
        {
            "name": "Exponential RIRs",
            "domain": "simulated",
            "layout": "csv",
            "root_path": audio_root,
            "description": "Unit-test impulse responses with known T60. Not a room simulation.",
        },
    )
    run = queue_run(
        store,
        root,
        model_id="schroeder-t60",
        dataset_id="exponential-rirs",
        raw_config={"sample_rate": 16000, "max_seconds": 5},
    )
    assert run["config"]["task"] == "t60"
    finished = execute_run(store, run["id"], root)
    assert finished["status"] == "completed", finished["error"]
    assert finished["summary"]["task"] == "t60"
    assert finished["summary"]["mae"] < 0.05
    assert finished["summary"]["by_condition"]["small"]["n"] == 1
    assert finished["summary"]["provenance"]["acousticbench_version"]
    assert SchroederT60Model().get_info()["task"] == "t60"
