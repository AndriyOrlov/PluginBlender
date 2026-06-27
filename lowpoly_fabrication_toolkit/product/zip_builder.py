from __future__ import annotations

from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile


def build_zip(zip_path: str | Path, files: list[str | Path]) -> None:
    zip_path = Path(zip_path)
    with ZipFile(zip_path, "w", ZIP_DEFLATED) as zf:
        for file in files:
            p = Path(file)
            if p.exists():
                zf.write(p, p.name)
