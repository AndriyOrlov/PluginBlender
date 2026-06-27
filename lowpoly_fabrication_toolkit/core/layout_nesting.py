from __future__ import annotations

from dataclasses import replace

from .fabrication_data import LayoutSheet, Panel2D
from .geometry_2d import polygon_bounds, translated


def nest_panels(panels: list[Panel2D], sheet: LayoutSheet) -> list[Panel2D]:
    x = sheet.margin
    y = sheet.margin
    row_h = 0.0
    placed: list[Panel2D] = []
    for panel in panels:
        min_x, min_y, max_x, max_y = polygon_bounds(panel.points)
        w = max_x - min_x
        h = max_y - min_y
        if x + w > sheet.width - sheet.margin:
            x = sheet.margin
            y += row_h + sheet.spacing
            row_h = 0.0
        if y + h > sheet.height - sheet.margin:
            # ponytail: start a new virtual sheet by continuing downward; SVG labels overflow instead of failing.
            x = sheet.margin
            y += row_h + sheet.spacing
            row_h = 0.0
        pts = translated(panel.points, x - min_x, y - min_y)
        holes = []
        for hole in panel.holes:
            h2 = dict(hole)
            if "x" in h2:
                h2["x"] += x - min_x
            if "y" in h2:
                h2["y"] += y - min_y
            holes.append(h2)
        placed.append(replace(panel, points=pts, holes=holes))
        x += w + sheet.spacing
        row_h = max(row_h, h)
    return placed
