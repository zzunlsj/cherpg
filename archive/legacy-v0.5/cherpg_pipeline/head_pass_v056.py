import bpy, bmesh, math, sys, json
from pathlib import Path
from mathutils import Vector

VERSION="0.5.6-head"

def parse_args():
    a=sys.argv
    if "--" not in a: raise RuntimeError("Expected input blend and output blend")
    a=a[a.index("--")+1:]
    return Path(a[0]).resolve(), Path(a[1]).resolve()

def wc(o):
    pts=[o.matrix_world@Vector(c) for c in o.bound_box]
    return sum(pts,Vector())/len(pts)

def xform(o, scale=(1,1,1), translate=(0,0,0), pivot=None):
    if pivot is None: pivot=wc(o)
    inv=o.matrix_world.inverted()
    sx,sy,sz=scale
    d=Vector(translate)
    for v in o.data.vertices:
        w=o.matrix_world@v.co
        r=w-pivot
        w2=pivot+Vector((r.x*sx,r.y*sy,r.z*sz))+d
        v.co=inv@w2
    bm=bmesh.new(); bm.from_mesh(o.data)
    if bm.faces: bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
    bm.to_mesh(o.data); bm.free(); o.data.update()

def do(name,scale=(1,1,1),translate=(0,0,0),pivot=None,changes=None):
    o=bpy.data.objects.get(name)
    if not o or o.type!="MESH": return
    xform(o,scale,translate,pivot)
    if changes is not None: changes[name]={"scale":scale,"translate":translate}

inp,out=parse_args()
if Path(bpy.data.filepath).resolve()!=inp:
    bpy.ops.wm.open_mainfile(filepath=str(inp))

changes={}

# Shared face pivot slightly behind the facial plane.
face_pivot=Vector((0.0,0.035,1.425))

# Face shell: narrower, less spherical, slightly flatter in depth, subtle chin emphasis.
o=bpy.data.objects.get("HEAD_FaceShell")
if o:
    inv=o.matrix_world.inverted()
    for v in o.data.vertices:
        w=o.matrix_world@v.co
        rel=w-face_pivot
        # normalize by rough head radius for local shaping
        z=rel.z
        # narrow lower face, preserve temple width
        lower=max(0.0,min(1.0,(1.44-w.z)/0.16))
        sx=0.97-0.10*lower
        # flatten back/front depth but keep cheek plane
        sy=0.90
        # mild vertical compression
        sz=0.965
        rel=Vector((rel.x*sx, rel.y*sy, rel.z*sz))
        # chin taper: lower central vertices move slightly forward/down
        if w.z<1.385:
            chin=(1.385-w.z)/0.10
            rel.y += 0.010*chin
            rel.z -= 0.004*chin
        v.co=inv@(face_pivot+rel)
    bm=bmesh.new(); bm.from_mesh(o.data)
    if bm.faces: bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
    bm.to_mesh(o.data); bm.free(); o.data.update()
    changes[o.name]={"custom":"jaw taper + face flatten"}

# Back skull: reduce bulbous silhouette and move closer to face shell.
do("HEAD_BackSkull",(0.94,0.90,0.97),(0,0.010,-0.002),changes=changes)

# Eyes: smaller, slightly more recessed and a touch farther apart.
for name,dx in [("HEAD_Eye_L",-0.003),("HEAD_Eye_R",0.003)]:
    do(name,(0.88,0.82,0.90),(dx,-0.004,0.002),changes=changes)

# Lids: thinner, more carved than protruding.
for name,dx in [("HEAD_Lid_L",-0.003),("HEAD_Lid_R",0.003)]:
    do(name,(0.92,0.72,0.72),(dx,-0.003,0.000),changes=changes)

# Brows: shorten and pull toward face; less cartoon block.
for name,dx in [("HEAD_Brow_L",-0.002),("HEAD_Brow_R",0.002)]:
    do(name,(0.88,0.72,0.74),(dx,-0.006,-0.003),changes=changes)

# Nose: narrower and flatter, carved-stone wedge.
do("HEAD_Nose",(0.78,0.72,0.88),(0,-0.004,-0.002),changes=changes)

# Jaw plate and mouth seam: less mask-like.
do("HEAD_JawPlate",(0.90,0.82,0.84),(0,0.004,0.008),changes=changes)
do("HEAD_MouthSeam",(0.78,0.70,0.72),(0,-0.003,0.004),changes=changes)

# Hair locks: reduce spiky anime silhouette while keeping carved stone hair.
for i in range(7):
    name=f"HEAD_HairLock_{i:02d}"
    if bpy.data.objects.get(name):
        do(name,(0.90,0.82,0.82),(0,-0.006,-0.005),changes=changes)

# Helmet: reduce flat pancake brim and open face visibility.
do("HELM_Brim",(0.90,0.90,0.72),(0,0,0.005),changes=changes)
do("HELM_BrimTrim",(0.92,0.92,0.68),(0,0,0.005),changes=changes)
do("HELM_Cap",(0.96,0.96,1.03),(0,0,0.002),changes=changes)
do("HELM_CrownBand",(0.94,0.94,0.88),(0,0,0.004),changes=changes)
do("HELM_PawnSphere",(0.92,0.92,0.92),(0,0,0.006),changes=changes)

# Slightly lift whole eye/brow assembly for youthful proportion.
for name in ["HEAD_Eye_L","HEAD_Eye_R","HEAD_Lid_L","HEAD_Lid_R","HEAD_Brow_L","HEAD_Brow_R"]:
    o=bpy.data.objects.get(name)
    if o: xform(o,(1,1,1),(0,0,0.004))

bpy.context.scene["cherpg_version"]=VERSION
bpy.context.scene["part_pass"]="HEAD_FACE_HELMET"
bpy.context.scene["part_pass_goal"]="youthful carved-stone face, clearer pawn helmet silhouette"

out.parent.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=str(out))
out.with_suffix(".json").write_text(json.dumps({"version":VERSION,"changes":changes},indent=2),encoding="utf-8")
print(json.dumps({"version":VERSION,"changed_objects":len(changes)},indent=2))
