from __future__ import annotations

from .geometry_2d import centroid_offset


def apply_clearance(points: list[tuple[float, float]], clearance: float, kerf: float) -> list[tuple[float, float]]:
    return centroid_offset(points, -(clearance + kerf * 0.5))
