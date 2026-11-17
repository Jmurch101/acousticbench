"""Sabine reverberation time from room geometry.

T60 = 0.161 * volume / (absorption * surface area), with dimensions in meters.
This is the reference label for the Pyroomacoustics development set. It is not
a measured reverberation time.
"""

from __future__ import annotations


def surface_area(dimensions: tuple[float, float, float]) -> float:
    length, width, height = dimensions
    return 2.0 * (length * width + length * height + width * height)


def volume(dimensions: tuple[float, float, float]) -> float:
    length, width, height = dimensions
    return length * width * height


def sabine_t60(dimensions: tuple[float, float, float], absorption: float) -> float:
    if absorption <= 0:
        raise ValueError("Absorption must be positive.")
    area = surface_area(dimensions)
    if area <= 0 or volume(dimensions) <= 0:
        raise ValueError("Room dimensions must be positive.")
    return 0.161 * volume(dimensions) / (absorption * area)
