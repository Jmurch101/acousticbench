"""Schroeder backward-integration estimate of reverberation time.

This is a classical signal-processing baseline, not a trained neural model and
not a sponsor-supplied baseline. It estimates T60 from an impulse response.
M. R. Schroeder, "New Method of Measuring Reverberation Time," Journal of the
Acoustical Society of America, 1965.
"""

from __future__ import annotations

import numpy as np

from acousticbench.models.base import AcousticModel, Prediction


class SchroederT60Model(AcousticModel):
    model_id = "schroeder-t60"
    name = "Schroeder T60 baseline"
    task = "t60"
    description = (
        "Estimates reverberation time in seconds from a room impulse response "
        "using Schroeder backward integration and a linear fit on the decay curve. "
        "Classical baseline for the selected T60 task. Not a sponsor neural model."
    )

    def __init__(self, fit_start_db: float = -5.0, fit_end_db: float = -35.0, **_params: object) -> None:
        if fit_end_db >= fit_start_db:
            raise ValueError("fit_end_db must be more negative than fit_start_db.")
        self.fit_start_db = float(fit_start_db)
        self.fit_end_db = float(fit_end_db)

    def load(self) -> None:
        return None

    def get_info(self) -> dict:
        info = super().get_info()
        info["fit_start_db"] = self.fit_start_db
        info["fit_end_db"] = self.fit_end_db
        info["reference"] = "Schroeder, JASA, 1965"
        info["unit"] = "seconds"
        return info

    def predict(self, audio, sample_rate: int) -> Prediction:
        t60 = estimate_t60(
            audio,
            sample_rate,
            fit_start_db=self.fit_start_db,
            fit_end_db=self.fit_end_db,
        )
        return Prediction(label=f"{t60:.6f}", value=t60, extra={"method": "schroeder", "unit": "seconds"})


def estimate_t60(
    audio,
    sample_rate: int,
    fit_start_db: float = -5.0,
    fit_end_db: float = -35.0,
) -> float:
    if sample_rate <= 0:
        raise ValueError("Sample rate must be positive.")
    signal = np.asarray(audio, dtype=np.float64).reshape(-1)
    if signal.size < sample_rate // 10:
        raise ValueError("Audio is too short to estimate T60.")
    start = int(np.argmax(np.abs(signal)))
    signal = signal[start:]
    energy = np.cumsum((signal ** 2)[::-1])[::-1]
    if energy[0] <= 0:
        raise ValueError("Impulse response has no energy.")
    decay_db = 10.0 * np.log10((energy / energy[0]) + 1e-12)
    times = np.arange(decay_db.size, dtype=np.float64) / float(sample_rate)
    mask = (decay_db <= fit_start_db) & (decay_db >= fit_end_db)
    if int(mask.sum()) < 8:
        mask = (decay_db <= -5.0) & (decay_db >= -25.0)
    if int(mask.sum()) < 5:
        raise ValueError("The decay curve does not contain enough points for a T60 fit.")
    slope = float(np.polyfit(times[mask], decay_db[mask], 1)[0])
    if slope >= -1e-6:
        raise ValueError("The fitted decay slope is not negative.")
    return float(-60.0 / slope)
