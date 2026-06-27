import json

import bpy
from .common import LFTPanel


class LFT_PT_validate(LFTPanel, bpy.types.Panel):
    bl_label = "Validate"
    bl_idname = "LFT_PT_validate"

    def draw(self, context):
        s = context.scene.lft_settings
        self.layout.operator("lft.clean_mesh")
        self.layout.operator("lft.analyze_mesh")
        self.layout.operator("lft.validate")
        self.layout.label(text=s.validator_summary or "No validation run")
        obj = context.object
        if obj and obj.get("lft_validator_issues"):
            try:
                issues = json.loads(obj["lft_validator_issues"])
            except Exception:
                issues = []
            for issue in issues[:8]:
                self.layout.label(text=f"{issue.get('severity', 'INFO')}: {issue.get('message', '')}"[:120])
            if len(issues) > 8:
                self.layout.label(text=f"+ {len(issues) - 8} more")
