"""Closed-set classification metrics.

Assumption: one true label and one predicted label per audio item.
Macro averages include every class that appears as a true label or a prediction.
Weighted F1 weights classes by their true-label support.
"""

from __future__ import annotations

import math

import numpy as np


def classification_metrics(
    y_true: list[str],
    y_pred: list[str],
    confidences: list[float | None] | None = None,
    latencies_ms: list[float] | None = None,
) -> dict:
    if len(y_true) != len(y_pred):
        raise ValueError("True labels and predictions must have the same length.")
    if not y_true:
        raise ValueError("At least one evaluated item is required.")

    labels = sorted(set(y_true) | set(y_pred))
    index = {label: i for i, label in enumerate(labels)}
    counts = np.zeros((len(labels), len(labels)), dtype=int)
    for truth, pred in zip(y_true, y_pred):
        counts[index[truth], index[pred]] += 1

    per_class: dict[str, dict[str, float | int]] = {}
    f1_values: list[float] = []
    precision_values: list[float] = []
    recall_values: list[float] = []
    weighted_sum = 0.0
    support_total = 0
    for label in labels:
        i = index[label]
        tp = int(counts[i, i])
        support = int(counts[i, :].sum())
        predicted = int(counts[:, i].sum())
        precision = _div(tp, predicted)
        recall = _div(tp, support)
        f1 = _f1(precision, recall)
        per_class[label] = {
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "support": support,
        }
        precision_values.append(precision)
        recall_values.append(recall)
        f1_values.append(f1)
        weighted_sum += f1 * support
        support_total += support

    correct = int(np.trace(counts))
    total = int(counts.sum())
    confidence_values = _aligned_confidences(y_pred, confidences)
    correct_flags = [truth == pred for truth, pred in zip(y_true, y_pred)]
    ece, ece_count = _expected_calibration_error(confidence_values, correct_flags)
    latency = _latency_summary(latencies_ms or [])

    return {
        "task": "classification",
        "n_evaluated": total,
        "n_correct": correct,
        "accuracy": _div(correct, total),
        "macro_precision": float(np.mean(precision_values)),
        "macro_recall": float(np.mean(recall_values)),
        "macro_f1": float(np.mean(f1_values)),
        "weighted_f1": _div(weighted_sum, support_total),
        "labels": labels,
        "per_class": per_class,
        "confusion_matrix": {"labels": labels, "counts": counts.tolist()},
        "mean_latency_ms": latency["mean"],
        "p50_latency_ms": latency["p50"],
        "p95_latency_ms": latency["p95"],
        "ece": ece,
        "ece_count": ece_count,
    }


def _div(numerator: float, denominator: float) -> float:
    if denominator == 0:
        return 0.0
    return float(numerator) / float(denominator)


def _f1(precision: float, recall: float) -> float:
    if precision + recall == 0:
        return 0.0
    return 2.0 * precision * recall / (precision + recall)


def _aligned_confidences(
    y_pred: list[str], confidences: list[float | None] | None
) -> list[float | None]:
    if confidences is None:
        return [None] * len(y_pred)
    if len(confidences) != len(y_pred):
        raise ValueError("Confidence values must align with predictions.")
    cleaned: list[float | None] = []
    for value in confidences:
        if value is None:
            cleaned.append(None)
            continue
        number = float(value)
        if math.isnan(number) or number < 0.0 or number > 1.0:
            cleaned.append(None)
        else:
            cleaned.append(number)
    return cleaned


def _expected_calibration_error(
    confidences: list[float | None], correct: list[bool], n_bins: int = 10
) -> tuple[float | None, int]:
    pairs = [(conf, flag) for conf, flag in zip(confidences, correct) if conf is not None]
    if not pairs:
        return None, 0
    conf = np.array([pair[0] for pair in pairs], dtype=np.float64)
    hits = np.array([1.0 if pair[1] else 0.0 for pair in pairs], dtype=np.float64)
    edges = np.linspace(0.0, 1.0, n_bins + 1)
    total = len(pairs)
    ece = 0.0
    for index in range(n_bins):
        low, high = edges[index], edges[index + 1]
        if index == n_bins - 1:
            mask = (conf >= low) & (conf <= high)
        else:
            mask = (conf >= low) & (conf < high)
        count = int(mask.sum())
        if count == 0:
            continue
        ece += (count / total) * abs(float(hits[mask].mean()) - float(conf[mask].mean()))
    return float(ece), total


def _latency_summary(latencies_ms: list[float]) -> dict[str, float | None]:
    if not latencies_ms:
        return {"mean": None, "p50": None, "p95": None}
    values = np.array(latencies_ms, dtype=np.float64)
    return {
        "mean": float(np.mean(values)),
        "p50": float(np.percentile(values, 50)),
        "p95": float(np.percentile(values, 95)),
    }
