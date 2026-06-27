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
    steps = [
        ("Inspect files", "Open template.pdf and layout.svg. Confirm material thickness, kerf, and scale before cutting."),
        ("Cut panels", "Cut red outlines first. Keep labels on the sheet until assembly is finished."),
        ("Cut holes", "Cut or drill blue hole marks. Magnets and screws should be dry-fitted before glue."),
        ("Sort parts", "Group FACE panels, CONNECTOR parts, and SUPPORT ribs into separate piles."),
        ("Dry-fit shell", "Assemble matching edges without glue. Fix tight spots with light sanding."),
        ("Install connectors", "Glue or screw internal connectors, then add magnets with polarity marks aligned."),
        ("Final assembly", "Glue structural panels, install removable panels last, and re-check clearances."),
    ]
    step_cards = "\n".join(
        f"<section class='step'><div class='num'>{i}</div><div><h3>{escape(name)}</h3><p>{escape(body)}</p></div></section>"
        for i, (name, body) in enumerate(steps, 1)
    )
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
.steps {{ display: grid; gap: 10px; }}
.step {{ display: grid; grid-template-columns: 34px 1fr; gap: 10px; align-items: start; }}
.num {{ width: 28px; height: 28px; border-radius: 50%; background: #111; color: white; display: grid; place-items: center; font-weight: bold; }}
.parts {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px; }}
.part svg {{ width: 100%; height: 120px; background: #fafafa; border: 1px solid #eee; }}
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
<h2>Assembly Steps</h2>
<div class="steps">{step_cards}</div>
<h2>Parts Map</h2>
<div class="parts">{part_cards}</div>
{overflow}
</body>
</html>
"""


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


def _hole_svg(hole: dict, ox: float, oy: float) -> str:
    if hole.get("type") == "CIRCLE":
        return f'<circle cx="{hole["x"] - ox:.2f}" cy="{hole["y"] - oy:.2f}" r="{hole["r"]:.2f}" fill="none" stroke="#06c" stroke-width="0.6"/>'
    if hole.get("type") == "RECTANGLE":
        return f'<rect x="{hole["x"] - ox:.2f}" y="{hole["y"] - oy:.2f}" width="{hole["w"]:.2f}" height="{hole["h"]:.2f}" fill="none" stroke="#06c" stroke-width="0.6"/>'
    return ""
