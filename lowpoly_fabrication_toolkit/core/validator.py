from __future__ import annotations

from .fabrication_data import Panel2D, ValidatorIssue, edge_data_from_state
from .geometry_2d import polygon_bounds
from .material_profiles import get_profile


def validate_state(obj, panels: list[Panel2D], state: dict) -> list[ValidatorIssue]:
    issues: list[ValidatorIssue] = []
    analysis = state.get("analysis", {})
    for key in analysis.get("open_edges", []):
        issues.append(ValidatorIssue("WARNING", "Open edge: panel may not unfold cleanly.", obj.name, edge_key=key))
    for key in analysis.get("non_manifold_edges", []):
        issues.append(ValidatorIssue("ERROR", "Non-manifold edge: fix mesh before manufacturing.", obj.name, edge_key=key))

    for key, raw in state.get("edges", {}).items():
        data = edge_data_from_state(state, key)
        mat = get_profile(raw.get("material_override") or state["settings"]["material"])
        if data.join_type not in mat.allowed_join_types:
            issues.append(ValidatorIssue("ERROR", f"{mat.name} does not support {data.join_type}.", obj.name, edge_key=key))
        if data.clearance is not None and data.clearance < 0.05:
            issues.append(ValidatorIssue("WARNING", "Clearance is very small.", obj.name, edge_key=key))

    for p in panels:
        profile = get_profile(p.material)
        min_x, min_y, max_x, max_y = polygon_bounds(p.points)
        if max_x - min_x < profile.thickness * 2 or max_y - min_y < profile.thickness * 2:
            issues.append(ValidatorIssue("ERROR", f"{p.panel_id} is too small for {profile.thickness} mm material."))
        for hole in p.holes:
            x = hole.get("x", 0)
            y = hole.get("y", 0)
            r = hole.get("r", max(hole.get("w", 0), hole.get("h", 0)) / 2)
            if x - r < profile.min_hole_edge_distance or y - r < profile.min_hole_edge_distance:
                issues.append(ValidatorIssue("WARNING", f"{p.panel_id} hole is close to an edge."))
    return issues
