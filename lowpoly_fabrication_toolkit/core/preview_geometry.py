from __future__ import annotations


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
