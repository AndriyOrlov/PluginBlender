from __future__ import annotations


def active_mesh_object(bpy):
    obj = bpy.context.object
    if not obj or obj.type != "MESH":
        raise ValueError("Select a mesh object first.")
    return obj


def ensure_object_mode(bpy):
    if bpy.context.object and bpy.context.object.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")
