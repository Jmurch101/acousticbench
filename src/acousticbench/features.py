"""Small spectral features used by the example baseline.

These are not a claim about the best features for the team's real models.
They give the built-in example classifier something deterministic to use
without librosa or a GPU.
"""

from __future__ import annotations

import numpy as np

FRAME_SIZE = 512
HOP = 256
_EPS = 1e-12


def extract_features(audio: np.ndarray, sample_rate: int) -> dict[str, float]:
    signal = np.ascontiguousarray(np.asarray(audio, dtype=np.float64))
    if signal.size == 0:
        raise ValueError("Cannot extract features from empty audio.")
    if sample_rate <= 0:
        raise ValueError("Sample rate must be positive.")

    rms = float(np.sqrt(np.mean(signal**2)))
    signs = np.signbit(signal)
    zero_crossings = np.count_nonzero(signs[1:] != signs[:-1]) if signal.size > 1 else 0
    duration = signal.size / float(sample_rate)
    zcr = float(zero_crossings / duration) if duration else 0.0

    frames = _frames(signal, FRAME_SIZE, HOP)
    window = np.hanning(FRAME_SIZE)
    spectrum = np.abs(np.fft.rfft(frames * window, axis=1))
    freqs = np.fft.rfftfreq(FRAME_SIZE, d=1.0 / float(sample_rate))

    flatness = np.array([_flatness(row) for row in spectrum], dtype=np.float64)
    centroids = np.array([_centroid(row, freqs) for row in spectrum], dtype=np.float64)
    times = (np.arange(len(centroids)) * HOP) / float(sample_rate)
    slope = _slope(times, centroids)

    return {
        "rms": rms,
        "zero_crossing_rate": zcr,
        "spectral_flatness": float(np.mean(flatness)),
        "spectral_centroid_hz": float(np.mean(centroids)),
        "centroid_slope_hz_per_s": float(slope),
    }


def _frames(signal: np.ndarray, frame_size: int, hop: int) -> np.ndarray:
    if signal.size < frame_size:
        padded = np.zeros(frame_size, dtype=np.float64)
        padded[: signal.size] = signal
        return padded.reshape(1, frame_size)
    count = 1 + (signal.size - frame_size) // hop
    shape = (count, frame_size)
    strides = (signal.strides[0] * hop, signal.strides[0])
    view = np.lib.stride_tricks.as_strided(signal, shape=shape, strides=strides)
    return np.array(view, dtype=np.float64, copy=True)


def _flatness(magnitude: np.ndarray) -> float:
    power = magnitude + _EPS
    geometric = float(np.exp(np.mean(np.log(power))))
    arithmetic = float(np.mean(power))
    return geometric / arithmetic


def _centroid(magnitude: np.ndarray, freqs: np.ndarray) -> float:
    weight = float(np.sum(magnitude))
    if weight <= _EPS:
        return 0.0
    return float(np.sum(freqs * magnitude) / weight)


def _slope(times: np.ndarray, values: np.ndarray) -> float:
    if times.size < 2:
        return 0.0
    fit = np.polyfit(times, values, 1)
    return float(fit[0])
