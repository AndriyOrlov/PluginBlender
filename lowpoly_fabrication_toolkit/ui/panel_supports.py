import bpy
from .common import LFTPanel


class LFT_PT_supports(LFTPanel, bpy.types.Panel):
    bl_label = "Supports"
    bl_idname = "LFT_PT_supports"

    def draw(self, context):
        self.layout.label(text="Auto ribs are added during layout export.")
        self.layout.operator("lft.export_layout", text="Regenerate Supports")
