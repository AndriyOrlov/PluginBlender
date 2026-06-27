# LowPoly Fabrication Toolkit

Blender 4.x add-on for turning low-poly meshes into fabrication layouts.

## Install

1. Zip the `lowpoly_fabrication_toolkit` folder, or use the included `lowpoly_fabrication_toolkit.zip`.
2. In Blender: `Edit > Preferences > Add-ons > Install`.
3. Pick the zip.
4. Enable `LowPoly Fabrication Toolkit`.
5. Open the 3D View sidebar and use the `LFT` tab.

## Basic Usage

1. Select a mesh object.
2. `Validate > Analyze Mesh`.
3. In Edit Mode, select faces and use `Face Tools` to assign face types and material.
4. Select edges and use `Edge Tools` to assign join type, trim mode, clearance and kerf.
5. Use `Holes & Vents` to add simple circular, rectangular, or vent-grid holes.
6. Set `Materials > Unit Scale mm`; default `100` means one Blender unit exports as 100 mm.
7. Use `Preview > Thickness Preview`.
8. Use `Layout > Generate 2D Layout`.
9. Use `Product Pack > Generate Product Pack`.

Exports are written to `//lft_output` by default:

- `layout.svg`
- `layout.dxf`
- `BOM.csv`
- `project.json`
- `product_pack.zip`

## Implemented MVP

- Blender add-on registration and sidebar UI.
- Material profiles for paper, cardboard, foamboard, plywood, MDF, acrylic, ACP, aluminum, steel, custom.
- Mesh analysis with open-edge and non-manifold edge detection.
- Face type assignment stored in object custom JSON state.
- Edge join, trim, connector, fastener, clearance and kerf assignment.
- Butt/overlap/connector/magnet/glue data model.
- Inward thickness preview through a Solidify preview copy.
- Door/removable/magnetic hatch magnet-hole generation in layout.
- Simple connector parts.
- Auto support ribs for large panels.
- Custom circle/rectangle holes and vent grids.
- Manufacturing validator.
- SVG, DXF, JSON, CSV BOM export.
- Basic Tripo prompt optimizer and configurable client stub.
- OBJ/GLB/GLTF import hook.
- Product pack zip with listing, README, license and preview placeholder.

## Phase 2 TODO

- Exact butt-joint plane trimming and equal mitre geometry.
- Robust polygon offset for concave faces.
- True multi-sheet nesting with rotation optimization.
- Full PDF template generation.
- Advanced DXF layers/entities.
- Living hinge, V-groove, weld and sheet-metal bend math.
- Real Tripo task polling and download workflow matched to current API docs.
- Render automation for cover/exploded/cut-layout images.
- Assembly guide generation.

## Known Limitations

- The SVG exporter is the primary working output.
- Trim modes are stored and influence clearance/kerf shrink, but exact A-to-B/B-to-A cutting planes are Phase 2.
- Nesting is a simple row packer.
- Generated support ribs are heuristic.
- Per-face and per-edge data is stored as object custom JSON, not Blender mesh attributes.
