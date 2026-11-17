from __future__ import annotations

from acousticbench.compare import compare_runs


def _run(run_id: str, domain: str, accuracy: float, f1: float, n: int, example: bool = False) -> dict:
    return {
        "id": run_id,
        "status": "completed",
        "model_id": "example-spectral",
        "dataset_domain": domain,
        "config": {
            "sample_rate": 16000,
            "dataset_flags": {"is_example": example, "synthetic": example},
        },
        "summary": {
            "task": "classification",
            "n_evaluated": n,
            "accuracy": accuracy,
            "macro_f1": f1,
            "macro_precision": f1,
            "macro_recall": f1,
            "weighted_f1": f1,
            "ece": None,
            "mean_latency_ms": 1.0,
            "per_class": {
                "tone": {"f1": f1, "support": n},
            },
        },
    }


def test_gap_is_real_minus_simulated():
    comparison = compare_runs(
        _run("sim", "simulated", 0.9, 0.8, 20),
        _run("real", "real", 0.6, 0.5, 20),
    )
    accuracy = next(item for item in comparison["metrics"] if item["key"] == "accuracy")
    assert abs(accuracy["gap"] - -0.3) < 1e-9
    assert abs(comparison["per_class_f1"][0]["gap"] - -0.3) < 1e-9
    assert comparison["gap_definition"] == "gap = real - simulated"


def test_example_audio_adds_a_warning():
    comparison = compare_runs(
        _run("sim", "simulated", 1.0, 1.0, 4, example=True),
        _run("real", "real", 1.0, 1.0, 4, example=True),
    )
    assert any("synthetic" in warning.lower() or "example" in warning.lower() for warning in comparison["warnings"])
    assert any("unstable" in warning.lower() for warning in comparison["warnings"])


def test_incomplete_runs_cannot_be_compared():
    simulated = _run("sim", "simulated", 1.0, 1.0, 10)
    simulated["status"] = "failed"
    try:
        compare_runs(simulated, _run("real", "real", 1.0, 1.0, 10))
    except ValueError as exc:
        assert "completed" in str(exc)
    else:
        raise AssertionError("comparison should reject a failed run")
