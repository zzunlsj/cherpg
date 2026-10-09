import bpy
import json
import math
import sys
from pathlib import Path
from mathutils import Vector

VERSION = "0.5.4.1"

def parse_args():
    args = sys.argv
    if "--" not in args:
        raise RuntimeError("Expected: input_blend output_dir")
    args = args[args.index("--") + 1:]
    if len(args) < 2:
        raise RuntimeError("Usage: blender --background input.blend --python rig_v054.py -- input.blend output_dir")
    return Path(args[0]).resolve(), Path(args[1]).resolve()

def C(x, y, z=0.0):
    # Source model convention: +Y up, -Z forward.
    # Blender after glTF import: +Z up, -Y forward.
    return Vector((x, -z, y))

JOINTS = {
    "ROOT": C(0.0, 0.0, 0.0),
    "Pelvis": C(0.0, 0.88, 0.0),
    "Spine1": C(0.0, 0.98, 0.0),
    "Spine2": C(0.0, 1.10, 0.0),
    "Chest": C(0.0, 1.19, 0.0),
    "Neck": C(0.0, 1.29, 0.0),
    "Head": C(0.0, 1.405, 0.0),
    "Shoulder_L": C(-0.238, 1.205, 0.0),
    "Elbow_L": C(-0.355, 1.005, 0.0),
    "Wrist_L": C(-0.405, 0.805, -0.006),
    "Hand_L": C(-0.410, 0.735, -0.015),
    "Shoulder_R": C(0.238, 1.205, 0.0),
    "Elbow_R": C(0.355, 1.005, 0.0),
    "Wrist_R": C(0.405, 0.805, -0.006),
    "Hand_R": C(0.410, 0.735, -0.015),
    "Hip_L": C(-0.105, 0.88, 0.0),
    "Knee_L": C(-0.105, 0.585, 0.0),
    "Ankle_L": C(-0.105, 0.275, 0.0),
    "Foot_L": C(-0.105, 0.145, -0.030),
    "Hip_R": C(0.105, 0.88, 0.0),
    "Knee_R": C(0.105, 0.585, 0.0),
    "Ankle_R": C(0.105, 0.275, 0.0),
    "Foot_R": C(0.105, 0.145, -0.030),
}

BONES = [
    ("Root", C(0,0,0), C(0,0.12,0), None),
    ("Pelvis", JOINTS["Pelvis"], JOINTS["Spine1"], "Root"),
    ("Spine1", JOINTS["Spine1"], JOINTS["Spine2"], "Pelvis"),
    ("Spine2", JOINTS["Spine2"], JOINTS["Chest"], "Spine1"),
    ("Chest", JOINTS["Chest"], JOINTS["Neck"], "Spine2"),
    ("Neck", JOINTS["Neck"], JOINTS["Head"], "Chest"),
    ("Head", JOINTS["Head"], C(0,1.54,0), "Neck"),

    ("UpperArm_L", JOINTS["Shoulder_L"], JOINTS["Elbow_L"], "Chest"),
    ("Forearm_L", JOINTS["Elbow_L"], JOINTS["Wrist_L"], "UpperArm_L"),
    ("Hand_L", JOINTS["Wrist_L"], C(-0.415,0.68,-0.018), "Forearm_L"),
    ("UpperArm_R", JOINTS["Shoulder_R"], JOINTS["Elbow_R"], "Chest"),
    ("Forearm_R", JOINTS["Elbow_R"], JOINTS["Wrist_R"], "UpperArm_R"),
    ("Hand_R", JOINTS["Wrist_R"], C(0.415,0.68,-0.018), "Forearm_R"),

    ("Thigh_L", JOINTS["Hip_L"], JOINTS["Knee_L"], "Pelvis"),
    ("Shin_L", JOINTS["Knee_L"], JOINTS["Ankle_L"], "Thigh_L"),
    ("Foot_L", JOINTS["Ankle_L"], C(-0.105,0.13,-0.16), "Shin_L"),
    ("Thigh_R", JOINTS["Hip_R"], JOINTS["Knee_R"], "Pelvis"),
    ("Shin_R", JOINTS["Knee_R"], JOINTS["Ankle_R"], "Thigh_R"),
    ("Foot_R", JOINTS["Ankle_R"], C(0.105,0.13,-0.16), "Shin_R"),

    ("CapeUpper", C(0,1.22,0.055), C(0,1.07,0.075), "Chest"),
    ("CapeMid", C(0,1.07,0.075), C(0,0.83,0.105), "CapeUpper"),
    ("CapeLower", C(0,0.83,0.105), C(0,0.48,0.14), "CapeMid"),
    ("Scarf", C(0,1.285,-0.015), C(0,1.18,0.07), "Neck"),
]

RIGID_MAP = {
    "HEAD": "Head",
    "HELMET": "Head",
    "CHEST": "Chest",
    "PELVIS": "Pelvis",
    "UPPER_ARM_L": "UpperArm_L",
    "UPPER_ARM_R": "UpperArm_R",
    "FOREARM_L": "Forearm_L",
    "FOREARM_R": "Forearm_R",
    "HAND_L": "Hand_L",
    "HAND_R": "Hand_R",
    "THIGH_L": "Thigh_L",
    "THIGH_R": "Thigh_R",
    "SHIN_L": "Shin_L",
    "SHIN_R": "Shin_R",
    "FOOT_L": "Foot_L",
    "FOOT_R": "Foot_R",
    "BACKPACK": "Chest",
}

def mesh_objects():
    return [o for o in bpy.context.scene.objects if o.type == "MESH"]

def get_group(obj):
    # v0.5.4 bugfix: only DEVICE_* meshes belong to the direction device.
    # The elbow rings were incorrectly captured by the old generic "Ring" rule.
    if obj.name == "ARM_L_ElbowRing":
        g = "FOREARM_L"
    elif obj.name == "ARM_R_ElbowRing":
        g = "FOREARM_R"
    elif obj.name.startswith("DEVICE_"):
        g = "DEVICE"
    else:
        g = str(obj.get("cherpg_group", "OTHER"))
    obj["cherpg_group"] = g
    return g

def create_armature():
    old = bpy.data.objects.get("RIG_PawnHero")
    if old:
        bpy.data.objects.remove(old, do_unlink=True)

    arm_data = bpy.data.armatures.new("RIG_PawnHero_DATA")
    arm_obj = bpy.data.objects.new("RIG_PawnHero", arm_data)
    bpy.context.scene.collection.objects.link(arm_obj)
    arm_obj.show_in_front = True
    arm_obj["rig_version"] = VERSION
    arm_obj["rig_type"] = "Rigid stone body + deformable cloth"

    bpy.context.view_layer.objects.active = arm_obj
    arm_obj.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")

    made = {}
    for name, head, tail, parent in BONES:
        b = arm_data.edit_bones.new(name)
        b.head = head
        b.tail = tail
        if (b.tail - b.head).length < 0.02:
            b.tail.z += 0.05
        made[name] = b

    for name, head, tail, parent in BONES:
        if parent:
            made[name].parent = made[parent]
            made[name].use_connect = False

    bpy.ops.object.mode_set(mode="OBJECT")
    arm_obj.select_set(False)
    return arm_obj

def clear_old_skin(obj, arm_obj):
    for m in list(obj.modifiers):
        if m.type == "ARMATURE":
            obj.modifiers.remove(m)
    for vg in list(obj.vertex_groups):
        obj.vertex_groups.remove(vg)

def add_armature_modifier(obj, arm_obj):
    mod = obj.modifiers.new(name="CheRPG_Armature", type="ARMATURE")
    mod.object = arm_obj
    mod.use_vertex_groups = True
    return mod

def rigid_skin(obj, arm_obj, bone):
    clear_old_skin(obj, arm_obj)
    vg = obj.vertex_groups.new(name=bone)
    if len(obj.data.vertices):
        vg.add(list(range(len(obj.data.vertices))), 1.0, "REPLACE")
    add_armature_modifier(obj, arm_obj)
    obj["cherpg_skin_mode"] = "rigid"
    obj["cherpg_primary_bone"] = bone

def cloth_skin_cape(obj, arm_obj):
    clear_old_skin(obj, arm_obj)
    groups = {
        "CapeUpper": obj.vertex_groups.new(name="CapeUpper"),
        "CapeMid": obj.vertex_groups.new(name="CapeMid"),
        "CapeLower": obj.vertex_groups.new(name="CapeLower"),
    }
    if not obj.data.vertices:
        add_armature_modifier(obj, arm_obj)
        return

    zs = [v.co.z for v in obj.data.vertices]
    zmin, zmax = min(zs), max(zs)
    span = max(1e-6, zmax-zmin)

    for v in obj.data.vertices:
        t = (v.co.z-zmin)/span
        # t=1 upper, t=0 lower. Blend adjacent zones.
        if t >= 0.60:
            upper = min(1.0, (t-0.50)/0.30)
            mid = 1.0-upper
            lower = 0.0
        elif t >= 0.28:
            mid = min(1.0, 1.0-abs(t-0.45)/0.22)
            lower = max(0.0, 1.0-mid)
            upper = 0.0
        else:
            lower = 1.0
            mid = 0.0
            upper = 0.0
        s = upper+mid+lower
        if s <= 1e-6:
            lower = 1.0
            s = 1.0
        groups["CapeUpper"].add([v.index], upper/s, "REPLACE")
        groups["CapeMid"].add([v.index], mid/s, "REPLACE")
        groups["CapeLower"].add([v.index], lower/s, "REPLACE")

    add_armature_modifier(obj, arm_obj)
    obj["cherpg_skin_mode"] = "deform_cape"
    obj["cherpg_primary_bone"] = "CapeUpper"

def cloth_skin_scarf(obj, arm_obj):
    clear_old_skin(obj, arm_obj)
    vg = obj.vertex_groups.new(name="Scarf")
    if len(obj.data.vertices):
        vg.add(list(range(len(obj.data.vertices))), 1.0, "REPLACE")
    add_armature_modifier(obj, arm_obj)
    obj["cherpg_skin_mode"] = "deform_scarf"
    obj["cherpg_primary_bone"] = "Scarf"

def obj_world_center(obj):
    corners = [obj.matrix_world @ Vector(c) for c in obj.bound_box]
    if not corners:
        return obj.matrix_world.translation.copy()
    c = Vector((0,0,0))
    for p in corners:
        c += p
    return c / len(corners)

NEAREST_BONES = [
    "Head","Chest","Pelvis",
    "UpperArm_L","Forearm_L","Hand_L",
    "UpperArm_R","Forearm_R","Hand_R",
    "Thigh_L","Shin_L","Foot_L",
    "Thigh_R","Shin_R","Foot_R",
]

def bone_midpoints(arm_obj):
    return {b.name:(arm_obj.matrix_world @ ((b.head_local+b.tail_local)*0.5)) for b in arm_obj.data.bones}

def nearest_body_bone(obj, mids):
    center = obj_world_center(obj)
    return min(NEAREST_BONES, key=lambda n:(center-mids[n]).length)

def ensure_device_root(arm_obj, objs):
    root = bpy.data.objects.get("DEVICE_ROOT")
    if root is None:
        root = bpy.data.objects.new("DEVICE_ROOT", None)
        bpy.context.scene.collection.objects.link(root)

    # Preserve DEVICE_ROOT's current world transform when bone-parenting.
    # v0.5.4 omitted this and shifted the complete device assembly.
    root_world = root.matrix_world.copy()

    root["visual_facing_deg"] = 0.0
    root["movement_heading_deg"] = 0.0
    root["heading_changes_body_rotation"] = False
    root["anchor_motion"] = "vertical"

    device_set = {o for o in objs if o.name.startswith("DEVICE_")}
    top_level = []
    for o in device_set:
        if o.parent not in device_set:
            top_level.append(o)

    # Device meshes are transform-driven children, not skinned body meshes.
    for o in device_set:
        clear_old_skin(o, arm_obj)

    for o in top_level:
        world = o.matrix_world.copy()
        o.parent = root
        o.matrix_world = world

    root.parent = arm_obj
    root.parent_type = "BONE"
    root.parent_bone = "Pelvis"
    root.matrix_world = root_world
    return root, [o.name for o in top_level]

def make_validation_action(arm_obj):
    action = bpy.data.actions.get("RIG_VALIDATION")
    if action:
        bpy.data.actions.remove(action)
    action = bpy.data.actions.new("RIG_VALIDATION")
    arm_obj.animation_data_create()
    arm_obj.animation_data.action = action

    poses = {
        1:  {"UpperArm_L":0.0, "UpperArm_R":0.0, "Thigh_L":0.0, "Thigh_R":0.0},
        15: {"UpperArm_L":math.radians(12), "UpperArm_R":math.radians(-12), "Thigh_L":math.radians(-8), "Thigh_R":math.radians(8)},
        30: {"UpperArm_L":0.0, "UpperArm_R":0.0, "Thigh_L":0.0, "Thigh_R":0.0},
    }
    for frame, values in poses.items():
        for bone_name, ang in values.items():
            pb = arm_obj.pose.bones.get(bone_name)
            if not pb:
                continue
            pb.rotation_mode = "XYZ"
            pb.rotation_euler.y = ang
            pb.keyframe_insert(data_path="rotation_euler", frame=frame)

    bpy.context.scene.frame_start = 1
    bpy.context.scene.frame_end = 30
    bpy.context.scene.render.fps = 30
    return action.name

def main():
    input_blend, output_dir = parse_args()
    output_dir.mkdir(parents=True, exist_ok=True)

    if not input_blend.exists():
        raise FileNotFoundError(input_blend)

    # The .blend is normally already open by Blender CLI, but opening explicitly keeps this script reusable.
    if Path(bpy.data.filepath).resolve() != input_blend:
        bpy.ops.wm.open_mainfile(filepath=str(input_blend))

    objs = mesh_objects()

    # Capture source rest-pose centers before rig changes for regression testing.
    source_device_centers = {
        o.name: obj_world_center(o).copy()
        for o in objs if o.name.startswith("DEVICE_")
    }
    source_elbow_centers = {
        o.name: obj_world_center(o).copy()
        for o in objs if o.name in {"ARM_L_ElbowRing", "ARM_R_ElbowRing"}
    }

    arm = create_armature()
    mids = bone_midpoints(arm)

    assigned = {}
    nearest_assigned = {}
    cloth = {"cape": [], "scarf": []}
    device_objs = []

    for obj in objs:
        g = get_group(obj)
        if g == "DEVICE":
            device_objs.append(obj)
            continue
        if g == "CAPE":
            cloth_skin_cape(obj, arm)
            cloth["cape"].append(obj.name)
            assigned[obj.name] = "CapeUpper/CapeMid/CapeLower"
            continue
        if g == "SCARF":
            cloth_skin_scarf(obj, arm)
            cloth["scarf"].append(obj.name)
            assigned[obj.name] = "Scarf"
            continue

        bone = RIGID_MAP.get(g)
        if bone is None:
            bone = nearest_body_bone(obj, mids)
            nearest_assigned[obj.name] = bone
        rigid_skin(obj, arm, bone)
        assigned[obj.name] = bone

    device_root, device_top = ensure_device_root(arm, objs)

    # Rest-pose transform regression checks.
    device_drift = {}
    for name, before in source_device_centers.items():
        after = obj_world_center(bpy.data.objects[name])
        device_drift[name] = float((after - before).length)

    elbow_drift = {}
    for name, before in source_elbow_centers.items():
        after = obj_world_center(bpy.data.objects[name])
        elbow_drift[name] = float((after - before).length)

    max_device_drift = max(device_drift.values(), default=0.0)
    max_elbow_drift = max(elbow_drift.values(), default=0.0)
    if max_device_drift > 0.0001:
        raise RuntimeError(f"Device rest-pose drift too large: {max_device_drift} m")
    if max_elbow_drift > 0.0001:
        raise RuntimeError(f"Elbow-ring rest-pose drift too large: {max_elbow_drift} m")

    action_name = make_validation_action(arm)

    bpy.context.scene["cherpg_version"] = VERSION
    bpy.context.scene["cherpg_stage"] = "Armature correction / device hierarchy fix"
    bpy.context.scene["blender_visual_front_axis"] = "+Y"
    bpy.context.scene["canonical_glb_forward_axis"] = "-Z"
    bpy.context.scene["movement_heading_independent_of_visual_facing"] = True

    blend_path = output_dir / "cherpg-pawn-protagonist-rigged-v0.5.4.1.blend"
    glb_path = output_dir / "cherpg-pawn-protagonist-rigged-v0.5.4.1.glb"
    report_path = output_dir / "cherpg-pawn-protagonist-v0.5.4.1-rig-report.json"

    bpy.ops.wm.save_as_mainfile(filepath=str(blend_path))

    bpy.ops.export_scene.gltf(
        filepath=str(glb_path),
        export_format="GLB",
        export_yup=True,
        export_normals=True,
        export_materials="EXPORT",
        export_animations=True,
        export_cameras=False,
        export_lights=False,
    )

    report = {
        "version": VERSION,
        "blender_version": bpy.app.version_string,
        "armature_object": arm.name,
        "bone_count": len(arm.data.bones),
        "bones": [b.name for b in arm.data.bones],
        "mesh_objects": len(objs),
        "skinned_mesh_objects": len(assigned),
        "device_mesh_objects": len(device_objs),
        "device_top_level_reparented": device_top,
        "device_rest_pose_drift_m": device_drift,
        "max_device_rest_pose_drift_m": max_device_drift,
        "elbow_ring_rest_pose_drift_m": elbow_drift,
        "max_elbow_ring_rest_pose_drift_m": max_elbow_drift,
        "classification_fixes": {
            "ARM_L_ElbowRing": "FOREARM_L",
            "ARM_R_ElbowRing": "FOREARM_R",
            "device_rule": "only names beginning DEVICE_"
        },
        "axis_metadata": {
            "blender_visual_front": "+Y",
            "canonical_export_forward": "-Z"
        },
        "cloth": cloth,
        "nearest_assignment_count": len(nearest_assigned),
        "nearest_assignments": nearest_assigned,
        "validation_action": action_name,
        "validation_frames": [1,15,30],
        "canonical_direction_device": {
            "body_rotation_when_heading_changes": False,
            "movement_heading_independent_of_visual_facing": True,
            "device_root_attached_to": "Pelvis",
            "anchor_motion": "vertical",
        },
        "outputs": {
            "blend": blend_path.name,
            "glb": glb_path.name,
        },
    }
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    print(f"OUTPUT_GLB={glb_path}")
    print(f"OUTPUT_BLEND={blend_path}")
    print(f"OUTPUT_REPORT={report_path}")

if __name__ == "__main__":
    main()
