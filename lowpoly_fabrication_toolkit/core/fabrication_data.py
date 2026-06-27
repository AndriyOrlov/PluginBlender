from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from typing import Any


JOIN_TYPES = [
    "BUTT",
    "OVERLAP",
    "CONNECTOR",
    "MAGNET_CONNECTOR",
    "GLUE_CONNECTOR",
    "SLOT",
    "WELD",
    "FOLD_LINE",
    "V_GROOVE",
    "LIVING_HINGE",
]

TRIM_MODES = ["NO_TRIM", "TRIM_A_TO_B", "TRIM_B_TO_A", "EQUAL_MITRE", "MANUAL_OVERRIDE"]

FACE_TYPES = [
    "SOLID",
    "DOOR",
    "REMOVABLE_PANEL",
    "MAGNETIC_HATCH",
    "SHELF",
    "SUPPORT",
    "VENT_PANEL",
    "LED_PANEL",
    "SERVICE_HATCH",
    "CUSTOM_HOLE_PANEL",
]


@dataclass
class MaterialProfile:
    name: str
    thickness: float
    kerf: float
    default_clearance: float
    bend_radius: float
    min_hole_edge_distance: float
    allowed_join_types: list[str]
    recommended_fasteners: list[str]
    magnet_hole_tolerance: float
    screw_hole_tolerance: float
    compatible_machines: list[str]
    can_bend: bool = False
    can_living_hinge: bool = False
    can_weld: bool = False


@dataclass
class FaceFabricationData:
    face_type: str = "SOLID"
    material: str = "Plywood 3 mm"
    holes: list[dict[str, Any]] = field(default_factory=list)
    notes: str = ""


@dataclass
class EdgeFabricationData:
    join_type: str = "BUTT"
    trim_mode: str = "NO_TRIM"
    material_override: str = ""
    connector_type: str = "NONE"
    fastener_type: str = "NONE"
    clearance: float | None = None
    kerf: float | None = None
    preview: bool = True


@dataclass
class ConnectorData:
    connector_type: str = "GLUE_CONNECTOR"
    length: float = 25.0
    width: float = 10.0
    offset: float = 8.0
    quantity: int = 1
    material: str = "Plywood 3 mm"
    hole_diameter: float = 3.0
    magnet_diameter: float = 8.0
    magnet_depth: float = 3.0
    screw_diameter: float = 3.0
    clearance: float = 0.2
    hidden: bool = True


@dataclass
class SupportData:
    support_type: str = "INTERNAL_RIB"
    material: str = "Plywood 3 mm"
    length: float = 100.0
    width: float = 15.0
    quantity: int = 1


@dataclass
class Panel2D:
    panel_id: str
    material: str
    thickness: float
    points: list[tuple[float, float]]
    holes: list[dict[str, Any]] = field(default_factory=list)
    labels: list[str] = field(default_factory=list)
    quantity: int = 1


@dataclass
class LayoutSheet:
    width: float = 600.0
    height: float = 400.0
    margin: float = 10.0
    spacing: float = 5.0
    rotate_parts: bool = True
    group_by_material: bool = True


@dataclass
class ValidatorIssue:
    severity: str
    message: str
    object_name: str = ""
    face_index: int | None = None
    edge_key: str = ""


@dataclass
class TripoGenerationSettings:
    api_key: str = ""
    endpoint_base: str = "https://api.tripo3d.ai"
    prompt: str = ""
    object_type: str = "sculpture"
    style: str = "low-poly"
    target_polycount: int = 1200
    manufacturing_intent: str = "laser cut panel fabrication"
    avoid_thin_parts: bool = True
    symmetry: bool = False
    hollow: bool = False
    model_size: float = 200.0
    material_target: str = "Plywood 3 mm"


@dataclass
class ProductPackSettings:
    title: str = "LowPoly Fabrication Kit"
    description: str = ""
    tags: str = "low-poly,laser cut,template"
    difficulty: str = "intermediate"
    estimated_assembly_time: str = "2-4 hours"
    required_tools: str = "laser cutter, glue, magnets"
    recommended_price: str = "19.00"


def default_state() -> dict[str, Any]:
    return {
        "faces": {},
        "edges": {},
        "connectors": [],
        "supports": [],
        "settings": {
            "material": "Plywood 3 mm",
            "sheet": asdict(LayoutSheet()),
            "connector": asdict(ConnectorData()),
            "tripo": asdict(TripoGenerationSettings()),
            "pack": asdict(ProductPackSettings()),
        },
    }


def load_state(obj: Any) -> dict[str, Any]:
    raw = obj.get("lft_project_state", "") if obj else ""
    if not raw:
        return default_state()
    try:
        state = json.loads(raw)
    except Exception:
        return default_state()
    base = default_state()
    base.update(state)
    base.setdefault("faces", {})
    base.setdefault("edges", {})
    base.setdefault("settings", {}).update(state.get("settings", {}))
    return base


def save_state(obj: Any, state: dict[str, Any]) -> None:
    if obj:
        obj["lft_project_state"] = json.dumps(state, indent=2, sort_keys=True)


def edge_key(vertices: tuple[int, int] | list[int]) -> str:
    a, b = sorted((int(vertices[0]), int(vertices[1])))
    return f"{a}:{b}"


def face_data_from_state(state: dict[str, Any], face_index: int) -> FaceFabricationData:
    return FaceFabricationData(**state.get("faces", {}).get(str(face_index), {}))


def edge_data_from_state(state: dict[str, Any], key: str) -> EdgeFabricationData:
    return EdgeFabricationData(**state.get("edges", {}).get(key, {}))


if __name__ == "__main__":
    s = default_state()
    assert s["settings"]["material"] == "Plywood 3 mm"
    assert edge_key((9, 2)) == "2:9"
