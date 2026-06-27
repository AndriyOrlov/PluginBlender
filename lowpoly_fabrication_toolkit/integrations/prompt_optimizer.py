from __future__ import annotations


REQUIRED_PHRASES = [
    "clean low-poly style",
    "large flat polygonal faces",
    "simple silhouette",
    "no tiny details",
    "no thin fragile parts",
    "no floating pieces",
    "no intersecting geometry",
    "watertight single mesh",
    "centered origin",
    "clear front/back orientation",
    "suitable for laser-cut plywood/acrylic panel fabrication",
    "suitable for papercraft-style assembly",
]


def optimize_prompt(prompt: str, material: str = "plywood/acrylic") -> str:
    text = (prompt or "low-poly object").strip()
    suffix = ", ".join(REQUIRED_PHRASES).replace("plywood/acrylic", material)
    return f"Create {text}, {suffix}."


if __name__ == "__main__":
    assert "watertight single mesh" in optimize_prompt("a wolf head")
