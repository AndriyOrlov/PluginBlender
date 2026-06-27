import bpy
from .common import LFTPanel


class LFT_PT_faces(LFTPanel, bpy.types.Panel):
    bl_label = "Face Tools"
    bl_idname = "LFT_PT_faces"

    def draw(self, context):
        s = context.scene.lft_settings
        self.layout.prop(s, "face_type")
        self.layout.prop(s, "material_profile")
        self.layout.operator("lft.assign_face_type")
