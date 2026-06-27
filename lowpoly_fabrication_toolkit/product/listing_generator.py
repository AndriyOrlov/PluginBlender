from __future__ import annotations

from dataclasses import asdict
from html import escape

from ..core.fabrication_data import ProductPackSettings
from ..core.geometry_2d import polygon_bounds


def listing(settings: ProductPackSettings, materials: list[str], included_files: list[str]) -> dict:
    return {
        **asdict(settings),
        "materials": materials,
        "included_files": included_files,
    }


def assembly_guide(title: str, panels, issues_count: int = 0) -> str:
    materials = sorted({p.material for p in panels})
    lines = [
        title,
        "",
        "Files:",
        "- template.pdf: printable overview",
        "- layout.svg: laser/CNC cut source",
        "- layout.dxf: CAD cut source",
        "- BOM.csv: material list",
        "",
        f"Parts: {len(panels)}",
        f"Materials: {', '.join(materials) if materials else 'none'}",
        f"Validator warnings/errors: {issues_count}",
        "",
        "Assembly:",
        "1. Cut the red outlines.",
        "2. Cut or drill blue hole marks.",
        "3. Dry-fit panels by matching labels.",
        "4. Install magnets/connectors before final glue.",
        "5. Check doors/removable panels for clearance.",
    ]
    return "\n".join(lines) + "\n"


def assembly_guide_html(title: str, panels, issues_count: int = 0) -> str:
    materials = sorted({p.material for p in panels})
    part_cards = "\n".join(_part_card(i + 1, panel) for i, panel in enumerate(panels[:80]))
    overflow = f"<p class='muted'>+ {len(panels) - 80} more parts in the SVG/DXF layout.</p>" if len(panels) > 80 else ""
    stage_cards = "\n".join(_stage_card(i + 1, stage) for i, stage in enumerate(_assembly_stages(panels)))
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>{escape(title)} Assembly Guide</title>
<style>
@page {{ size: A4; margin: 14mm; }}
body {{ font-family: Arial, sans-serif; color: #171717; margin: 0; }}
.cover {{ min-height: 240mm; display: flex; flex-direction: column; justify-content: center; border-bottom: 2px solid #111; }}
h1 {{ font-size: 42px; margin: 0 0 12px; }}
h2 {{ font-size: 22px; margin: 28px 0 12px; page-break-after: avoid; }}
h3 {{ margin: 0 0 4px; font-size: 15px; }}
.meta {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; margin-top: 24px; }}
.box, .step, .part {{ border: 1px solid #bbb; border-radius: 6px; padding: 10px; break-inside: avoid; }}
.box b {{ display: block; font-size: 11px; text-transform: uppercase; color: #666; }}
.steps, .stage-steps {{ display: grid; gap: 10px; }}
.step {{ display: grid; grid-template-columns: 34px 1fr; gap: 10px; align-items: start; }}
.num {{ width: 28px; height: 28px; border-radius: 50%; background: #111; color: white; display: grid; place-items: center; font-weight: bold; }}
.parts {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px; }}
.part svg {{ width: 100%; height: 120px; background: #fafafa; border: 1px solid #eee; }}
.stage-map {{ width: 100%; max-height: 220px; background: #fafafa; border: 1px solid #ddd; margin-bottom: 10px; }}
.stage {{ page-break-before: always; }}
.parts-list {{ columns: 2; margin: 8px 0 0; padding-left: 18px; }}
.callout {{ background: #f7f7f7; border-left: 5px solid #111; padding: 10px; margin: 10px 0; }}
.muted {{ color: #666; }}
.warn {{ border-left: 5px solid #d97706; padding-left: 10px; }}
@media print {{ .part, .step {{ page-break-inside: avoid; }} }}
</style>
</head>
<body>
<section class="cover">
<p class="muted">LowPoly Fabrication Toolkit</p>
<h1>{escape(title)}</h1>
<p>Printable fabrication and assembly guide generated from the Blender mesh.</p>
<div class="meta">
<div class="box"><b>Parts</b>{len(panels)}</div>
<div class="box"><b>Materials</b>{escape(", ".join(materials) if materials else "none")}</div>
<div class="box"><b>Warnings</b>{issues_count}</div>
</div>
</section>
<h2>Before Cutting</h2>
<div class="box warn">Print or import at 100% scale. Verify one known dimension before cutting expensive material.</div>
<h2>Assembly Stages</h2>
{stage_cards}
<h2>Parts Map</h2>
<div class="parts">{part_cards}</div>
{overflow}
</body>
</html>
"""


def stage_diagram_svgs(panels) -> list[tuple[str, str]]:
    files = []
    for index, stage in enumerate(_assembly_stages(panels), 1):
        slug = stage["title"].lower().replace(",", "").replace(" ", "_")
        svg = _stage_preview_svg(stage["parts"]).replace('class="stage-map"', 'class="stage-map" width="1200"')
        files.append((f"stage_{index:02d}_{slug}.svg", svg))
    return files


def _part_card(index: int, panel) -> str:
    min_x, min_y, max_x, max_y = polygon_bounds(panel.points)
    w = max(max_x - min_x, 1)
    h = max(max_y - min_y, 1)
    pad = max(w, h) * 0.08
    points = " ".join(f"{x - min_x + pad:.2f},{y - min_y + pad:.2f}" for x, y in panel.points)
    holes = "\n".join(_hole_svg(hole, min_x - pad, min_y - pad) for hole in panel.holes)
    view_w = w + pad * 2
    view_h = h + pad * 2
    return f"""<article class="part">
<h3>{index}. {escape(panel.panel_id)}</h3>
<p class="muted">{escape(panel.material)} | qty {panel.quantity}</p>
<svg viewBox="0 0 {view_w:.2f} {view_h:.2f}" xmlns="http://www.w3.org/2000/svg">
<polygon points="{points}" fill="none" stroke="#d00" stroke-width="{max(view_w, view_h) * 0.004:.2f}"/>
{holes}
</svg>
</article>"""


def _assembly_stages(panels) -> list[dict]:
    faces = [p for p in panels if p.panel_id.startswith("FACE_")]
    connectors = [p for p in panels if p.panel_id.startswith("CONN_")]
    supports = [p for p in panels if p.panel_id.startswith("SUPPORT_")]
    magnet_parts = [p for p in panels if any(h.get("layer") == "MAGNETS" for h in p.holes)]
    return [
        {
            "title": "Cut and Sort",
            "parts": panels,
            "steps": [
                "Cut every red outline from layout.svg or template.pdf.",
                "Keep labels visible until final assembly.",
                "Sort pieces into FACE, CONNECTOR, SUPPORT, and MAGNET groups.",
            ],
        },
        {
            "title": "Build Main Shell",
            "parts": faces,
            "steps": [
                "Dry-fit FACE panels first without glue.",
                "Check that each neighboring edge closes cleanly.",
                "Sand tight edges lightly instead of forcing the panel.",
            ],
        },
        {
            "title": "Install Connectors",
            "parts": connectors,
            "steps": [
                "Attach connector strips on the inside face of the shell.",
                "Use glue for glue connectors or screws/rivets for mechanical connectors.",
                "Keep connector faces flush so removable panels still seat correctly.",
            ],
        },
        {
            "title": "Add Supports",
            "parts": supports,
            "steps": [
                "Install ribs and frames after the shell holds its shape.",
                "Do not glue removable access panels to support ribs.",
                "Check long panels for flex before closing the model.",
            ],
        },
        {
            "title": "Doors, Magnets, and Final Check",
            "parts": magnet_parts,
            "steps": [
                "Dry-fit magnets and mark polarity before glue.",
                "Install matching magnet pairs on panel and connector side.",
                "Close the model and verify clearance around every door or removable panel.",
            ],
        },
    ]


def _stage_card(index: int, stage: dict) -> str:
    parts = stage["parts"]
    part_names = "".join(f"<li>{escape(p.panel_id)}</li>" for p in parts[:30])
    more = f"<li>+ {len(parts) - 30} more</li>" if len(parts) > 30 else ""
    steps = "".join(
        f"<section class='step'><div class='num'>{i}</div><div><p>{escape(step)}</p></div></section>"
        for i, step in enumerate(stage["steps"], 1)
    )
    return f"""<section class="stage">
<h2>Stage {index}: {escape(stage["title"])}</h2>
{_stage_preview_svg(parts)}
<div class="callout"><b>Parts in this stage:</b><ul class="parts-list">{part_names}{more}</ul></div>
<div class="stage-steps">{steps}</div>
</section>"""


def _stage_preview_svg(parts) -> str:
    shown = parts[:12]
    if not shown:
        return '<div class="callout">No generated parts in this stage.</div>'
    cells = []
    cell_w = 90
    cell_h = 70
    for i, panel in enumerate(shown):
        col = i % 4
        row = i // 4
        ox = col * cell_w + 8
        oy = row * cell_h + 8
        cells.append(_mini_panel_svg(panel, ox, oy, cell_w - 16, cell_h - 24))
        cells.append(f'<text x="{ox}" y="{oy + cell_h - 8}" font-size="6">{escape(panel.panel_id)}</text>')
    rows = (len(shown) + 3) // 4
    more = f'<text x="8" y="{rows * cell_h + 8}" font-size="7">+ {len(parts) - len(shown)} more parts</text>' if len(parts) > len(shown) else ""
    return f'<svg class="stage-map" viewBox="0 0 360 {rows * cell_h + (18 if more else 0)}" xmlns="http://www.w3.org/2000/svg">{"".join(cells)}{more}</svg>'


def _mini_panel_svg(panel, ox: float, oy: float, max_w: float, max_h: float) -> str:
    min_x, min_y, max_x, max_y = polygon_bounds(panel.points)
    w = max(max_x - min_x, 1)
    h = max(max_y - min_y, 1)
    scale = min(max_w / w, max_h / h)
    points = " ".join(f"{ox + (x - min_x) * scale:.2f},{oy + (y - min_y) * scale:.2f}" for x, y in panel.points)
    holes = []
    for hole in panel.holes[:8]:
        if hole.get("type") == "CIRCLE":
            holes.append(
                f'<circle cx="{ox + (hole["x"] - min_x) * scale:.2f}" cy="{oy + (hole["y"] - min_y) * scale:.2f}" r="{hole["r"] * scale:.2f}" fill="none" stroke="#06c" stroke-width="0.5"/>'
            )
        elif hole.get("type") == "RECTANGLE":
            holes.append(
                f'<rect x="{ox + (hole["x"] - min_x) * scale:.2f}" y="{oy + (hole["y"] - min_y) * scale:.2f}" width="{hole["w"] * scale:.2f}" height="{hole["h"] * scale:.2f}" fill="none" stroke="#06c" stroke-width="0.5"/>'
            )
    return f'<polygon points="{points}" fill="none" stroke="#d00" stroke-width="0.8"/>{"".join(holes)}'


def _hole_svg(hole: dict, ox: float, oy: float) -> str:
    if hole.get("type") == "CIRCLE":
        return f'<circle cx="{hole["x"] - ox:.2f}" cy="{hole["y"] - oy:.2f}" r="{hole["r"]:.2f}" fill="none" stroke="#06c" stroke-width="0.6"/>'
    if hole.get("type") == "RECTANGLE":
        return f'<rect x="{hole["x"] - ox:.2f}" y="{hole["y"] - oy:.2f}" width="{hole["w"]:.2f}" height="{hole["h"]:.2f}" fill="none" stroke="#06c" stroke-width="0.6"/>'
    return ""
