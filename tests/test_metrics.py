from __future__ import annotations

from acousticbench.metrics import classification_metrics


def test_perfect_predictions_score_one():
    metrics = classification_metrics(
        ["tone", "noise", "tone"],
        ["tone", "noise", "tone"],
        [1.0, 1.0, 1.0],
        [1.0, 2.0, 3.0],
    )
    assert metrics["accuracy"] == 1.0
    assert metrics["macro_f1"] == 1.0
    assert metrics["n_correct"] == 3
    assert metrics["per_class"]["noise"]["support"] == 1
    assert metrics["ece"] == 0.0
    assert metrics["mean_latency_ms"] == 2.0


def test_wrong_high_confidence_is_poorly_calibrated():
    metrics = classification_metrics(["tone"], ["noise"], [1.0], [4.0])
    assert metrics["accuracy"] == 0.0
    assert metrics["ece"] == 1.0
    labels = metrics["confusion_matrix"]["labels"]
    counts = metrics["confusion_matrix"]["counts"]
    true_index = labels.index("tone")
    pred_index = labels.index("noise")
    assert counts[true_index][pred_index] == 1


def test_macro_f1_includes_a_class_that_was_only_predicted():
    metrics = classification_metrics(["tone", "tone"], ["tone", "noise"])
    assert metrics["accuracy"] == 0.5
    assert "noise" in metrics["per_class"]
    assert metrics["per_class"]["noise"]["support"] == 0
    assert metrics["per_class"]["noise"]["precision"] == 0.0
