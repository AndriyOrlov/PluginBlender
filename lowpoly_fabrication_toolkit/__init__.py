from __future__ import annotations

bl_info = {
    "name": "LowPoly Fabrication Toolkit",
    "author": "Codex",
    "version": (0, 1, 1),
    "blender": (4, 0, 0),
    "location": "View3D > Sidebar > LFT",
    "description": "Turns low-poly meshes into panel fabrication layouts.",
    "category": "Mesh",
}

import json
from dataclasses import asdict
from pathlib import Path

import bpy
from bpy.props import BoolProperty, EnumProperty, FloatProperty, PointerProperty, StringProperty
from bpy.types import Operator, PropertyGroup

from .core.connectors import connector_panels
from .core.exporters import export_annotated_svg, export_bom_csv, export_canva_layout_board, export_dxf, export_pdf, export_project_json, export_svg
from .core.fabrication_data import (
    ConnectorData,
    EdgeFabricationData,
    FaceFabricationData,
    LayoutSheet,
    ProductPackSettings,
    Panel2D,
    JOIN_TYPES,
    TRIM_MODES,
    FACE_TYPES,
    edge_key,
    load_state,
    save_state,
)
from .core.geometry_2d import face_points_2d, polygon_bounds
from .core.holes import circle_hole, rect_hole, vent_grid
from .core.layout_nesting import nest_panels
from .core.material_profiles import MATERIAL_PROFILES, get_profile
from .core.mesh_analysis import analyze_object
from .core.preview_geometry import create_layout_preview, create_manufacturing_copy, create_thickness_preview
from .core.supports import suggest_supports, support_panels
from .core.trimming import apply_clearance
from .core.validator import validate_state
from .integrations.prompt_optimizer import optimize_prompt
from .integrations.tripo_client import TripoClient, TripoClientConfig
from .product.listing_generator import assembly_guide, assembly_guide_html, listing, stage_diagram_svgs
from .product.render_pack import render_placeholder_files
from .product.zip_builder import build_zip
from .utils.blender_utils import active_mesh_object, ensure_object_mode


def enum_items(values):
    return [(v, v.replace("_", " ").title(), "") for v in values]


def selected_faces_and_edges(obj):
    faces, edges = [], []
    if obj.mode == "EDIT":
        import bmesh

        bm = bmesh.from_edit_mesh(obj.data)
        bm.faces.ensure_lookup_table()
        bm.edges.ensure_lookup_table()
        bm.faces.index_update()
        bm.edges.index_update()
        faces = [f.index for f in bm.faces if f.select]
        edges = [edge_key((e.verts[0].index, e.verts[1].index)) for e in bm.edges if e.select]
    return faces, edges


def scale_points(points, scale):
    return [(x * scale, y * scale) for x, y in points]


def layout_height(panels, sheet):
    if not panels:
        return sheet.height
    return max(sheet.height, max(polygon_bounds(p.points)[3] for p in panels) + sheet.margin)


def build_panels(obj, state, unit_scale_mm=1.0):
    panels = []
    for poly in obj.data.polygons:
        face_data = FaceFabricationData(**state.get("faces", {}).get(str(poly.index), {}))
        material = face_data.material or state["settings"]["material"]
        profile = get_profile(material)
        points = scale_points(face_points_2d(obj, poly.index), unit_scale_mm)
        clearance = profile.default_clearance
        kerf = profile.kerf
        for a, b in poly.edge_keys:
            edge_data = state.get("edges", {}).get(edge_key((a, b)), {})
            clearance = edge_data.get("clearance", clearance) or clearance
            kerf = edge_data.get("kerf", kerf) or kerf
        points = apply_clearance(points, clearance, kerf)
        holes = list(face_data.holes)
        min_x, min_y, max_x, max_y = polygon_bounds(points)
        w, h = max_x - min_x, max_y - min_y
        if face_data.face_type in {"DOOR", "REMOVABLE_PANEL", "MAGNETIC_HATCH"}:
            holes += [
                circle_hole(w * 0.2, h * 0.2, 8, "MAGNETS"),
                circle_hole(w * 0.8, h * 0.8, 8, "MAGNETS"),
            ]
        panels.append(
            Panel2D(f"FACE_{poly.index}", material, profile.thickness, points, holes=holes, labels=[face_data.face_type])
        )

    connector_settings = ConnectorData(**state["settings"].get("connector", {}))
    for key, data in state.get("edges", {}).items():
        if data.get("join_type") in {"CONNECTOR", "MAGNET_CONNECTOR", "GLUE_CONNECTOR"}:
            connector_settings.connector_type = data.get("join_type")
            panels.extend(connector_panels(key, connector_settings))
    supports = suggest_supports(panels)
    state["supports"] = [asdict(s) for s in supports]
    panels.extend(support_panels(supports))
    return panels


class LFT_Settings(PropertyGroup):
    material_profile: EnumProperty(name="Material", items=enum_items(MATERIAL_PROFILES.keys()), default="Plywood 3 mm")
    sheet_width: FloatProperty(name="Sheet W", default=600, min=1)
    sheet_height: FloatProperty(name="Sheet H", default=400, min=1)
    sheet_margin: FloatProperty(name="Margin", default=10, min=0)
    sheet_spacing: FloatProperty(name="Spacing", default=5, min=0)
    unit_scale_mm: FloatProperty(name="Unit Scale mm", default=100.0, min=0.001, description="Millimeters per Blender unit")
    face_type: EnumProperty(name="Face Type", items=enum_items(FACE_TYPES), default="SOLID")
    join_type: EnumProperty(name="Join Type", items=enum_items(JOIN_TYPES), default="BUTT")
    trim_mode: EnumProperty(name="Trim", items=enum_items(TRIM_MODES), default="NO_TRIM")
    connector_type: EnumProperty(name="Connector", items=enum_items(["NONE", "GLUE_CONNECTOR", "MAGNET_CONNECTOR", "BOLT_CONNECTOR", "RIVET_CONNECTOR", "DOOR_HINGE_CONNECTOR"]))
    fastener_type: EnumProperty(name="Fastener", items=enum_items(["NONE", "GLUE", "MAGNET", "SCREW", "RIVET", "BOLT"]))
    clearance: FloatProperty(name="Clearance", default=0.2, min=0)
    kerf: FloatProperty(name="Kerf", default=0.15, min=0)
    preview: BoolProperty(name="Preview", default=True)
    hole_type: EnumProperty(name="Hole", items=enum_items(["CIRCLE", "RECTANGLE", "VENT_GRID"]))
    hole_diameter: FloatProperty(name="Diameter", default=8, min=0.1)
    hole_width: FloatProperty(name="Width", default=12, min=0.1)
    hole_height: FloatProperty(name="Height", default=6, min=0.1)
    output_dir: StringProperty(name="Output Dir", subtype="DIR_PATH", default="//lft_output")
    project_json_path: StringProperty(name="Project JSON", subtype="FILE_PATH")
    tripo_api_key: StringProperty(name="API Key", subtype="PASSWORD")
    tripo_endpoint: StringProperty(name="Endpoint", default="https://api.tripo3d.ai")
    tripo_prompt: StringProperty(name="Prompt", default="a low-poly wolf head sculpture")
    tripo_optimized_prompt: StringProperty(name="Optimized")
    tripo_model_path: StringProperty(name="Model Path", subtype="FILE_PATH")
    pack_title: StringProperty(name="Title", default="LowPoly Fabrication Kit")
    validator_summary: StringProperty(name="Validator")


class LFT_OT_analyze(Operator):
    bl_idname = "lft.analyze_mesh"
    bl_label = "Analyze Mesh"

    def execute(self, context):
        try:
            obj = active_mesh_object(bpy)
            ensure_object_mode(bpy)
            analysis = analyze_object(obj)
            self.report({"INFO"}, f"Faces: {analysis['face_count']}, edges: {analysis['edge_count']}")
        except Exception as exc:
            self.report({"ERROR"}, str(exc))
            return {"CANCELLED"}
        return {"FINISHED"}


class LFT_OT_clean_mesh(Operator):
    bl_idname = "lft.clean_mesh"
    bl_label = "Clean Mesh"

    def execute(self, context):
        try:
            obj = active_mesh_object(bpy)
            ensure_object_mode(bpy)
            bpy.ops.object.select_all(action="DESELECT")
            obj.select_set(True)
            context.view_layer.objects.active = obj
            bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
            bpy.ops.object.mode_set(mode="EDIT")
            bpy.ops.mesh.select_all(action="SELECT")
            bpy.ops.mesh.remove_doubles(threshold=0.0001)
            bpy.ops.mesh.normals_make_consistent(inside=False)
            bpy.ops.object.mode_set(mode="OBJECT")
            obj.data.validate(clean_customdata=False)
            obj.data.update()
            self.report({"INFO"}, "Mesh cleaned")
        except Exception as exc:
            self.report({"ERROR"}, str(exc))
            return {"CANCELLED"}
        return {"FINISHED"}


class LFT_OT_make_manufacturing_copy(Operator):
    bl_idname = "lft.make_manufacturing_copy"
    bl_label = "Create Manufacturing Copy"

    def execute(self, context):
        try:
            obj = active_mesh_object(bpy)
            ensure_object_mode(bpy)
            copy = create_manufacturing_copy(bpy, obj)
            bpy.ops.object.select_all(action="DESELECT")
            copy.select_set(True)
            context.view_layer.objects.active = copy
            self.report({"INFO"}, f"Created {copy.name}")
        except Exception as exc:
            self.report({"ERROR"}, str(exc))
            return {"CANCELLED"}
        return {"FINISHED"}


class LFT_OT_assign_face_type(Operator):
    bl_idname = "lft.assign_face_type"
    bl_label = "Assign Face Type"

    def execute(self, context):
        try:
            obj = active_mesh_object(bpy)
            settings = context.scene.lft_settings
            faces, _ = selected_faces_and_edges(obj)
            if not faces:
                faces = [p.index for p in obj.data.polygons]
            state = load_state(obj)
            state["settings"]["material"] = settings.material_profile
            for idx in faces:
                state["faces"][str(idx)] = asdict(FaceFabricationData(settings.face_type, settings.material_profile))
            save_state(obj, state)
            self.report({"INFO"}, f"Assigned {settings.face_type} to {len(faces)} face(s)")
        except Exception as exc:
            self.report({"ERROR"}, str(exc))
            return {"CANCELLED"}
        return {"FINISHED"}


class LFT_OT_assign_edge_data(Operator):
    bl_idname = "lft.assign_edge_data"
    bl_label = "Assign Edge Data"

    def execute(self, context):
        try:
            obj = active_mesh_object(bpy)
            settings = context.scene.lft_settings
            _, edges = selected_faces_and_edges(obj)
            if not edges:
                ensure_object_mode(bpy)
                edges = [edge_key(e.vertices) for e in obj.data.edges]
            state = load_state(obj)
            for key in edges:
                state["edges"][key] = asdict(
                    EdgeFabricationData(
                        settings.join_type,
                        settings.trim_mode,
                        "",
                        settings.connector_type,
                        settings.fastener_type,
                        settings.clearance,
                        settings.kerf,
                        settings.preview,
                    )
                )
            save_state(obj, state)
            self.report({"INFO"}, f"Assigned edge settings to {len(edges)} edge(s)")
        except Exception as exc:
            self.report({"ERROR"}, str(exc))
            return {"CANCELLED"}
        return {"FINISHED"}


class LFT_OT_add_hole(Operator):
    bl_idname = "lft.add_hole"
    bl_label = "Add Hole"

    def execute(self, context):
        try:
            obj = active_mesh_object(bpy)
            settings = context.scene.lft_settings
            faces, _ = selected_faces_and_edges(obj)
            if not faces:
                faces = [p.index for p in list(obj.data.polygons)[:1]]
            state = load_state(obj)
            for idx in faces:
                points = scale_points(face_points_2d(obj, idx), settings.unit_scale_mm)
                min_x, min_y, max_x, max_y = polygon_bounds(points)
                cx, cy = (min_x + max_x) / 2, (min_y + max_y) / 2
                if settings.hole_type == "CIRCLE":
                    hole = circle_hole(cx, cy, settings.hole_diameter)
                elif settings.hole_type == "RECTANGLE":
                    hole = rect_hole(cx - settings.hole_width / 2, cy - settings.hole_height / 2, settings.hole_width, settings.hole_height)
                else:
                    hole = {"vent": True, "holes": vent_grid(max_x - min_x, max_y - min_y)}
                face = state["faces"].setdefault(str(idx), asdict(FaceFabricationData()))
                if "vent" in hole:
                    face.setdefault("holes", []).extend(hole["holes"])
                else:
                    face.setdefault("holes", []).append(hole)
            save_state(obj, state)
            self.report({"INFO"}, "Hole data added")
        except Exception as exc:
            self.report({"ERROR"}, str(exc))
            return {"CANCELLED"}
        return {"FINISHED"}


class LFT_OT_preview(Operator):
    bl_idname = "lft.preview_thickness"
    bl_label = "Thickness Preview"

    def execute(self, context):
        try:
            obj = active_mesh_object(bpy)
            profile = get_profile(context.scene.lft_settings.material_profile)
            ensure_object_mode(bpy)
            create_thickness_preview(bpy, obj, profile.thickness)
            self.report({"INFO"}, "Preview created in LFT_Preview")
        except Exception as exc:
            self.report({"ERROR"}, str(exc))
            return {"CANCELLED"}
        return {"FINISHED"}


class LFT_OT_export_layout(Operator):
    bl_idname = "lft.export_layout"
    bl_label = "Generate 2D Layout"

    def execute(self, context):
        try:
            obj = active_mesh_object(bpy)
            ensure_object_mode(bpy)
            settings = context.scene.lft_settings
            state = load_state(obj)
            state["settings"]["material"] = settings.material_profile
            state["settings"]["unit_scale_mm"] = settings.unit_scale_mm
            sheet = LayoutSheet(settings.sheet_width, settings.sheet_height, settings.sheet_margin, settings.sheet_spacing)
            panels = nest_panels(build_panels(obj, state, settings.unit_scale_mm), sheet)
            out = Path(bpy.path.abspath(settings.output_dir))
            out.mkdir(parents=True, exist_ok=True)
            export_svg(out / "layout.svg", panels, sheet.width, layout_height(panels, sheet))
            export_annotated_svg(out / "layout_annotated.svg", panels, sheet.width, layout_height(panels, sheet), obj.name)
            export_canva_layout_board(out / "canva_layout_board.html")
            export_dxf(out / "layout.dxf", panels)
            export_pdf(out / "template.pdf", panels, sheet.width, layout_height(panels, sheet))
            export_bom_csv(out / "BOM.csv", panels)
            export_project_json(out / "project.json", state, panels)
            create_layout_preview(bpy, panels)
            save_state(obj, state)
            self.report({"INFO"}, f"Exported layout to {out}")
        except Exception as exc:
            self.report({"ERROR"}, str(exc))
            return {"CANCELLED"}
        return {"FINISHED"}


class LFT_OT_validate(Operator):
    bl_idname = "lft.validate"
    bl_label = "Run Validator"

    def execute(self, context):
        try:
            obj = active_mesh_object(bpy)
            ensure_object_mode(bpy)
            state = load_state(obj)
            analyze_object(obj)
            state = load_state(obj)
            unit_scale = context.scene.lft_settings.unit_scale_mm
            panels = build_panels(obj, state, unit_scale)
            issues = validate_state(obj, panels, state)
            context.scene.lft_settings.validator_summary = f"{len(issues)} issue(s)"
            obj["lft_validator_issues"] = json.dumps([asdict(i) for i in issues], indent=2)
            self.report({"INFO"} if not issues else {"WARNING"}, context.scene.lft_settings.validator_summary)
        except Exception as exc:
            self.report({"ERROR"}, str(exc))
            return {"CANCELLED"}
        return {"FINISHED"}


class LFT_OT_load_project_json(Operator):
    bl_idname = "lft.load_project_json"
    bl_label = "Load Project JSON"

    def execute(self, context):
        try:
            obj = active_mesh_object(bpy)
            path = Path(bpy.path.abspath(context.scene.lft_settings.project_json_path))
            data = json.loads(path.read_text(encoding="utf-8"))
            state = data.get("state", data)
            if not isinstance(state, dict):
                raise ValueError("Project JSON does not contain a state object.")
            save_state(obj, state)
            self.report({"INFO"}, f"Loaded project state from {path}")
        except Exception as exc:
            self.report({"ERROR"}, str(exc))
            return {"CANCELLED"}
        return {"FINISHED"}


class LFT_OT_optimize_prompt(Operator):
    bl_idname = "lft.optimize_prompt"
    bl_label = "Optimize Prompt"

    def execute(self, context):
        s = context.scene.lft_settings
        s.tripo_optimized_prompt = optimize_prompt(s.tripo_prompt, s.material_profile)
        return {"FINISHED"}


class LFT_OT_test_tripo(Operator):
    bl_idname = "lft.test_tripo"
    bl_label = "Test Connection"

    def execute(self, context):
        s = context.scene.lft_settings
        client = TripoClient(TripoClientConfig(s.tripo_endpoint, s.tripo_api_key))
        self.report({"INFO"}, "Tripo endpoint configured" if client.test_connection() else "No endpoint")
        return {"FINISHED"}


class LFT_OT_import_generated(Operator):
    bl_idname = "lft.import_generated_model"
    bl_label = "Import Result"

    def execute(self, context):
        try:
            path = bpy.path.abspath(context.scene.lft_settings.tripo_model_path)
            suffix = Path(path).suffix.lower()
            if suffix == ".obj":
                bpy.ops.wm.obj_import(filepath=path)
            elif suffix in {".glb", ".gltf"}:
                bpy.ops.import_scene.gltf(filepath=path)
            else:
                raise ValueError("Supported imports: OBJ, GLB, GLTF.")
            self.report({"INFO"}, "Model imported")
        except Exception as exc:
            self.report({"ERROR"}, str(exc))
            return {"CANCELLED"}
        return {"FINISHED"}


class LFT_OT_product_pack(Operator):
    bl_idname = "lft.product_pack"
    bl_label = "Generate Product Pack"

    def execute(self, context):
        try:
            settings = context.scene.lft_settings
            out = Path(bpy.path.abspath(settings.output_dir))
            out.mkdir(parents=True, exist_ok=True)
            files = [out / "template.pdf", out / "layout.svg", out / "layout_annotated.svg", out / "canva_layout_board.html", out / "layout.dxf", out / "BOM.csv", out / "project.json"]
            files += render_placeholder_files(out)
            obj = context.object if context.object and context.object.type == "MESH" else None
            panels = build_panels(obj, load_state(obj), settings.unit_scale_mm) if obj else []
            issues = json.loads(obj.get("lft_validator_issues", "[]")) if obj else []
            pack_settings = ProductPackSettings(title=settings.pack_title)
            guide = out / "assembly_guide.txt"
            guide.write_text(assembly_guide(settings.pack_title, panels, len(issues)), encoding="utf-8")
            guide_html = out / "assembly_guide.html"
            guide_html.write_text(assembly_guide_html(settings.pack_title, panels, len(issues)), encoding="utf-8")
            stage_files = []
            for name, svg in stage_diagram_svgs(panels):
                stage_path = out / name
                stage_path.write_text(svg, encoding="utf-8")
                stage_files.append(stage_path)
            readme = out / "README.txt"
            readme.write_text("LowPoly Fabrication Toolkit export. Cut red outlines, engrave labels, dry-fit before glue.\n", encoding="utf-8")
            license_file = out / "license.txt"
            license_file.write_text("Add your license terms here.\n", encoding="utf-8")
            listing_path = out / "listing.json"
            files += [listing_path, guide, guide_html, *stage_files, readme, license_file]
            listing_path.write_text(json.dumps(listing(pack_settings, [settings.material_profile], [p.name for p in files]), indent=2), encoding="utf-8")
            build_zip(out / "product_pack.zip", files)
            self.report({"INFO"}, f"Product pack: {out / 'product_pack.zip'}")
        except Exception as exc:
            self.report({"ERROR"}, str(exc))
            return {"CANCELLED"}
        return {"FINISHED"}


from .ui.panel_generate import LFT_PT_generate
from .ui.panel_materials import LFT_PT_materials
from .ui.panel_faces import LFT_PT_faces
from .ui.panel_edges import LFT_PT_edges
from .ui.panel_supports import LFT_PT_supports
from .ui.panel_holes import LFT_PT_holes
from .ui.panel_layout import LFT_PT_layout
from .ui.panel_validate import LFT_PT_validate
from .ui.panel_preview import LFT_PT_preview
from .ui.panel_pack import LFT_PT_pack


classes = (
    LFT_Settings,
    LFT_OT_analyze,
    LFT_OT_make_manufacturing_copy,
    LFT_OT_clean_mesh,
    LFT_OT_assign_face_type,
    LFT_OT_assign_edge_data,
    LFT_OT_add_hole,
    LFT_OT_preview,
    LFT_OT_export_layout,
    LFT_OT_validate,
    LFT_OT_load_project_json,
    LFT_OT_optimize_prompt,
    LFT_OT_test_tripo,
    LFT_OT_import_generated,
    LFT_OT_product_pack,
    LFT_PT_generate,
    LFT_PT_materials,
    LFT_PT_faces,
    LFT_PT_edges,
    LFT_PT_supports,
    LFT_PT_holes,
    LFT_PT_layout,
    LFT_PT_validate,
    LFT_PT_preview,
    LFT_PT_pack,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.lft_settings = PointerProperty(type=LFT_Settings)


def unregister():
    del bpy.types.Scene.lft_settings
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
