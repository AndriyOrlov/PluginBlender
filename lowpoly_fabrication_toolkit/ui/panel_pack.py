import bpy
from .common import LFTPanel


class LFT_PT_pack(LFTPanel, bpy.types.Panel):
    bl_label = "Product Pack"
    bl_idname = "LFT_PT_pack"

    def draw(self, context):
        s = context.scene.lft_settings
        self.layout.prop(s, "pack_title")
        self.layout.operator("lft.product_pack")
