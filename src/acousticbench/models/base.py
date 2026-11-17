"""Model interface.

A model receives mono audio and the sample rate AcoustiBench resampled to.
It returns one predicted label and, when it has them, class scores in [0, 1].
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Prediction:
    label: str
    scores: dict[str, float] | None = None
    extra: dict | None = field(default=None)


class AcousticModel:
    model_id = "base"
    name = "Acoustic model"
    task = "classification"
    description = ""

    def predict(self, audio, sample_rate: int) -> Prediction:
        raise NotImplementedError

    def predict_many(self, items: list[tuple]) -> list[Prediction]:
        return [self.predict(audio, sample_rate) for audio, sample_rate in items]
