"""WAV loading and a simple resampler.

The MVP reads PCM WAV files with the standard-library wave module so Windows
setup does not depend on libsndfile. 32-bit files are interpreted as float32
when the sample values sit in a typical audio range, and as int32 otherwise.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

AUDIO_EXTENSIONS = {".wav", ".wave"}


def load_wav(path: Path) -> tuple[np.ndarray, int]:
    import wave

    try:
        with wave.open(str(path), "rb") as handle:
            sample_rate = handle.getframerate()
            channels = handle.getnchannels()
            sample_width = handle.getsampwidth()
            frame_count = handle.getnframes()
            raw = handle.readframes(frame_count)
            comptype = handle.getcomptype()
    except wave.Error as exc:
        raise ValueError(f"Could not read WAV file {path}: {exc}") from exc

    if sample_rate <= 0:
        raise ValueError(f"{path} has an invalid sample rate.")
    if channels < 1:
        raise ValueError(f"{path} has no audio channels.")
    if comptype not in {"NONE", "not compressed"}:
        raise ValueError(
            f"{path} uses compression '{comptype}'. AcoustiBench reads uncompressed WAV."
        )

    samples = _decode_pcm(raw, sample_width, path)
    if channels > 1:
        usable = (len(samples) // channels) * channels
        if usable == 0:
            raise ValueError(f"{path} did not contain a full audio frame.")
        samples = samples[:usable].reshape(-1, channels).mean(axis=1)
    return np.ascontiguousarray(samples, dtype=np.float64), int(sample_rate)


def write_wav(path: Path, audio: np.ndarray, sample_rate: int) -> None:
    import wave

    path.parent.mkdir(parents=True, exist_ok=True)
    clipped = np.clip(np.asarray(audio, dtype=np.float64), -1.0, 1.0)
    pcm = (clipped * 32767.0).astype("<i2")
    with wave.open(str(path), "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(int(sample_rate))
        handle.writeframes(pcm.tobytes())


def resample_linear(audio: np.ndarray, original_rate: int, target_rate: int) -> np.ndarray:
    """Linear interpolation. It is for a shared model input rate, not a hi-fi converter."""
    signal = np.asarray(audio, dtype=np.float64)
    if original_rate == target_rate or signal.size == 0:
        return signal
    if original_rate <= 0 or target_rate <= 0:
        raise ValueError("Sample rates must be positive.")
    target_length = int(round(signal.size * target_rate / original_rate))
    target_length = max(target_length, 1)
    if signal.size == 1 or target_length == 1:
        return np.full(target_length, float(signal[0]), dtype=np.float64)
    old_x = np.linspace(0.0, 1.0, num=signal.size, endpoint=False)
    new_x = np.linspace(0.0, 1.0, num=target_length, endpoint=False)
    return np.interp(new_x, old_x, signal).astype(np.float64)


def _decode_pcm(raw: bytes, sample_width: int, path: Path) -> np.ndarray:
    if sample_width == 1:
        data = np.frombuffer(raw, dtype=np.uint8).astype(np.float64)
        return (data - 128.0) / 128.0
    if sample_width == 2:
        return np.frombuffer(raw, dtype="<i2").astype(np.float64) / 32768.0
    if sample_width == 3:
        bytes_ = np.frombuffer(raw, dtype=np.uint8)
        usable = (len(bytes_) // 3) * 3
        triples = bytes_[:usable].reshape(-1, 3).astype(np.int32)
        values = triples[:, 0] | (triples[:, 1] << 8) | (triples[:, 2] << 16)
        values = np.where(values >= 2**23, values - 2**24, values)
        return values.astype(np.float64) / float(2**23)
    if sample_width == 4:
        as_float = np.frombuffer(raw, dtype="<f4")
        finite = as_float[np.isfinite(as_float)]
        if finite.size and np.percentile(np.abs(finite), 95) <= 2.5:
            return as_float.astype(np.float64)
        return np.frombuffer(raw, dtype="<i4").astype(np.float64) / float(2**31)
    raise ValueError(
        f"{path} uses {sample_width * 8}-bit samples. "
        "Supported WAV depths are 8, 16, 24, and 32 bit."
    )
