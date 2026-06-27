import bpy
from .common import LFTPanel


class LFT_PT_preview(LFTPanel, bpy.types.Panel):
    bl_label = "Preview"
    bl_idname = "LFT_PT_preview"

    def draw(self, context):
        self.layout.operator("lft.preview_thickness")
        self.layout.label(text="Generated objects go to LFT_Preview.")
