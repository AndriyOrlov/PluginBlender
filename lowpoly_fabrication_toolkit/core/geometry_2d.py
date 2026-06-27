from __future__ import annotations

from math import hypot
from typing import Iterable

from mathutils import Vector


def face_points_2d(obj, face_index: int) -> list[tuple[float, float]]:
    mesh = obj.data
    poly = mesh.polygons[face_index]
    verts = [mesh.vertices[i].co.copy() for i in poly.vertices]
    origin = verts[0]
    x_axis = (verts[1] - origin).normalized() if len(verts) > 1 else Vector((1, 0, 0))
    y_axis = poly.normal.cross(x_axis).normalized()
    return [((v - origin).dot(x_axis), (v - origin).dot(y_axis)) for v in verts]


def polygon_bounds(points: Iterable[tuple[float, float]]) -> tuple[float, float, float, float]:
    pts = list(points)
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    return min(xs), min(ys), max(xs), max(ys)


def polygon_area(points: list[tuple[float, float]]) -> float:
    total = 0.0
    for i, (x1, y1) in enumerate(points):
        x2, y2 = points[(i + 1) % len(points)]
        total += x1 * y2 - x2 * y1
    return abs(total) * 0.5


def centroid_offset(points: list[tuple[float, float]], offset: float) -> list[tuple[float, float]]:
    # ponytail: simple centroid scaling; replace with real polygon offset for concave production parts.
    if not points or offset == 0:
        return points
    cx = sum(x for x, _ in points) / len(points)
    cy = sum(y for _, y in points) / len(points)
    out = []
    for x, y in points:
        dx, dy = x - cx, y - cy
        length = hypot(dx, dy) or 1.0
        out.append((x + offset * dx / length, y + offset * dy / length))
    return out


def translated(points: list[tuple[float, float]], dx: float, dy: float) -> list[tuple[float, float]]:
    return [(x + dx, y + dy) for x, y in points]


if __name__ == "__main__":
    assert polygon_area([(0, 0), (2, 0), (2, 1), (0, 1)]) == 2
