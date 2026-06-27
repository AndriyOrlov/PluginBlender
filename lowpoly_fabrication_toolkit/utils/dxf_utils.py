from __future__ import annotations


def line_entity(x1: float, y1: float, x2: float, y2: float, layer: str = "CUT") -> list[str]:
    return ["0", "LINE", "8", layer, "10", str(x1), "20", str(y1), "11", str(x2), "21", str(y2)]
