import bpy
from .common import LFTPanel


class LFT_PT_layout(LFTPanel, bpy.types.Panel):
    bl_label = "Layout"
    bl_idname = "LFT_PT_layout"

    def draw(self, context):
        s = context.scene.lft_settings
        self.layout.prop(s, "output_dir")
        self.layout.operator("lft.export_layout")
