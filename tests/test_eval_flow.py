from __future__ import annotations

from pathlib import Path

import numpy as np

from acousticbench.eval.runner import execute_run
from acousticbench.eval.store import Store
from acousticbench.examples_data import SEED, generate_example_datasets, synthesize
from acousticbench.models.example_spectral import ExampleSpectralClassifier
from acousticbench.paths import database_path
from acousticbench.report import run_report_markdown
from acousticbench.service import add_dataset, queue_run


def test_clean_example_signals_match_their_class():
    rng = np.random.default_rng(SEED)
    model = ExampleSpectralClassifier()
    for _ in range(6):
        for kind in ("tone", "noise", "chirp"):
            prediction = model.predict(synthesize(kind, rng), 16000)
            assert prediction.label == kind
            assert prediction.scores is not None
            assert abs(sum(prediction.scores.values()) - 1.0) < 1e-6
            assert max(prediction.scores, key=prediction.scores.get) == kind


def test_constant_model_accuracy_is_the_true_class_share(tmp_path: Path):
    from acousticbench.audio import write_wav

    root = tmp_path / "project"
    audio_root = root / "audio"
    for index in range(3):
        write_wav(audio_root / "tone" / f"{index}.wav", np.sin(np.linspace(0, 20, 1600)), 16000)
    write_wav(audio_root / "noise" / "0.wav", np.linspace(-0.2, 0.2, 1600), 16000)
    store = Store(database_path(root))
    add_dataset(
        store,
        {
            "name": "Tiny set",
            "domain": "simulated",
            "layout": "class_folders",
            "root_path": audio_root,
            "description": "Unit-test audio",
        },
    )
    run = queue_run(
        store,
        root,
        model_id="constant-label",
        dataset_id="tiny-set",
        raw_config={"model_params": {"label": "tone"}, "max_seconds": 5, "sample_rate": 16000},
    )
    finished = execute_run(store, run["id"], root)
    assert finished["status"] == "completed"
    assert finished["summary"]["n_evaluated"] == 4
    assert finished["summary"]["n_correct"] == 3
    assert finished["summary"]["accuracy"] == 0.75
    assert Path(finished["predictions_path"]).is_file()

    capped = queue_run(
        store,
        root,
        model_id="constant-label",
        dataset_id="tiny-set",
        raw_config={"model_params": {"label": "tone"}, "max_items": 1},
    )
    capped_done = execute_run(store, capped["id"], root)
    assert capped_done["summary"]["n_evaluated"] == 1


def test_generated_examples_are_marked_synthetic(tmp_path: Path):
    root = tmp_path / "project"
    root.mkdir()
    store = Store(database_path(root))
    records = generate_example_datasets(root, store)
    by_id = {record["id"]: record for record in records}
    assert by_id["example-sim-clean"]["domain"] == "simulated"
    assert by_id["example-sim-clean"]["is_example"] is True
    assert by_id["example-synthetic-realish"]["domain"] == "real"
    assert by_id["example-synthetic-realish"]["synthetic_stand_in"] is True
    notice = Path(by_id["example-synthetic-realish"]["root_path"]) / "EXAMPLE.txt"
    assert "NOT a real recording".lower() in notice.read_text(encoding="utf-8").lower() or "Not a real recording" in notice.read_text(encoding="utf-8")
    run = queue_run(
        store,
        root,
        model_id="example-spectral",
        dataset_id="example-sim-clean",
        raw_config={"max_items": 3},
    )
    finished = execute_run(store, run["id"], root)
    assert finished["status"] == "completed"
    report = run_report_markdown(finished)
    assert "not real-world experimental results" in report.lower() or "not real-world" in report.lower()


def test_missing_dataset_path_is_rejected(tmp_path: Path):
    store = Store(database_path(tmp_path))
    try:
        add_dataset(
            store,
            {
                "name": "Missing",
                "domain": "real",
                "layout": "class_folders",
                "root_path": tmp_path / "does-not-exist",
                "description": "",
            },
        )
    except ValueError as exc:
        assert "does not exist" in str(exc)
    else:
        raise AssertionError("missing path should be rejected")
