import bpy, bmesh, json, sys, math
from pathlib import Path
from mathutils import Vector

VERSION="0.5.6-upperbody"

def parse_args():
    a=sys.argv
    if "--" not in a:
        raise RuntimeError("Expected input blend and output blend")
    a=a[a.index("--")+1:]
    return Path(a[0]).resolve(), Path(a[1]).resolve()

def center(o):
    pts=[o.matrix_world@Vector(c) for c in o.bound_box]
    return sum(pts,Vector())/len(pts)

def recalc(o):
    bm=bmesh.new()
    bm.from_mesh(o.data)
    if bm.faces:
        bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
    bm.to_mesh(o.data)
    bm.free()
    o.data.update()

def chest_deform(o):
    inv=o.matrix_world.inverted()
    for v in o.data.vertices:
        w=o.matrix_world@v.co

        # Chest region from waist ~0.90 m to collar ~1.31 m.
        t=max(0.0,min(1.0,(w.z-0.90)/(1.31-0.90)))

        # Stronger taper: narrower waist, broader upper chest.
        width=0.90 + 0.17*t

        # Reduce front/back blockiness while preserving slight upper chest projection.
        depth=0.82 + 0.05*t

        # Pivot near spine center.
        x=w.x*width
        y=-0.018 + (w.y+0.018)*depth

        # Very mild vertical compression to avoid long rectangular torso.
        z=1.105 + (w.z-1.105)*0.975

        v.co=inv@Vector((x,y,z))
    recalc(o)

def scale_about(o, pivot, scale=(1,1,1), translate=(0,0,0)):
    inv=o.matrix_world.inverted()
    sx,sy,sz=scale
    d=Vector(translate)
    for v in o.data.vertices:
        w=o.matrix_world@v.co
        r=w-pivot
        w2=pivot+Vector((r.x*sx,r.y*sy,r.z*sz))+d
        v.co=inv@w2
    recalc(o)

inp,out=parse_args()
if Path(bpy.data.filepath).resolve()!=inp:
    bpy.ops.wm.open_mainfile(filepath=str(inp))

changes={"chest_group":[],"shoulder_group":[]}

# 1) Unified chest deformation so plates/straps/details keep alignment.
for o in bpy.context.scene.objects:
    if o.type!="MESH":
        continue
    if str(o.get("cherpg_group",""))=="CHEST":
        chest_deform(o)
        changes["chest_group"].append(o.name)

# 2) Shoulder cap correction based on upper-arm group and spatial position.
# Only uppermost meshes are affected; lower upper-arm stone remains intact.
for side,sgn in [("L",-1.0),("R",1.0)]:
    g=f"UPPER_ARM_{side}"
    pivot=Vector((0.238*sgn,0.0,1.205))
    for o in bpy.context.scene.objects:
        if o.type!="MESH" or str(o.get("cherpg_group",""))!=g:
            continue
        c=center(o)
        if c.z >= 1.105:
            # Reduce spherical pauldron size and bring it closer to chest.
            scale_about(
                o,pivot,
                scale=(0.88,0.84,0.90),
                translate=(-0.014*sgn,0.004,-0.010)
            )
            changes["shoulder_group"].append(o.name)

# 3) Sternum gets a slightly stronger central stone wedge rather than a flat board.
stern=bpy.data.objects.get("TORSO_Sternum")
if stern:
    p=center(stern)
    scale_about(stern,p,scale=(0.92,0.86,1.02),translate=(0,0.004,0))
    changes["sternum"]="narrower/deeper central wedge"

# 4) Chest plates: subtle downward-inner bevel through geometry squeeze.
for name,sgn in [("TORSO_ChestPlate_L",-1),("TORSO_ChestPlate_R",1)]:
    o=bpy.data.objects.get(name)
    if not o: continue
    inv=o.matrix_world.inverted()
    c=center(o)
    for v in o.data.vertices:
        w=o.matrix_world@v.co
        # pull lower-inner vertices toward sternum to create sloped armor silhouette
        lower=max(0.0,min(1.0,(1.19-w.z)/0.18))
        inward=0.012*lower
        w.x -= sgn*inward
        v.co=inv@w
    recalc(o)

# 5) Ribs: flatten depth further and pull closer to torso.
for o in bpy.context.scene.objects:
    if o.type!="MESH" or not o.name.startswith("TORSO_Rib_"):
        continue
    p=center(o)
    scale_about(o,p,scale=(0.94,0.78,0.95),translate=(0,0.006,0))

bpy.context.scene["cherpg_version"]=VERSION
bpy.context.scene["part_pass"]="UPPER_BODY_SHOULDERS"
bpy.context.scene["part_pass_goal"]="tapered ribcage, reduced boxiness, integrated shoulders"

out.parent.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=str(out))
out.with_suffix(".json").write_text(json.dumps({"version":VERSION,"changes":changes},ensure_ascii=False,indent=2),encoding="utf-8")
print(json.dumps({"version":VERSION,"chest_objects":len(changes["chest_group"]),"shoulder_objects":len(changes["shoulder_group"])},indent=2))
