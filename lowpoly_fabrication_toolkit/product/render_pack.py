from __future__ import annotations

from pathlib import Path


def render_placeholder_files(folder: str | Path) -> list[Path]:
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    readme = folder / "preview_renders.txt"
    readme.write_text("Open Blender and use Product Pack > Render Previews for final renders.\n", encoding="utf-8")
    return [readme]
