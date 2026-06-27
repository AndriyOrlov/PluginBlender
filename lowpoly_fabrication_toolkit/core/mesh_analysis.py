from __future__ import annotations

from mathutils import Vector

from .fabrication_data import edge_key, load_state, save_state


def analyze_object(obj) -> dict:
    mesh = obj.data
    mesh.update()
    state = load_state(obj)
    faces = []
    edge_to_faces: dict[str, list[int]] = {}

    for poly in mesh.polygons:
        verts = [mesh.vertices[i].co.copy() for i in poly.vertices]
        area = poly.area
        faces.append(
            {
                "index": poly.index,
                "area": float(area),
                "normal": tuple(poly.normal),
                "vertex_count": len(poly.vertices),
                "material": state.get("faces", {}).get(str(poly.index), {}).get("material", state["settings"]["material"]),
            }
        )
        for a, b in poly.edge_keys:
            edge_to_faces.setdefault(edge_key((a, b)), []).append(poly.index)

    open_edges = [k for k, f in edge_to_faces.items() if len(f) == 1]
    non_manifold_edges = [k for k, f in edge_to_faces.items() if len(f) > 2]
    tiny_faces = [f["index"] for f in faces if f["area"] < 1e-4]

    state["analysis"] = {
        "face_count": len(faces),
        "edge_count": len(edge_to_faces),
        "open_edges": open_edges,
        "non_manifold_edges": non_manifold_edges,
        "tiny_faces": tiny_faces,
    }
    save_state(obj, state)
    return state["analysis"]


def face_center(obj, face_index: int) -> Vector:
    poly = obj.data.polygons[face_index]
    return sum((obj.data.vertices[i].co for i in poly.vertices), Vector()) / len(poly.vertices)
