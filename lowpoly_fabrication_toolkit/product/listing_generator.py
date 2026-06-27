from __future__ import annotations

from dataclasses import asdict

from ..core.fabrication_data import ProductPackSettings


def listing(settings: ProductPackSettings, materials: list[str], included_files: list[str]) -> dict:
    return {
        **asdict(settings),
        "materials": materials,
        "included_files": included_files,
    }
