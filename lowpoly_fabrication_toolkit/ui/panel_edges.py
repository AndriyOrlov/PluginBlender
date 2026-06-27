import bpy
from .common import LFTPanel


class LFT_PT_edges(LFTPanel, bpy.types.Panel):
    bl_label = "Edge Tools"
    bl_idname = "LFT_PT_edges"

    def draw(self, context):
        s = context.scene.lft_settings
        layout = self.layout
        layout.prop(s, "join_type")
        layout.prop(s, "trim_mode")
        layout.prop(s, "connector_type")
        layout.prop(s, "fastener_type")
        layout.prop(s, "clearance")
        layout.prop(s, "kerf")
        layout.prop(s, "preview")
        layout.operator("lft.assign_edge_data")
