"""Clip-level sound-type rule for ambient, babble, and fan.

ACE's single-channel archive names each noise file, and it does not give
event start and end times. This rule identifies the whole clip. The cuts were
read from that same archive, so the ACE accuracy describes these files. It is
not a held-out test and not a sponsor model.
"""

from __future__ import annotations

import numpy as np

from acousticbench.models.base import AcousticModel, Prediction

BABBLE_ZERO_CROSSING = 0.055
AMBIENT_LOW_BAND = 0.93
LOW_BAND_HZ = 300.0


class NoiseTypeRule(AcousticModel):
    model_id = "noise-type-rule"
    name = "Noise-type rule"
    task = "classification"
    description = (
        "Labels a clip as babble, ambient, or fan from zero crossings and the "
        "share of energy below 300 Hz. Built for the ACE noise filenames. "
        "Not timed sound-event detection and not a trained model."
    )

    def get_info(self) -> dict:
        info = super().get_info()
        info["reference"] = "ACE filename classes; cuts inspected on this corpus"
        info["classes"] = ["ambient", "babble", "fan"]
        info["babble_zero_crossing"] = BABBLE_ZERO_CROSSING
        info["ambient_low_band"] = AMBIENT_LOW_BAND
        info["low_band_hz"] = LOW_BAND_HZ
        return info

    def predict(self, audio, sample_rate: int) -> Prediction:
        label = classify_noise(audio, sample_rate)
        return Prediction(label=label, extra={"method": "noise-type-rule"})


def classify_noise(audio, sample_rate: int) -> str:
    signal = np.asarray(audio, dtype=np.float64).reshape(-1)
    if signal.size < 8 or sample_rate <= 0:
        raise ValueError("Audio is too short to classify.")
    spectrum = np.fft.rfft(signal)
    freqs = np.fft.rfftfreq(signal.size, d=1.0 / float(sample_rate))
    power = np.abs(spectrum) ** 2
    total = float(power.sum()) + 1e-12
    low_band = float(power[freqs < LOW_BAND_HZ].sum()) / total
    zero_crossing = float(np.mean(np.abs(np.diff(np.signbit(signal).astype(np.float64)))))
    if zero_crossing >= BABBLE_ZERO_CROSSING:
        return "babble"
    if low_band >= AMBIENT_LOW_BAND:
        return "ambient"
    return "fan"
