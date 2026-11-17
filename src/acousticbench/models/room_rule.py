"""Room-family rule based on a Schroeder T60 estimate.

The cuts sit in the gaps between the simulated design bands: office targets
stay at or below 0.45 s, meeting targets start at 0.55 s, and lecture targets
start at 0.90 s. The cuts were not adjusted to ACE scores. There is no lobby
band. This is not a trained classifier and not a sponsor model.
"""

from __future__ import annotations

from acousticbench.models.base import AcousticModel, Prediction
from acousticbench.models.schroeder_t60 import estimate_t60

OFFICE_MAX_S = 0.50
MEETING_MAX_S = 0.80


class T60RoomRuleModel(AcousticModel):
    model_id = "t60-room-rule"
    name = "T60 room-family rule"
    task = "classification"
    description = (
        "Classifies a room impulse response as office, meeting, or lecture from "
        "the Schroeder T60. Fixed bands: below 0.50 s office, below 0.80 s meeting, "
        "otherwise lecture. Not trained, and not a sponsor model. No lobby class."
    )

    def get_info(self) -> dict:
        info = super().get_info()
        info["reference"] = "Schroeder T60 bands chosen from the simulated design gaps"
        info["thresholds_s"] = [OFFICE_MAX_S, MEETING_MAX_S]
        info["classes"] = ["office", "meeting", "lecture"]
        return info

    def predict(self, audio, sample_rate: int) -> Prediction:
        t60 = estimate_t60(audio, sample_rate)
        if t60 < OFFICE_MAX_S:
            label = "office"
        elif t60 < MEETING_MAX_S:
            label = "meeting"
        else:
            label = "lecture"
        return Prediction(
            label=label,
            extra={"t60_s": t60, "thresholds_s": [OFFICE_MAX_S, MEETING_MAX_S]},
        )
