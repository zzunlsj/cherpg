"""CheRPG Pawn Hero: primitive-only, 1.55 m concept blockout.

Run with the retained GitHub Blender Tool (Blender 5.2.2+):
    blender --background --factory-startup --python THIS_FILE -- OUTPUT_DIR

This is NOT approved art or a replacement for the retained 22/26/27 sheets.
All proportions are provisional until real reference images are provided.
"""

import bpy
import bmesh
import json
import math
import sys
from mathutils import Vector
from pathlib import Path

VERSION = "0.0.1v"
HEIGHT_M = 1.55
OUTPUT_STEM = f"pawn-hero-blockout-{VERSION}"

# The character faces Blender -Y; Z is up; 1 Blender unit = 1 meter.
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
if len(argv) != 1:
    raise RuntimeError("Usage: blender --background --python FILE.py -- OUTPUT_DIR")
out = Path(argv[0]).resolve()
out.mkdir(parents=True, exist_ok=True)

bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)
for c in list(bpy.data.collections):
    if c.name != bpy.context.scene.collection.name:
        bpy.data.collections.remove(c)

scene = bpy.context.scene
scene.unit_settings.system = "METRIC"
scene.unit_settings.scale_length = 1.0
scene.render.resolution_x = 1000
scene.render.resolution_y = 1000
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"


def mat(name, color, metallic=0.0, roughness=0.82):
    material = bpy.data.materials.new(name=name)
    material.diffuse_color = (*color, 1.0)
    material.use_nodes = True
    bsdf = material.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (*color, 1.0)
        bsdf.inputs["Metallic"].default_value = metallic
        bsdf.inputs["Roughness"].default_value = roughness
    return material

STONE = mat("MAT_Stone_Chalk", (0.72, 0.71, 0.67))
IVORY = mat("MAT_Stone_Ivory", (0.91, 0.88, 0.80))
HAIR = mat("MAT_Pale_Layered_Stone", (0.79, 0.78, 0.72))
IRON = mat("MAT_Skeleton_Iron", (0.22, 0.24, 0.26), metallic=0.55)
BASALT = mat("MAT_Stone_Dark", (0.48, 0.47, 0.44))


def collection(name):
    col = bpy.data.collections.new(name)
    scene.collection.children.link(col)
    return col

HEAD_HELMET = collection("PART_01_HELMET")
HEAD_HAIR = collection("PART_02_HAIR")
HEAD_FACE = collection("PART_03_FACE")
FACE_SHAPE = bpy.data.collections.new("SUB_03_01_FACE_SHAPE")
HEAD_FACE.children.link(FACE_SHAPE)
BODY = collection("PART_04_STONE_BODY")
BELT = collection("PART_05_DIRECTION_BELT_PLACEHOLDER")
HELPERS = collection("PREVIEW_ONLY_NOT_EXPORTED")


def move_to(obj, col, material):
    for old in list(obj.users_collection):
        old.objects.unlink(obj)
    col.objects.link(obj)
    obj.data.materials.append(material)
    obj["prototype"] = True
    return obj


def bevel_cube(name, xyz, dimensions, col, material, bevel=0.018):
    bpy.ops.mesh.primitive_cube_add(size=1, location=xyz)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = dimensions
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if bevel > 0:
        mod = obj.modifiers.new("Blockout_Edge_Softening", "BEVEL")
        mod.width = bevel
        mod.segments = 1
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.modifier_apply(modifier=mod.name)
        w = obj.modifiers.new("Weighted_Normals", "WEIGHTED_NORMAL")
    return move_to(obj, col, material)


def ico(name, xyz, radii, subdivisions, col, material):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=subdivisions, radius=1, location=xyz)
    obj = bpy.context.object
    obj.name = name
    obj.scale = radii
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return move_to(obj, col, material)


def connector(name, begin, end, width, col, material, vertices=8):
    a, b = Vector(begin), Vector(end)
    direction = b - a
    bpy.ops.mesh.primitive_cone_add(
        vertices=vertices, radius1=width[0], radius2=width[1],
        depth=direction.length, location=(a + b) * 0.5,
    )
    obj = bpy.context.object
    obj.name = name
    obj.rotation_euler = direction.to_track_quat("Z", "Y").to_euler()
    return move_to(obj, col, material)


def ring(name, xyz, major, minor, xy_scale, col, material):
    bpy.ops.mesh.primitive_torus_add(
        major_segments=16, minor_segments=5, major_radius=major,
        minor_radius=minor, location=xyz,
    )
    obj = bpy.context.object
    obj.name = name
    obj.scale = (xy_scale[0], xy_scale[1], 1)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return move_to(obj, col, material)


# Feet on Z=0; separate rigid pieces rather than human skin or an organic body.
for side, x in (("L", -0.118), ("R", 0.118)):
    bevel_cube(f"BODY_{side}_Foot_Stone", (x, -0.042, 0.064),
               (0.190, 0.255, 0.128), BODY, BASALT, 0.026)
    connector(f"BODY_{side}_LowerLeg_Iron", (x, 0, 0.133),
              (x, 0, 0.416), (0.068, 0.084), BODY, IRON, 8)
    ico(f"BODY_{side}_Knee_Stone", (x, 0, 0.420),
        (0.095, 0.100, 0.080), 1, BODY, STONE)
    connector(f"BODY_{side}_Thigh_Stone", (x, 0, 0.458),
              (x * 0.86, 0, 0.663), (0.094, 0.109), BODY, STONE, 6)

bevel_cube("BODY_Pelvis_Stone", (0, 0, 0.673),
           (0.395, 0.258, 0.194), BODY, BASALT, 0.036)
bevel_cube("BODY_Torso_Stone", (0, 0, 0.903),
           (0.462, 0.282, 0.349), BODY, STONE, 0.047)
bevel_cube("BODY_UpperChest_Stone", (0, 0, 1.075),
           (0.482, 0.299, 0.105), BODY, STONE, 0.022)
connector("BODY_Neck_Iron", (0, 0, 1.111), (0, 0, 1.183),
          (0.071, 0.075), BODY, IRON)

for side, sign in (("L", -1), ("R", 1)):
    ico(f"BODY_{side}_Shoulder_Stone", (sign * 0.289, 0, 1.051),
        (0.112, 0.125, 0.102), 1, BODY, BASALT)
    connector(f"BODY_{side}_UpperArm_Stone",
              (sign * 0.320, 0, 1.024), (sign * 0.356, 0, 0.843),
              (0.079, 0.066), BODY, STONE, 6)
    ico(f"BODY_{side}_Elbow_Iron", (sign * 0.357, 0, 0.824),
        (0.062, 0.062, 0.071), 1, BODY, IRON)
    connector(f"BODY_{side}_Forearm_Stone",
              (sign * 0.361, 0, 0.810), (sign * 0.399, -0.005, 0.602),
              (0.076, 0.055), BODY, STONE, 6)
    bevel_cube(f"BODY_{side}_Hand_Mitten", (sign * 0.401, -0.005, 0.546),
               (0.108, 0.103, 0.135), BODY, BASALT, 0.025)

# Bald head is independent of ears/nose; facial details intentionally not invented.
ico("HEAD_Face_Blank_AngularStone", (0, -0.003, 1.217),
    (0.148, 0.134, 0.139), 1, FACE_SHAPE, IVORY)
# Distinct provisional stone hair cap; no realistic strands or finished bangs.
ico("HEAD_Hair_SilhouetteCap", (0, 0.002, 1.333),
    (0.158, 0.142, 0.052), 1, HEAD_HAIR, HAIR)
for i, x in enumerate((-0.092, 0.0, 0.092)):
    connector(f"HEAD_Hair_FrontTuft_{i + 1}",
              (x, -0.105, 1.346), (x * 0.8, -0.131, 1.303),
              (0.047, 0.008), HEAD_HAIR, HAIR, 5)

# Low-poly annular stone shell; OPEN underneath, no filled cone over the face.
def hollow_helmet_shell():
    n = 16
    # bottom rim -> upper cap, outside first; internal cavity rings continue back down
    outer = [(1.308, 0.202, 0.183), (1.342, 0.202, 0.183),
             (1.379, 0.171, 0.154), (1.433, 0.100, 0.092),
             (1.445, 0.060, 0.056)]
    inner = [(1.427, 0.056, 0.052), (1.382, 0.107, 0.097),
             (1.347, 0.156, 0.144), (1.308, 0.165, 0.152)]
    rings = outer + inner
    verts = [(rx * math.cos(2 * math.pi * j / n),
              ry * math.sin(2 * math.pi * j / n), z)
             for z, rx, ry in rings for j in range(n)]
    faces = []
    for k in range(len(rings) - 1):
        for j in range(n):
            a, b = k * n + j, k * n + (j + 1) % n
            faces.append((a, b, b + n, a + n))
    # Join inner rim to outer rim without a bottom cap; cavity is real.
    last = (len(rings) - 1) * n
    for j in range(n):
        faces.append((last + j, last + (j + 1) % n,
                      (j + 1) % n, j))
    faces.append(tuple((len(outer) - 1) * n + j for j in range(n)))
    faces.append(tuple(len(outer) * n + j for j in reversed(range(n))))
    mesh = bpy.data.meshes.new("Helmet_HollowLowPolyMesh")
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new("HEAD_Helmet_HollowShell", mesh)
    HEAD_HELMET.objects.link(obj)
    obj.data.materials.append(IVORY)
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(mesh)
    bm.free()
    return obj


hollow_helmet_shell()
ring("HEAD_Helmet_BottomStoneBand", (0, 0, 1.323), 0.188, 0.016,
     (1.06, 0.96), HEAD_HELMET, IVORY)
ico("HEAD_Helmet_PawnOrb", (0, 0, 1.506),
    (0.044, 0.044, 0.044), 2, HEAD_HELMET, IVORY)
# Simple waist-mounted device: no deployed anchors or body-rotation animation.
ring("BELT_DirectionDevice_StowedRing", (0, 0, 0.746),
     0.186, 0.020, (1.29, 0.86), BELT, IRON)

export_cols = [HEAD_HELMET, HEAD_HAIR, HEAD_FACE, FACE_SHAPE, BODY, BELT]
export_objects = [obj for col in export_cols for obj in col.objects if obj.type == "MESH"]
if not export_objects:
    raise RuntimeError("No modeling meshes generated")

bpy.ops.object.select_all(action="DESELECT")
for obj in export_objects:
    obj.select_set(True)
bpy.context.view_layer.objects.active = export_objects[0]

blend_path = out / f"{OUTPUT_STEM}.blend"
glb_path = out / f"{OUTPUT_STEM}.glb"
bpy.ops.wm.save_as_mainfile(filepath=str(blend_path))
bpy.ops.export_scene.gltf(
    filepath=str(glb_path), export_format="GLB", use_selection=True,
    export_extras=True, export_apply=False,
)

# Preview guide grid is outside the exported character model.
bevel_cube("PREVIEW_FloorGuide_2mTile", (0, 0, -0.028),
           (2, 2, 0.04), HELPERS, mat("MAT_Backdrop", (0.37, 0.40, 0.43)), 0.0)
for obj in export_objects:
    obj.select_set(False)

scene.render.engine = "BLENDER_WORKBENCH"
scene.display.shading.light = "STUDIO"
scene.display.shading.color_type = "MATERIAL"
scene.display.shading.show_shadows = True
scene.display.shading.show_cavity = True
scene.camera = bpy.data.objects.new("PREVIEW_Camera", bpy.data.cameras.new("PREVIEW_Camera"))
scene.collection.objects.link(scene.camera)
scene.camera.data.type = "ORTHO"
scene.camera.data.ortho_scale = 2.15

def view(name, camera_pos):
    scene.camera.location = camera_pos
    look_at = Vector((0, 0, 0.775))
    scene.camera.rotation_euler = (look_at - scene.camera.location).to_track_quat("-Z", "Y").to_euler()
    scene.render.filepath = str(out / f"{OUTPUT_STEM}-{name}.png")
    bpy.ops.render.render(write_still=True)

for name, coords in (("front", (0, -4, 1.23)),
                     ("side", (4, 0, 1.23)),
                     ("threequarter", (3, -4, 2.05))):
    view(name, coords)

report = {
    "status": "blockout_generated_not_art_approved",
    "version": VERSION,
    "height_m_target": HEIGHT_M,
    "world_units": "meters",
    "coordinate_convention": "Z up; facing -Y",
    "tile_reference_m": [2, 2],
    "mesh_count": len(export_objects),
    "head_modules": ["PART_01_HELMET", "PART_02_HAIR", "PART_03_FACE"],
    "reference_images_available": False,
    "face_features_status": "intentionally_not_modeled",
    "direction_device_status": "belt_only_stowed_placeholder_no_body_rotation",
    "notes": [
        "All proportions are provisional until approved drawings are supplied.",
        "The original deleted character models are not reused.",
        "Exporting and rendering do not establish visual likeness or game-readiness.",
    ],
    "files": [blend_path.name, glb_path.name,
              *(f"{OUTPUT_STEM}-{x}.png" for x in ("front", "side", "threequarter"))],
}
(out / f"{OUTPUT_STEM}-manifest.json").write_text(
    json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
print("CHERPG_PAWN_BLOCKOUT_READY", json.dumps(report, ensure_ascii=False))
