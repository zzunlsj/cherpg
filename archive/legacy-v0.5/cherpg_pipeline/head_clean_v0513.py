import bpy,bmesh,math,json,sys
from pathlib import Path
from mathutils import Vector

VERSION="0.5.13-head-clean"

def parse_args():
    a=sys.argv
    if "--" not in a: raise RuntimeError("expected input output")
    a=a[a.index("--")+1:];return Path(a[0]).resolve(),Path(a[1]).resolve()

def mat_like(*hints):
    for h in hints:
        for m in bpy.data.materials:
            if h.lower() in m.name.lower():return m
    return bpy.data.materials[0] if bpy.data.materials else None

def recalc(o):
    bm=bmesh.new();bm.from_mesh(o.data)
    if bm.faces:bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
    bm.to_mesh(o.data);bm.free();o.data.update()

def arm():return bpy.data.objects.get("RIG_PawnHero")

def skin(o,group="HEAD"):
    a=arm();o["cherpg_group"]=group
    if not a:return
    for vg in list(o.vertex_groups):o.vertex_groups.remove(vg)
    vg=o.vertex_groups.new(name="Head")
    if len(o.data.vertices):vg.add(list(range(len(o.data.vertices))),1.0,"REPLACE")
    for m in list(o.modifiers):
        if m.type=="ARMATURE":o.modifiers.remove(m)
    md=o.modifiers.new("CheRPG_Armature","ARMATURE");md.object=a
    o["cherpg_primary_bone"]="Head";o["cherpg_skin_mode"]="rigid"

def segment_mesh(name,p0,p1,radius,mat):
    p0,p1=Vector(p0),Vector(p1)
    mid=(p0+p1)*0.5;d=p1-p0;L=d.length
    bpy.ops.mesh.primitive_cylinder_add(vertices=16,radius=radius,depth=L,location=mid)
    o=bpy.context.object;o.name=name
    o.rotation_euler=d.to_track_quat("Z","Y").to_euler()
    if mat:o.data.materials.append(mat)
    skin(o,"HEAD")
    return o

def polyline_segments(prefix,pts,radius,mat):
    out=[]
    for i in range(len(pts)-1):
        out.append(segment_mesh(f"{prefix}_{i}",pts[i],pts[i+1],radius,mat))
    return out

def center(o):
    pts=[o.matrix_world@Vector(c) for c in o.bound_box]
    return sum(pts,Vector())/len(pts)

inp,out=parse_args()
if Path(bpy.data.filepath).resolve()!=inp:bpy.ops.wm.open_mainfile(filepath=str(inp))
stone=mat_like("marble","stone");iron=mat_like("iron","metal")
removed=[]

# Remove curve-derived facial marks that can overshoot.
for o in list(bpy.context.scene.objects):
    if o.name.startswith(("HEAD5_Mouth","HEAD5_LowerLip","HEAD6_Nostril","HEAD4_Mouth")):
        removed.append(o.name);bpy.data.objects.remove(o,do_unlink=True)

# Recreate nostrils as tiny fixed cylinders, impossible to overshoot.
segment_mesh("HEAD7_NostrilL",(-0.010,0.111,1.397),(-0.004,0.113,1.396),0.00085,iron)
segment_mesh("HEAD7_NostrilR",(0.004,0.113,1.396),(0.010,0.111,1.397),0.00085,iron)

# Neutral mouth: short segmented crease with a separate subtle stone lower lip.
polyline_segments("HEAD7_Mouth",[
(-0.026,0.102,1.369),(-0.012,0.104,1.368),(0,0.105,1.368),(0.012,0.104,1.368),(0.026,0.102,1.369)
],0.00115,iron)
polyline_segments("HEAD7_LowerLip",[
(-0.015,0.101,1.361),(0,0.103,1.360),(0.015,0.101,1.361)
],0.00110,stone)

# Slightly sculpt lower face to prevent blank mask effect.
face=bpy.data.objects.get("HEAD4_Face")
if face:
    inv=face.matrix_world.inverted()
    for v in face.data.vertices:
        w=face.matrix_world@v.co
        x,y,z=w.x,w.y,w.z
        # shallow lower cheek hollow near mouth corners
        if 1.355<z<1.395 and 0.035<abs(x)<0.075 and y>0.075:
            y-=0.0020
        # chin plane forward slightly
        if z<1.350 and abs(x)<0.045 and y>0.060:
            y+=0.0018
        v.co=inv@Vector((x,y,z))
    recalc(face)

# Tiny smoothing bevel on nose without changing silhouette.
nose=bpy.data.objects.get("HEAD6_Nose")
if nose:
    md=nose.modifiers.new("NoseSoftBevel","BEVEL");md.width=0.0018;md.segments=2
    bpy.context.view_layer.objects.active=nose;bpy.ops.object.modifier_apply(modifier=md.name)

bpy.context.scene["cherpg_version"]=VERSION
bpy.context.scene["part_pass"]="HEAD_CLEAN_FINAL"
bpy.context.scene["part_pass_goal"]="remove curve artifacts, clean mouth and nose, preserve concept-matched head"

out.parent.mkdir(parents=True,exist_ok=True);bpy.ops.wm.save_as_mainfile(filepath=str(out))
out.with_suffix(".json").write_text(json.dumps({"version":VERSION,"removed":removed},ensure_ascii=False,indent=2),encoding="utf-8")
print(json.dumps({"version":VERSION,"removed":removed},ensure_ascii=False,indent=2))
