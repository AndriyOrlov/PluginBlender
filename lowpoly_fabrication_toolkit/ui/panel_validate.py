import bpy
from .common import LFTPanel


class LFT_PT_validate(LFTPanel, bpy.types.Panel):
    bl_label = "Validate"
    bl_idname = "LFT_PT_validate"

    def draw(self, context):
        s = context.scene.lft_settings
        self.layout.operator("lft.analyze_mesh")
        self.layout.operator("lft.validate")
        self.layout.label(text=s.validator_summary or "No validation run")
