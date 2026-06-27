from __future__ import annotations

from .fabrication_data import ConnectorData, Panel2D


def connector_panels(edge_key: str, settings: ConnectorData) -> list[Panel2D]:
    panels = []
    for i in range(max(settings.quantity, 1)):
        pid = f"CONN_{edge_key.replace(':', '_')}_{i + 1}"
        points = [(0, 0), (settings.length, 0), (settings.length, settings.width), (0, settings.width)]
        holes = []
        if "MAGNET" in settings.connector_type:
            r = settings.magnet_diameter / 2
            holes = [
                {"type": "CIRCLE", "layer": "MAGNETS", "x": settings.length * 0.3, "y": settings.width / 2, "r": r},
                {"type": "CIRCLE", "layer": "MAGNETS", "x": settings.length * 0.7, "y": settings.width / 2, "r": r},
            ]
        elif settings.hole_diameter > 0:
            holes = [{"type": "CIRCLE", "layer": "SCREWS", "x": settings.length / 2, "y": settings.width / 2, "r": settings.hole_diameter / 2}]
        panels.append(Panel2D(pid, settings.material, 0, points, holes=holes))
    return panels
