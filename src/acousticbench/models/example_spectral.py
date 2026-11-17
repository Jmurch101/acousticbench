"""Built-in rule baseline for the synthetic example classes.

The rules separate a steady tone, broadband noise, and a frequency sweep.
Thresholds were chosen for the signals in acousticbench.examples_data.
This is not a trained research model and it does not have published accuracy.
"""

from __future__ import annotations

import numpy as np

from acousticbench.features import extract_features
from acousticbench.models.base import AcousticModel, Prediction

LABELS = ("chirp", "noise", "tone")
FLATNESS_NOISE = 0.18
CHIRP_SLOPE_HZ_PER_S = 250.0


class ExampleSpectralClassifier(AcousticModel):
    model_id = "example-spectral"
    name = "Example spectral baseline"
    description = (
        "Example-only rules on spectral flatness and how fast the spectral "
        "centroid moves. Built for the generated tone, noise, and chirp files. "
        "Not a trained acoustic model."
    )

    def __init__(self, **_params: object) -> None:
        self.labels = LABELS

    def predict(self, audio, sample_rate: int) -> Prediction:
        features = extract_features(audio, sample_rate)
        label = classify_features(features)
        return Prediction(label=label, scores=heuristic_scores(label, features), extra={"features": features})


def classify_features(features: dict[str, float]) -> str:
    if features["rms"] < 1e-6:
        return "noise"
    if features["spectral_flatness"] >= FLATNESS_NOISE:
        return "noise"
    if abs(features["centroid_slope_hz_per_s"]) >= CHIRP_SLOPE_HZ_PER_S:
        return "chirp"
    return "tone"


def heuristic_scores(label: str, features: dict[str, float]) -> dict[str, float]:
    """Scores peak on the chosen rule so the reported label matches argmax.

    They are heuristic decision scores, not calibrated probabilities from training.
    """
    logits = {
        "noise": (features["spectral_flatness"] - FLATNESS_NOISE) * 8.0,
        "chirp": abs(features["centroid_slope_hz_per_s"]) / CHIRP_SLOPE_HZ_PER_S - 1.0,
        "tone": 1.0 - features["spectral_flatness"] * 4.0,
    }
    logits[label] = logits.get(label, 0.0) + 2.0
    return _softmax(logits)


def _softmax(logits: dict[str, float]) -> dict[str, float]:
    keys = list(logits)
    values = np.array([logits[key] for key in keys], dtype=np.float64)
    values -= np.max(values)
    exp = np.exp(values)
    probs = exp / np.sum(exp)
    return {key: float(prob) for key, prob in zip(keys, probs)}
