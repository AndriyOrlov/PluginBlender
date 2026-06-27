from __future__ import annotations

from dataclasses import asdict

from ..core.fabrication_data import ProductPackSettings


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
