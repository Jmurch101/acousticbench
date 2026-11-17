"""Run one model over one dataset and store item-level predictions."""

from __future__ import annotations

import csv
import logging
import time
from pathlib import Path

from acousticbench.audio import load_wav, resample_linear
from acousticbench.eval.store import Store
from acousticbench.metrics import classification_metrics, regression_metrics
from acousticbench.provenance import collect_provenance
from acousticbench.models.base import Prediction
from acousticbench.models.registry import get_model, instantiate
from acousticbench.paths import runs_dir
from acousticbench.service import dataset_items
from acousticbench.util import jsonable

logger = logging.getLogger(__name__)


def execute_run(store: Store, run_id: str, project_root: Path) -> dict:
    run = store.get_run(run_id)
    store.mark_running(run_id)
    try:
        summary, predictions_path = _evaluate(store, run, project_root)
    except Exception as exc:
        logger.exception("Run %s failed", run_id)
        message = exc.args[0] if isinstance(exc, KeyError) and exc.args else str(exc)
        return store.finish_run(run_id, status="failed", error=str(message))
    return store.finish_run(
        run_id,
        status="completed",
        summary=jsonable(summary),
        predictions_path=str(predictions_path),
    )


def _evaluate(store: Store, run: dict, project_root: Path) -> tuple[dict, Path]:
    dataset = store.get_dataset(run["dataset_id"])
    items = dataset_items(dataset, run.get("config") or {})
    if not items:
        split = (run.get("config") or {}).get("split")
        raise RuntimeError(f"No audio items matched split '{split}'.")

    registered = store.list_registered_models()
    spec = get_model(project_root, run["model_id"], registered)
    model = instantiate(spec, run.get("model_params") or {})
    if hasattr(model, "load"):
        model.load()
    task = getattr(model, "task", "classification")
    if task not in {"classification", "t60", "distance"}:
        raise RuntimeError(
            f"Model '{spec.model_id}' declares task '{task}'. "
            "Supported tasks are classification, t60, and distance."
        )

    config = run.get("config") or {}
    target_rate = int(config.get("sample_rate") or 16000)
    max_seconds = config.get("max_seconds")
    rows: list[dict] = []
    y_true: list[str] = []
    y_pred: list[str] = []
    true_values: list[float] = []
    pred_values: list[float] = []
    conditions: list[str | None] = []
    confidences: list[float | None] = []
    latencies: list[float] = []
    domain_mismatch = False

    for item in items:
        row = {
            "path": item.relpath,
            "true_label": item.label,
            "pred_label": "",
            "true_value": "" if item.target is None else f"{item.target:.6f}",
            "pred_value": "",
            "condition": item.condition or "",
            "confidence": "",
            "latency_ms": "",
            "sample_rate": "",
            "error": "",
        }
        if item.domain and item.domain != dataset["domain"]:
            domain_mismatch = True
        try:
            audio, sample_rate = load_wav(item.path)
            audio = resample_linear(audio, sample_rate, target_rate)
            if max_seconds:
                audio = audio[: int(float(max_seconds) * target_rate)]
            if audio.size == 0:
                raise ValueError("Audio is empty after loading.")
            started = time.perf_counter()
            prediction = model.predict(audio, target_rate)
            latency_ms = (time.perf_counter() - started) * 1000.0
            parsed = _parse_prediction(prediction, task)
            true_target = _true_target(item) if task != "classification" else None
        except Exception as exc:
            row["error"] = str(exc)
            rows.append(row)
            continue
        row["pred_label"] = parsed["label"]
        row["confidence"] = "" if parsed["confidence"] is None else f"{parsed['confidence']:.6f}"
        row["latency_ms"] = f"{latency_ms:.3f}"
        row["sample_rate"] = str(sample_rate)
        if parsed["value"] is not None:
            row["pred_value"] = f"{parsed['value']:.6f}"
        rows.append(row)
        y_true.append(item.label)
        y_pred.append(parsed["label"])
        confidences.append(parsed["confidence"])
        latencies.append(latency_ms)
        conditions.append(item.condition)
        if task != "classification":
            true_values.append(float(true_target))
            pred_values.append(float(parsed["value"]))

    if task == "classification" and not y_true:
        first_error = next((row["error"] for row in rows if row["error"]), "unknown error")
        raise RuntimeError(f"No audio items could be evaluated. First error: {first_error}")
    if task != "classification" and not true_values:
        first_error = next((row["error"] for row in rows if row["error"]), "unknown error")
        raise RuntimeError(f"No audio items could be evaluated. First error: {first_error}")

    if task == "classification":
        metrics = classification_metrics(y_true, y_pred, confidences, latencies)
    else:
        unit = "seconds" if task == "t60" else "meters"
        metrics = regression_metrics(true_values, pred_values, latencies, conditions, task=task, unit=unit)
    metrics["n_items"] = len(items)
    evaluated = len(y_true) if task == "classification" else len(true_values)
    metrics["n_errors"] = len(items) - evaluated
    if domain_mismatch:
        metrics["warnings"] = [
            "Some files declare a domain that differs from the dataset domain. "
            "The run is still recorded under the dataset domain."
        ]
    else:
        metrics["warnings"] = []
    if task == "classification":
        score_note = _score_note(confidences)
        if score_note:
            metrics["warnings"].append(score_note)
    info = model.get_info() if hasattr(model, "get_info") else {}
    metrics["model_info"] = info
    metrics["provenance"] = collect_provenance(project_root)

    destination = runs_dir(project_root) / run["id"]
    destination.mkdir(parents=True, exist_ok=True)
    predictions_path = destination / "predictions.csv"
    _write_predictions(predictions_path, rows)
    return metrics, predictions_path


def _true_target(item) -> float:
    if item.target is not None:
        return float(item.target)
    try:
        return float(item.label)
    except (TypeError, ValueError) as exc:
        raise ValueError(
            f"{item.relpath} has no numeric target. Add a t60 or target column to the manifest."
        ) from exc


def _parse_prediction(prediction: Prediction, task: str = "classification") -> dict:
    if not isinstance(prediction, Prediction):
        raise TypeError("Model.predict must return a Prediction.")
    label = str(prediction.label).strip()
    if not label:
        raise ValueError("Model returned an empty label.")
    confidence = None
    if prediction.scores:
        if label in prediction.scores:
            value = float(prediction.scores[label])
            if 0.0 <= value <= 1.0:
                confidence = value
        total = sum(float(value) for value in prediction.scores.values())
        if abs(total - 1.0) > 0.05:
            prediction.extra = dict(prediction.extra or {})
            prediction.extra["scores_sum"] = total
    if task != "classification" and prediction.value is None:
        raise ValueError("A T60 or distance model must set Prediction.value.")
    return {
        "label": label,
        "confidence": confidence,
        "value": None if prediction.value is None else float(prediction.value),
    }


def _score_note(confidences: list[float | None]) -> str | None:
    missing = sum(value is None for value in confidences)
    if missing == len(confidences):
        return "The model did not provide confidence scores, so calibration error was not computed."
    if missing:
        return (
            f"Confidence was missing for {missing} of {len(confidences)} items. "
            "Calibration error uses only items with a score."
        )
    return None


def _write_predictions(path: Path, rows: list[dict]) -> None:
    fieldnames = [
        "path",
        "true_label",
        "pred_label",
        "true_value",
        "pred_value",
        "condition",
        "confidence",
        "latency_ms",
        "sample_rate",
        "error",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
