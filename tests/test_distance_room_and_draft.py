from pathlib import Path

import numpy as np

from acousticbench.ace_prepare import room_family
from acousticbench.audio import write_wav
from acousticbench.datasets.manifest import load_items
from acousticbench.models.direct_path_distance import SPEED_OF_SOUND_M_S, estimate_distance
from acousticbench.models.room_rule import T60RoomRuleModel
from acousticbench.models.schroeder_t60 import estimate_t60
from acousticbench.report import draft_report_markdown


def _exponential(t60: float, sample_rate: int = 16000, seconds: float = 1.5) -> np.ndarray:
    times = np.arange(int(sample_rate * seconds), dtype=np.float64) / sample_rate
    return np.exp(-6.90775527898 * times / t60)


def test_direct_path_distance_uses_onset_and_343_m_s():
    audio = np.zeros(16000)
    audio[160] = 1.0
    expected = 160 / 16000 * SPEED_OF_SOUND_M_S
    assert abs(estimate_distance(audio, 16000) - expected) < 1e-9


def test_room_rule_follows_the_fixed_bands():
    model = T60RoomRuleModel()
    assert model.predict(_exponential(0.35), 16000).label == "office"
    assert model.predict(_exponential(0.65), 16000).label == "meeting"
    assert model.predict(_exponential(1.0), 16000).label == "lecture"
    assert abs(estimate_t60(_exponential(0.35), 16000) - 0.35) < 0.03


def test_manifest_keeps_t60_and_distance_separate(tmp_path: Path):
    write_wav(tmp_path / "a.wav", np.array([0.1, 0.0]), 8000)
    (tmp_path / "manifest.csv").write_text(
        "path,t60,distance,label\na.wav,0.4,1.25,office\n",
        encoding="utf-8",
    )
    item = load_items(tmp_path, "csv")[0]
    assert item.label == "office"
    assert item.t60 == 0.4
    assert item.distance == 1.25


def test_room_family_collapses_ace_names():
    assert room_family("Office_2") == "office"
    assert room_family("Meeting_Room_1") == "meeting"
    assert room_family("Lecture_Room_2") == "lecture"
    assert room_family("Building_Lobby") == "lobby"


def test_draft_report_copies_run_ids_and_scores():
    run = {
        "id": "run-sim",
        "summary": {
            "n_evaluated": 4,
            "mae": 0.1,
            "rmse": 0.2,
            "median_ae": 0.05,
            "unit": "meters",
            "provenance": {"acousticbench_version": "0.1.0", "python": "3.14.3", "sample_rate": 16000, "dataset": {"image_order": 40}},
        },
    }
    other = {"id": "run-real", "summary": {}}
    room = {"id": "run-room", "summary": {}}
    comparison = {"metrics": [{"label": "Mean absolute error", "simulated": 0.1, "real": 0.2, "gap": 0.1}], "warnings": []}
    text = draft_report_markdown(
        t60_comparison=comparison,
        t60_simulated=run,
        t60_real=other,
        room_comparison=comparison,
        room_simulated=room,
        room_real={"id": "run-room-real", "summary": {}},
        distance_run=run,
    )
    assert "run-sim" in text
    assert "0.1000" in text or "0.1" in text
    assert "not the submitted final report" in text.lower()
