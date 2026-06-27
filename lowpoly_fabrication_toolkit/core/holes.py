from __future__ import annotations


def circle_hole(x: float, y: float, diameter: float, layer: str = "HOLES") -> dict:
    return {"type": "CIRCLE", "layer": layer, "x": x, "y": y, "r": diameter / 2}


def rect_hole(x: float, y: float, width: float, height: float, layer: str = "HOLES") -> dict:
    return {"type": "RECTANGLE", "layer": layer, "x": x, "y": y, "w": width, "h": height}


def vent_grid(width: float, height: float, cols: int = 4, rows: int = 3, slot_w: float = 8, slot_h: float = 3) -> list[dict]:
    holes = []
    for r in range(rows):
        for c in range(cols):
            x = (c + 1) * width / (cols + 1) - slot_w / 2
            y = (r + 1) * height / (rows + 1) - slot_h / 2
            holes.append(rect_hole(x, y, slot_w, slot_h, "HOLES"))
    return holes
