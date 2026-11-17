"""Predict one configured label for every item. Useful as a baseline."""

from __future__ import annotations

from acousticbench.models.base import AcousticModel, Prediction


class ConstantLabelModel(AcousticModel):
    model_id = "constant-label"
    name = "Constant label baseline"
    description = (
        "Always predicts the configured label. Use it to check that metrics move "
        "when a model ignores the audio. Default label is 'tone'."
    )

    def __init__(self, label: str = "tone", **_params: object) -> None:
        cleaned = str(label).strip()
        if not cleaned:
            raise ValueError("Constant label baseline needs a non-empty label.")
        self.label = cleaned

    def predict(self, audio, sample_rate: int) -> Prediction:
        del audio, sample_rate
        return Prediction(label=self.label, scores={self.label: 1.0})
