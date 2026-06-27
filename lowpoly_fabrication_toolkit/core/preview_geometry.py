from __future__ import annotations


from math import cos, pi, sin


def get_collection(bpy, name: str):
    coll = bpy.data.collections.get(name) or bpy.data.collections.new(name)
    if coll.name not in bpy.context.scene.collection.children.keys():
        try:
            bpy.context.scene.collection.children.link(coll)
        except Exception:
            pass
    return coll


def clear_collection(bpy, name: str) -> None:
    coll = bpy.data.collections.get(name)
    if not coll:
        return
    for obj in list(coll.objects):
        bpy.data.objects.remove(obj, do_unlink=True)


def create_thickness_preview(bpy, obj, thickness: float):
    clear_collection(bpy, "LFT_Preview")
    coll = get_collection(bpy, "LFT_Preview")
    copy = obj.copy()
    copy.data = obj.data.copy()
    copy.name = f"LFT_Thickness_{obj.name}"
    coll.objects.link(copy)
    mod = copy.modifiers.new("LFT inward thickness", "SOLIDIFY")
    mod.thickness = thickness
    mod.offset = -1
    copy.display_type = "TEXTURED"
    return copy


def create_layout_preview(bpy, panels, preview_scale: float = 0.01):
    clear_collection(bpy, "LFT_2D_Layout")
    coll = get_collection(bpy, "LFT_2D_Layout")
    objects = []
    for panel in panels:
        verts = [(x * preview_scale, y * preview_scale, 0.0) for x, y in panel.points]
        edges = [(i, (i + 1) % len(verts)) for i in range(len(verts))]
        mesh = bpy.data.meshes.new(f"{panel.panel_id}_mesh")
        mesh.from_pydata(verts, edges, [])
        mesh.update()
        obj = bpy.data.objects.new(panel.panel_id, mesh)
        coll.objects.link(obj)
        objects.append(obj)
        for i, hole in enumerate(panel.holes):
            hole_obj = _hole_preview_object(bpy, panel.panel_id, i, hole, preview_scale)
            if hole_obj:
                coll.objects.link(hole_obj)
                objects.append(hole_obj)
    return objects


def create_manufacturing_copy(bpy, obj):
    coll = get_collection(bpy, "LFT_Generated")
    copy = obj.copy()
    copy.data = obj.data.copy()
    copy.name = f"LFT_Manufacturing_{obj.name}"
    coll.objects.link(copy)
    for collection in copy.users_collection:
        if collection != coll:
            collection.objects.unlink(copy)
    copy["lft_source_object"] = obj.name
    return copy


def _hole_preview_object(bpy, panel_id: str, index: int, hole: dict, scale: float):
    if hole.get("type") == "CIRCLE":
        cx = hole["x"] * scale
        cy = hole["y"] * scale
        radius = hole["r"] * scale
        verts = [(cx + cos(i * pi / 12) * radius, cy + sin(i * pi / 12) * radius, 0.0) for i in range(24)]
    elif hole.get("type") == "RECTANGLE":
        x = hole["x"] * scale
        y = hole["y"] * scale
        w = hole["w"] * scale
        h = hole["h"] * scale
        verts = [(x, y, 0.0), (x + w, y, 0.0), (x + w, y + h, 0.0), (x, y + h, 0.0)]
    else:
        return None
    edges = [(i, (i + 1) % len(verts)) for i in range(len(verts))]
    mesh = bpy.data.meshes.new(f"{panel_id}_HOLE_{index}_mesh")
    mesh.from_pydata(verts, edges, [])
    mesh.update()
    return bpy.data.objects.new(f"{panel_id}_HOLE_{index}", mesh)
