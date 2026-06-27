from __future__ import annotations


def parallel_cut_pattern(width: float, height: float, spacing: float = 4.0, margin: float = 5.0) -> list[tuple[tuple[float, float], tuple[float, float]]]:
    cuts = []
    x = margin
    while x < width - margin:
        cuts.append(((x, margin), (x, height - margin)))
        x += spacing
    return cuts
