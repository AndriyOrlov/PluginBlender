from __future__ import annotations

from .fabrication_data import JOIN_TYPES, MaterialProfile


def _profile(
    name: str,
    thickness: float,
    kerf: float,
    clearance: float,
    machines: list[str],
    *,
    bend: bool = False,
    hinge: bool = False,
    weld: bool = False,
) -> MaterialProfile:
    allowed = list(JOIN_TYPES)
    if not weld and "WELD" in allowed:
        allowed.remove("WELD")
    if not hinge and "LIVING_HINGE" in allowed:
        allowed.remove("LIVING_HINGE")
    return MaterialProfile(
        name=name,
        thickness=thickness,
        kerf=kerf,
        default_clearance=clearance,
        bend_radius=max(thickness * 2, 1.0),
        min_hole_edge_distance=max(thickness * 1.5, 2.0),
        allowed_join_types=allowed,
        recommended_fasteners=["glue", "magnets"] if thickness <= 4 else ["bolts", "rivets"],
        magnet_hole_tolerance=0.15,
        screw_hole_tolerance=0.2,
        compatible_machines=machines,
        can_bend=bend,
        can_living_hinge=hinge,
        can_weld=weld,
    )


MATERIAL_PROFILES = {
    p.name: p
    for p in [
        _profile("Paper", 0.2, 0.05, 0.05, ["blade"], bend=True),
        _profile("Cardboard", 1.5, 0.1, 0.15, ["laser", "blade"], bend=True),
        _profile("Foamboard", 5.0, 0.2, 0.3, ["knife", "CNC"]),
        _profile("Plywood 3 mm", 3.0, 0.15, 0.2, ["laser", "CNC"], hinge=True),
        _profile("Plywood 4 mm", 4.0, 0.18, 0.25, ["laser", "CNC"], hinge=True),
        _profile("MDF 3 mm", 3.0, 0.15, 0.2, ["laser", "CNC"]),
        _profile("MDF 6 mm", 6.0, 0.22, 0.3, ["CNC"]),
        _profile("Acrylic 2 mm", 2.0, 0.12, 0.2, ["laser", "CNC"], hinge=True),
        _profile("Acrylic 3 mm", 3.0, 0.15, 0.25, ["laser", "CNC"], hinge=True),
        _profile("ACP 3 mm", 3.0, 0.2, 0.25, ["CNC"], bend=True),
        _profile("Aluminum Sheet", 1.5, 0.25, 0.3, ["CNC", "plasma"], bend=True, weld=True),
        _profile("Steel Sheet", 1.5, 0.3, 0.35, ["CNC", "plasma"], bend=True, weld=True),
        _profile("Custom", 3.0, 0.15, 0.2, ["laser", "CNC"]),
    ]
}


def get_profile(name: str) -> MaterialProfile:
    return MATERIAL_PROFILES.get(name) or MATERIAL_PROFILES["Plywood 3 mm"]
