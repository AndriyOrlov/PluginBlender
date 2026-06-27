from __future__ import annotations

from .fabrication_data import Panel2D, SupportData
from .geometry_2d import polygon_bounds


def suggest_supports(panels: list[Panel2D], area_limit: float = 12000.0, length_limit: float = 160.0) -> list[SupportData]:
    supports = []
    for p in panels:
        min_x, min_y, max_x, max_y = polygon_bounds(p.points)
        w = max_x - min_x
        h = max_y - min_y
        if w * h > area_limit or max(w, h) > length_limit:
            supports.append(SupportData("INTERNAL_RIB", p.material, max(w, h), 15.0, 1))
    return supports


def support_panels(supports: list[SupportData]) -> list[Panel2D]:
    return [
        Panel2D(f"SUPPORT_{i + 1}", s.material, 0, [(0, 0), (s.length, 0), (s.length, s.width), (0, s.width)], quantity=s.quantity)
        for i, s in enumerate(supports)
    ]
