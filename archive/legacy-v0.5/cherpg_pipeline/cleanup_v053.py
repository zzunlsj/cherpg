import bpy
import bmesh
import json
import math
import os
import sys
from pathlib import Path
from mathutils import Vector

VERSION = "0.5.3"
CAPE_THICKNESS_M = 0.005

def parse_args():
    args = sys.argv
    if "--" not in args:
        raise RuntimeError("Expected arguments after --: input_glb output_dir")
    args = args[args.index("--") + 1:]
    if len(args) < 2:
        raise RuntimeError("Usage: blender --background --python cleanup_v053.py -- input.glb output_dir")
    return Path(args[0]).resolve(), Path(args[1]).resolve()

def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for datablocks in (bpy.data.meshes, bpy.data.curves, bpy.data.armatures, bpy.data.cameras, bpy.data.lights):
        for block in list(datablocks):
            if block.users == 0:
                datablocks.remove(block)

def mesh_objects():
    return [o for o in bpy.context.scene.objects if o.type == "MESH"]

def mesh_stats(objects):
    verts = sum(len(o.data.vertices) for o in objects)
    faces = sum(len(o.data.polygons) for o in objects)
    mats = sorted({slot.material.name for o in objects for slot in o.material_slots if slot.material})
    nan_inf = 0
    degenerate = 0
    non_manifold = 0
    loose_edges = 0
    exact_duplicate_positions = 0

    for o in objects:
        me = o.data
        coords = []
        for v in me.vertices:
            c = v.co
            if not all(math.isfinite(float(x)) for x in c):
                nan_inf += 1
            coords.append((round(c.x, 9), round(c.y, 9), round(c.z, 9)))
        exact_duplicate_positions += max(0, len(coords) - len(set(coords)))

        for p in me.polygons:
            if p.area <= 1e-12:
                degenerate += 1

        bm = bmesh.new()
        bm.from_mesh(me)
        non_manifold += sum(1 for e in bm.edges if not e.is_manifold and not e.is_boundary)
        loose_edges += sum(1 for e in bm.edges if e.is_wire)
        bm.free()

    return {
        "mesh_objects": len(objects),
        "vertices": verts,
        "tri_or_poly_faces": faces,
        "materials": len(mats),
        "material_names": mats,
        "nan_or_inf_vertices": nan_inf,
        "degenerate_faces": degenerate,
        "non_manifold_internal_edges": non_manifold,
        "loose_edges": loose_edges,
        "exact_duplicate_vertex_positions_report_only": exact_duplicate_positions,
    }

def recalc_normals(obj):
    me = obj.data
    bm = bmesh.new()
    bm.from_mesh(me)
    if bm.faces:
        bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    bm.to_mesh(me)
    bm.free()
    me.update()

def set_surface_shading(obj):
    n = obj.name.upper()
    cloth_or_face = (
        "CLOTH" in n
        or "CAPE" in n
        or "SCARF" in n
        or "TABARD" in n
        or "SKIRT" in n
        or "FACE" in n
        or "JAW" in n
        or "EYE" in n
        or "EYELID" in n
    )
    for p in obj.data.polygons:
        p.use_smooth = cloth_or_face

def apply_cape_thickness(obj):
    before = {
        "vertices": len(obj.data.vertices),
        "faces": len(obj.data.polygons),
    }
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj

    mod = obj.modifiers.new(name="CheRPG_Cape_5mm_Solidify", type="SOLIDIFY")
    mod.thickness = CAPE_THICKNESS_M
    mod.offset = 0.0
    mod.use_even_offset = True
    try:
        mod.use_quality_normals = True
    except Exception:
        pass

    bpy.ops.object.modifier_apply(modifier=mod.name)
    recalc_normals(obj)

    after = {
        "vertices": len(obj.data.vertices),
        "faces": len(obj.data.polygons),
    }
    return {"before": before, "after": after, "thickness_m": CAPE_THICKNESS_M}

GROUPS = [
    "HEAD", "HELMET", "CHEST", "PELVIS",
    "UPPER_ARM_L", "UPPER_ARM_R", "FOREARM_L", "FOREARM_R",
    "HAND_L", "HAND_R", "THIGH_L", "THIGH_R",
    "SHIN_L", "SHIN_R", "FOOT_L", "FOOT_R",
    "CAPE", "SCARF", "BACKPACK", "DEVICE", "OTHER"
]

def classify(name):
    n = name.upper()
    if any(k in n for k in ["DEVICE", "DIRECTION", "RING", "CASSETTE", "ANCHOR", "HEADING", "POINTER"]):
        return "DEVICE"
    if "CAPE" in n:
        return "CAPE"
    if "SCARF" in n:
        return "SCARF"
    if any(k in n for k in ["BACKPACK", "BEDROLL"]):
        return "BACKPACK"
    if any(k in n for k in ["HELM", "HELMET"]):
        return "HELMET"
    if any(k in n for k in ["HEAD", "FACE", "JAW", "EYE", "BROW", "HAIR"]):
        return "HEAD"
    if any(k in n for k in ["CHEST", "TORSO", "RIB", "STERNUM", "ABPLATE"]):
        return "CHEST"
    if any(k in n for k in ["PELVIS", "BELT", "TABARD", "SKIRT", "TASSET", "POUCH"]):
        return "PELVIS"

    lr = "L" if any(k in n for k in ["_L_", "_L", "LEFT"]) else ("R" if any(k in n for k in ["_R_", "_R", "RIGHT"]) else None)
    if any(k in n for k in ["UPPERARM", "UPPER_ARM", "PAULDRON", "SHOULDER"]) and lr:
        return f"UPPER_ARM_{lr}"
    if any(k in n for k in ["FOREARM", "ELBOW", "WRIST"]) and lr:
        return f"FOREARM_{lr}"
    if any(k in n for k in ["HAND", "PALM", "FINGER", "THUMB"]) and lr:
        return f"HAND_{lr}"
    if any(k in n for k in ["THIGH", "HIP"]) and lr:
        return f"THIGH_{lr}"
    if any(k in n for k in ["SHIN", "KNEE"]) and lr:
        return f"SHIN_{lr}"
    if any(k in n for k in ["BOOT", "FOOT", "ANKLE"]) and lr:
        return f"FOOT_{lr}"
    return "OTHER"

def setup_collections(objects):
    root = bpy.data.collections.get("CHERPG_LOGICAL_GROUPS")
    if root is None:
        root = bpy.data.collections.new("CHERPG_LOGICAL_GROUPS")
        bpy.context.scene.collection.children.link(root)

    collections = {}
    for g in GROUPS:
        c = bpy.data.collections.get(f"CHR_{g}")
        if c is None:
            c = bpy.data.collections.new(f"CHR_{g}")
            root.children.link(c)
        collections[g] = c

    counts = {g: 0 for g in GROUPS}
    for obj in objects:
        g = classify(obj.name)
        c = collections[g]
        if obj.name not in c.objects:
            c.objects.link(obj)
        obj["cherpg_group"] = g
        counts[g] += 1

    return counts

def setup_device_metadata(objects):
    device_root = bpy.data.objects.get("DEVICE_ROOT")
    if device_root is None:
        device_root = bpy.data.objects.new("DEVICE_ROOT", None)
        bpy.context.scene.collection.objects.link(device_root)
    device_root.empty_display_type = "CIRCLE"
    device_root.empty_display_size = 0.18
    device_root["visual_facing_deg"] = 0.0
    device_root["movement_heading_deg"] = 0.0
    device_root["heading_changes_body_rotation"] = False
    device_root["canonical_behavior"] = (
        "Waist belt expands into a large ring; an anchor descends vertically and locks into the ground. "
        "Only movement-rule heading changes. Character body orientation does not rotate."
    )

    parented = []
    for obj in objects:
        if classify(obj.name) == "DEVICE" and obj.parent is None:
            world = obj.matrix_world.copy()
            obj.parent = device_root
            obj.matrix_world = world
            parented.append(obj.name)
    return parented

def world_bounds(objects):
    pts = []
    for obj in objects:
        for corner in obj.bound_box:
            pts.append(obj.matrix_world @ Vector(corner))
    if not pts:
        return None
    mins = [min(p[i] for p in pts) for i in range(3)]
    maxs = [max(p[i] for p in pts) for i in range(3)]
    return {
        "min": mins,
        "max": maxs,
        "size_m": [maxs[i] - mins[i] for i in range(3)],
    }

def main():
    input_glb, output_dir = parse_args()
    output_dir.mkdir(parents=True, exist_ok=True)

    if not input_glb.exists():
        raise FileNotFoundError(input_glb)

    clear_scene()
    bpy.ops.import_scene.gltf(filepath=str(input_glb))
    objects = mesh_objects()
    before = mesh_stats(objects)

    corrected = []
    for obj in objects:
        recalc_normals(obj)
        set_surface_shading(obj)
        corrected.append(obj.name)

    cape_info = None
    cape = next((o for o in objects if "CLOTH_CAPE_MAIN" in o.name.upper()), None)
    if cape is not None:
        cape_info = apply_cape_thickness(cape)

    objects = mesh_objects()
    group_counts = setup_collections(objects)
    device_parented = setup_device_metadata(objects)

    scene = bpy.context.scene
    scene["cherpg_version"] = VERSION
    scene["cherpg_stage"] = "Blender-ready cleanup"
    scene["canonical_direction_device_body_rotation"] = False

    after = mesh_stats(objects)
    bounds = world_bounds(objects)

    blend_path = output_dir / "cherpg-pawn-protagonist-blender-ready-v0.5.3.blend"
    glb_path = output_dir / "cherpg-pawn-protagonist-blender-ready-v0.5.3.glb"
    report_path = output_dir / "cherpg-pawn-protagonist-v0.5.3-cleanup-report.json"

    bpy.ops.wm.save_as_mainfile(filepath=str(blend_path))

    bpy.ops.export_scene.gltf(
        filepath=str(glb_path),
        export_format="GLB",
        export_yup=True,
        export_normals=True,
        export_materials="EXPORT",
        export_cameras=False,
        export_lights=False,
    )

    report = {
        "version": VERSION,
        "stage": "Blender-ready cleanup",
        "blender_version": bpy.app.version_string,
        "input_file": input_glb.name,
        "output_glb": glb_path.name,
        "output_blend": blend_path.name,
        "before": before,
        "after": after,
        "world_bounds": bounds,
        "normal_recalculated_objects": len(corrected),
        "cape_solidify": cape_info,
        "logical_group_counts": group_counts,
        "device_objects_parented_to_DEVICE_ROOT": device_parented,
        "non_destructive_rules": {
            "merge_by_distance": False,
            "decimate": False,
            "destructive_mesh_join": False,
            "materials_preserved": True,
            "uvs_preserved": True,
        },
        "canonical_direction_device": {
            "body_rotation_when_heading_changes": False,
            "anchor_motion": "vertical",
            "movement_heading_independent_of_visual_facing": True,
        },
    }
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps(report, ensure_ascii=False, indent=2))
    print(f"OUTPUT_GLB={glb_path}")
    print(f"OUTPUT_BLEND={blend_path}")
    print(f"OUTPUT_REPORT={report_path}")

if __name__ == "__main__":
    main()
