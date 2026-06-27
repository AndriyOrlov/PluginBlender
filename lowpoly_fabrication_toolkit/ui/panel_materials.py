import bpy
from .common import LFTPanel


class LFT_PT_materials(LFTPanel, bpy.types.Panel):
    bl_label = "Materials"
    bl_idname = "LFT_PT_materials"

    def draw(self, context):
        s = context.scene.lft_settings
        layout = self.layout
        layout.prop(s, "material_profile")
        layout.prop(s, "sheet_width")
        layout.prop(s, "sheet_height")
        layout.prop(s, "sheet_margin")
        layout.prop(s, "sheet_spacing")
        layout.prop(s, "kerf")
        layout.prop(s, "clearance")
