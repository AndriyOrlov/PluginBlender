from __future__ import annotations

import csv
import json
from pathlib import Path

from .fabrication_data import Panel2D


SVG_LAYERS = ["CUT", "ENGRAVE", "FOLD", "V_GROOVE", "LIVING_HINGE", "HOLES", "MAGNETS", "SCREWS", "LABELS", "SUPPORTS", "CONNECTORS", "WARNINGS"]


def export_svg(path: str | Path, panels: list[Panel2D], width: float, height: float) -> None:
    path = Path(path)
    rows = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}mm" height="{height}mm" viewBox="0 0 {width} {height}">',
        "<style>.cut{fill:none;stroke:#d00;stroke-width:0.1}.hole{fill:none;stroke:#06c;stroke-width:0.1}.label{font:4px sans-serif;fill:#111}</style>",
    ]
    for layer in SVG_LAYERS:
        rows.append(f'<g id="{layer}">')
        if layer == "CUT":
            for p in panels:
                d = " ".join(f"{x:.3f},{y:.3f}" for x, y in p.points)
                rows.append(f'<polygon class="cut" points="{d}" data-id="{p.panel_id}" data-material="{p.material}"/>')
        if layer in {"HOLES", "MAGNETS", "SCREWS"}:
            for p in panels:
                for hole in p.holes:
                    if hole.get("layer", "HOLES") != layer:
                        continue
                    if hole["type"] == "CIRCLE":
                        rows.append(f'<circle class="hole" cx="{hole["x"]:.3f}" cy="{hole["y"]:.3f}" r="{hole["r"]:.3f}"/>')
                    elif hole["type"] == "RECTANGLE":
                        rows.append(f'<rect class="hole" x="{hole["x"]:.3f}" y="{hole["y"]:.3f}" width="{hole["w"]:.3f}" height="{hole["h"]:.3f}"/>')
        if layer == "LABELS":
            for p in panels:
                x, y = p.points[0]
                rows.append(f'<text class="label" x="{x:.3f}" y="{y:.3f}">{p.panel_id} {p.material}</text>')
        rows.append("</g>")
    rows.append("</svg>")
    path.write_text("\n".join(rows), encoding="utf-8")


def export_project_json(path: str | Path, state: dict, panels: list[Panel2D]) -> None:
    payload = {"state": state, "panels": [p.__dict__ for p in panels]}
    Path(path).write_text(json.dumps(payload, indent=2), encoding="utf-8")


def export_bom_csv(path: str | Path, panels: list[Panel2D]) -> None:
    counts: dict[tuple[str, str, float], int] = {}
    for p in panels:
        key = (p.panel_id, p.material, p.thickness)
        counts[key] = counts.get(key, 0) + p.quantity
    with Path(path).open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "material", "thickness_mm", "quantity"])
        for (panel_id, material, thickness), quantity in counts.items():
            writer.writerow([panel_id, material, thickness, quantity])


def export_dxf(path: str | Path, panels: list[Panel2D]) -> None:
    lines = ["0", "SECTION", "2", "ENTITIES"]
    for p in panels:
        pts = p.points + [p.points[0]]
        for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
            lines += ["0", "LINE", "8", "CUT", "10", str(x1), "20", str(y1), "11", str(x2), "21", str(y2)]
    lines += ["0", "ENDSEC", "0", "EOF"]
    Path(path).write_text("\n".join(lines), encoding="utf-8")
