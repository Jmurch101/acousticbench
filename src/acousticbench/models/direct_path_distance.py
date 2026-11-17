"""Source-to-microphone distance from the direct-path arrival.

The label this model is checked against is the straight-line distance in the
shoebox. The estimate is onset time times 343 m/s. That speed is the
conventional 20 C value, not a measured room temperature. This is not a
trained model and not a sponsor model.
"""

from __future__ import annotations

import numpy as np

from acousticbench.models.base import AcousticModel, Prediction

SPEED_OF_SOUND_M_S = 343.0
ONSET_FRACTION = 0.05


class DirectPathDistanceModel(AcousticModel):
    model_id = "direct-path-distance"
    name = "Direct-path distance baseline"
    task = "distance"
    description = (
        "Estimates source-to-microphone distance in meters from the first arrival "
        "that reaches 5 percent of the peak, times 343 m/s. Classical baseline. "
        "Not a sponsor neural model."
    )

    def get_info(self) -> dict:
        info = super().get_info()
        info["reference"] = "Direct-path onset times 343 m/s"
        info["unit"] = "meters"
        info["speed_of_sound_m_s"] = SPEED_OF_SOUND_M_S
        info["onset_fraction"] = ONSET_FRACTION
        return info

    def predict(self, audio, sample_rate: int) -> Prediction:
        meters = estimate_distance(audio, sample_rate)
        return Prediction(
            label=f"{meters:.6f}",
            value=meters,
            extra={"method": "direct-path", "unit": "meters", "speed_of_sound_m_s": SPEED_OF_SOUND_M_S},
        )


def estimate_distance(audio, sample_rate: int, onset_fraction: float = ONSET_FRACTION) -> float:
    if sample_rate <= 0:
        raise ValueError("Sample rate must be positive.")
    signal = np.abs(np.asarray(audio, dtype=np.float64).reshape(-1))
    if signal.size == 0:
        raise ValueError("Audio is empty.")
    peak = float(signal.max())
    if peak <= 0:
        raise ValueError("Audio has no energy.")
    onset = int(np.argmax(signal >= onset_fraction * peak))
    return float(onset) / float(sample_rate) * SPEED_OF_SOUND_M_S
