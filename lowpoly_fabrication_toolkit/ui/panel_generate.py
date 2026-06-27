import bpy
from .common import LFTPanel


class LFT_PT_generate(LFTPanel, bpy.types.Panel):
    bl_label = "Generate"
    bl_idname = "LFT_PT_generate"

    def draw(self, context):
        s = context.scene.lft_settings
        layout = self.layout
        layout.prop(s, "tripo_api_key")
        layout.prop(s, "tripo_endpoint")
        layout.prop(s, "tripo_prompt")
        layout.operator("lft.optimize_prompt")
        layout.prop(s, "tripo_optimized_prompt")
        layout.operator("lft.test_tripo")
        layout.prop(s, "tripo_model_path")
        layout.operator("lft.import_generated_model")
