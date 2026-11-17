"""Run one model over one dataset and store item-level predictions."""

from __future__ import annotations

import csv
import logging
import time
from pathlib import Path

from acousticbench.audio import load_wav, resample_linear
from acousticbench.eval.store import Store
from acousticbench.metrics import classification_metrics
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
    if getattr(model, "task", "classification") != "classification":
        raise RuntimeError(
            f"Model '{spec.model_id}' declares task '{model.task}'. "
            "This version evaluates closed-set classification only."
        )

    config = run.get("config") or {}
    target_rate = int(config.get("sample_rate") or 16000)
    max_seconds = config.get("max_seconds")
    rows: list[dict] = []
    y_true: list[str] = []
    y_pred: list[str] = []
    confidences: list[float | None] = []
    latencies: list[float] = []
    domain_mismatch = False

    for item in items:
        row = {
            "path": item.relpath,
            "true_label": item.label,
            "pred_label": "",
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
            parsed = _parse_prediction(prediction)
        except Exception as exc:
            row["error"] = str(exc)
            rows.append(row)
            continue
        row["pred_label"] = parsed["label"]
        row["confidence"] = "" if parsed["confidence"] is None else f"{parsed['confidence']:.6f}"
        row["latency_ms"] = f"{latency_ms:.3f}"
        row["sample_rate"] = str(sample_rate)
        rows.append(row)
        y_true.append(item.label)
        y_pred.append(parsed["label"])
        confidences.append(parsed["confidence"])
        latencies.append(latency_ms)

    if not y_true:
        first_error = next((row["error"] for row in rows if row["error"]), "unknown error")
        raise RuntimeError(f"No audio items could be evaluated. First error: {first_error}")

    metrics = classification_metrics(y_true, y_pred, confidences, latencies)
    metrics["n_items"] = len(items)
    metrics["n_errors"] = len(items) - len(y_true)
    if domain_mismatch:
        metrics["warnings"] = [
            "Some files declare a domain that differs from the dataset domain. "
            "The run is still recorded under the dataset domain."
        ]
    else:
        metrics["warnings"] = []
    score_note = _score_note(confidences)
    if score_note:
        metrics["warnings"].append(score_note)

    destination = runs_dir(project_root) / run["id"]
    destination.mkdir(parents=True, exist_ok=True)
    predictions_path = destination / "predictions.csv"
    _write_predictions(predictions_path, rows)
    return metrics, predictions_path


def _parse_prediction(prediction: Prediction) -> dict:
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
    return {"label": label, "confidence": confidence, "scores_sum_ok": True}


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
    fieldnames = ["path", "true_label", "pred_label", "confidence", "latency_ms", "sample_rate", "error"]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
