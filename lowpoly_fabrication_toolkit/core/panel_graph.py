from __future__ import annotations

from .fabrication_data import edge_key


def build_panel_graph(obj) -> dict[str, list[int]]:
    graph: dict[str, list[int]] = {}
    for poly in obj.data.polygons:
        for a, b in poly.edge_keys:
            graph.setdefault(edge_key((a, b)), []).append(poly.index)
    return graph
