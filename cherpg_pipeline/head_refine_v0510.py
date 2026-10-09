"""CheRPG v0.5.10 head polish pass following v0.5.9."""
import bpy, bmesh, json, math, sys
from pathlib import Path
from mathutils import Vector

args = sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
if len(args) != 2:
    raise RuntimeError("Expected input.blend output.blend")
src, dst = [Path(p).resolve() for p in args]
if src == dst or not src.is_file():
    raise RuntimeError("Invalid input/output")
if Path(bpy.data.filepath).resolve() != src:
    bpy.ops.wm.open_mainfile(filepath=str(src))
face = bpy.data.objects.get("HEAD2_FaceShell")
rig = bpy.data.objects.get("RIG_PawnHero")
if not face or face.type != "MESH" or not rig or rig.type != "ARMATURE":
    raise RuntimeError("v0.5.9 face shell or rig missing")
for name in ("HEAD3_Eye_L", "HEAD3_Eye_R", "HEAD3_Nose"):
    if bpy.data.objects.get(name) is None:
        raise RuntimeError("Missing v0.5.9 component: " + name)

inv = face.matrix_world.inverted()
for v in face.data.vertices:
    p = face.matrix_world @ v.co
    x,y,z = p.x,p.y,p.z
    ax=abs(x)
    cheek=math.exp(-((z-1.420)/0.028)**2)*math.exp(-((ax-0.061)/0.030)**2)
    brow=math.exp(-((z-1.474)/0.018)**2)*math.exp(-((ax-0.041)/0.037)**2)
    temple=math.exp(-((z-1.459)/0.029)**2)*math.exp(-((ax-0.093)/0.013)**2)
    front=max(0.,min(1.,(y-0.030)/0.07))
    v.co=inv @ Vector((x,y+front*(0.0022*cheek+0.0011*brow-0.0012*temple),z))
bm=bmesh.new()
bm.from_mesh(face.data)
bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
bm.to_mesh(face.data)
bm.free()
face.data.update()

parts=[]
for o in bpy.data.objects:
    if o.type != "MESH" or not o.name.startswith(("HEAD3_","HELM3_")):
        continue
    arm_mods=[m for m in o.modifiers if m.type=="ARMATURE"]
    if not any(m.object==rig for m in arm_mods):
        for m in arm_mods:
            o.modifiers.remove(m)
        m=o.modifiers.new("CheRPG_Armature","ARMATURE")
        m.object=rig
    vg=o.vertex_groups.get("Head")
    if vg is None:
        vg=o.vertex_groups.new(name="Head")
    if len(o.data.vertices):
        vg.add(list(range(len(o.data.vertices))),1.0,"REPLACE")
    o["cherpg_primary_bone"]="Head"
    parts.append(o.name)
if len(parts)<10:
    raise RuntimeError("Insufficient head parts")
bpy.context.scene["cherpg_version"]="0.5.10-head-refine"
bpy.context.scene["part_pass"]="HEAD_REFINEMENT_D"
dst.parent.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=str(dst))
report={"version":"0.5.10","face_vertices":len(face.data.vertices),"rigged_head_parts":parts}
dst.with_suffix(".json").write_text(json.dumps(report,indent=2),encoding="utf-8")
print(json.dumps(report))
