import bpy
from .common import LFTPanel


class LFT_PT_holes(LFTPanel, bpy.types.Panel):
    bl_label = "Holes & Vents"
    bl_idname = "LFT_PT_holes"

    def draw(self, context):
        s = context.scene.lft_settings
        layout = self.layout
        layout.prop(s, "hole_type")
        layout.prop(s, "hole_diameter")
        layout.prop(s, "hole_width")
        layout.prop(s, "hole_height")
        layout.operator("lft.add_hole")
