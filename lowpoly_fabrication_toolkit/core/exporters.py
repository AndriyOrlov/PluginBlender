from __future__ import annotations

import csv
import json
from io import BytesIO
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


def export_pdf(path: str | Path, panels: list[Panel2D], width: float, height: float) -> None:
    mm_to_pt = 72 / 25.4
    page_w = width * mm_to_pt
    page_h = height * mm_to_pt
    commands = ["0.3 w", "1 0 0 RG"]
    for panel in panels:
        pts = [(x * mm_to_pt, page_h - y * mm_to_pt) for x, y in panel.points]
        if not pts:
            continue
        commands.append(f"{pts[0][0]:.3f} {pts[0][1]:.3f} m")
        for x, y in pts[1:]:
            commands.append(f"{x:.3f} {y:.3f} l")
        commands.append("h S")
        label_x, label_y = pts[0]
        commands.append("0 0 0 rg")
        commands.append(f"BT /F1 8 Tf {label_x:.3f} {label_y - 10:.3f} Td ({_pdf_escape(panel.panel_id)}) Tj ET")
        commands.append("1 0 0 RG")
        for hole in panel.holes:
            _pdf_hole(commands, hole, mm_to_pt, page_h)
    _write_pdf(path, page_w, page_h, "\n".join(commands).encode("ascii"))


def _pdf_hole(commands: list[str], hole: dict, scale: float, page_h: float) -> None:
    commands.append("0 0 1 RG")
    if hole.get("type") == "RECTANGLE":
        x = hole["x"] * scale
        y = page_h - (hole["y"] + hole["h"]) * scale
        commands.append(f"{x:.3f} {y:.3f} {hole['w'] * scale:.3f} {hole['h'] * scale:.3f} re S")
    elif hole.get("type") == "CIRCLE":
        from math import cos, pi, sin

        # ponytail: 12-sided circle approximation; swap for Beziers if print fidelity needs it.
        cx = hole["x"] * scale
        cy = page_h - hole["y"] * scale
        r = hole["r"] * scale
        pts = [(cx + cos(i * pi / 6) * r, cy + sin(i * pi / 6) * r) for i in range(12)]
        commands.append(f"{pts[0][0]:.3f} {pts[0][1]:.3f} m")
        for x, y in pts[1:]:
            commands.append(f"{x:.3f} {y:.3f} l")
        commands.append("h S")
    commands.append("1 0 0 RG")


def _pdf_escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def _write_pdf(path: str | Path, width: float, height: float, stream: bytes) -> None:
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {width:.3f} {height:.3f}] /Resources << /Font << /F1 5 0 R >> >> /Contents 4 0 R >>".encode("ascii"),
        b"<< /Length " + str(len(stream)).encode("ascii") + b" >>\nstream\n" + stream + b"\nendstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    out = BytesIO()
    out.write(b"%PDF-1.4\n")
    offsets = []
    for i, obj in enumerate(objects, 1):
        offsets.append(out.tell())
        out.write(f"{i} 0 obj\n".encode("ascii"))
        out.write(obj)
        out.write(b"\nendobj\n")
    xref = out.tell()
    out.write(f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n".encode("ascii"))
    for offset in offsets:
        out.write(f"{offset:010d} 00000 n \n".encode("ascii"))
    out.write(f"trailer << /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode("ascii"))
    Path(path).write_bytes(out.getvalue())
