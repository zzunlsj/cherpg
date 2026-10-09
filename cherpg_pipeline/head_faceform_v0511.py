"""CheRPG v0.5.11 face silhouette refinement after v0.5.10."""
import bpy,bmesh,sys,math,json
from pathlib import Path
from mathutils import Vector
a=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
if len(a)!=2: raise RuntimeError("Usage: -- source.blend output.blend")
src,dst=[Path(p).resolve() for p in a]
if not src.is_file() or src==dst: raise RuntimeError("Invalid source/destination")
if Path(bpy.data.filepath).resolve()!=src: bpy.ops.wm.open_mainfile(filepath=str(src))
face=bpy.data.objects.get("HEAD2_FaceShell")
rig=bpy.data.objects.get("RIG_PawnHero")
if face is None or face.type!="MESH" or rig is None or rig.type!="ARMATURE":
    raise RuntimeError("v0.5.10 head shell or rig unavailable")
if len(face.data.vertices)<100: raise RuntimeError("Face shell unexpectedly small")
def weight(value,center,sigma):
    return math.exp(-((value-center)/sigma)**2)
inv=face.matrix_world.inverted()
before=[tuple(face.matrix_world@v.co) for v in face.data.vertices]
for v in face.data.vertices:
    p=face.matrix_world@v.co
    x,y,z=p.x,p.y,p.z
    sign=-1 if x<0 else 1
    ax=abs(x)
    front=max(0.0,min(1.0,(y-0.025)/0.080))
    forehead=weight(z,1.486,0.030)
    temple=weight(z,1.455,0.030)*weight(ax,0.092,0.018)
    cheek=weight(z,1.424,0.030)*weight(ax,0.060,0.024)
    jaw=weight(z,1.372,0.028)*weight(ax,0.055,0.028)
    chin=weight(z,1.347,0.020)*weight(ax,0,0.050)
    x += sign*(0.0028*forehead-0.0032*temple+0.0030*cheek-0.0038*jaw)
    y += front*(0.0012*cheek-0.0008*jaw+0.0005*chin)-0.0006*forehead
    z += 0.0018*chin
    v.co=inv@Vector((x,y,z))
bm=bmesh.new();bm.from_mesh(face.data)
bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
bm.to_mesh(face.data);bm.free();face.data.update()
after=[tuple(face.matrix_world@v.co) for v in face.data.vertices]
max_motion=max((Vector(q)-Vector(p)).length for p,q in zip(before,after))
if max_motion>0.015: raise RuntimeError("Exceeded conservative movement limit")
bpy.context.scene["cherpg_version"]="0.5.11-faceform"
bpy.context.scene["part_pass"]="HEAD_FACEFORM"
dst.parent.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=str(dst))
report={"version":"0.5.11","vertex_count":len(before),"max_vertex_motion_m":max_motion,"source":src.name,"result":dst.name,"warning":"Concept-art match requires image-based visual review"}
dst.with_suffix(".json").write_text(json.dumps(report,indent=2),encoding="utf-8")
print(json.dumps(report))
