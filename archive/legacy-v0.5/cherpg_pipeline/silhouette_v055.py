import bpy, bmesh, json, sys
from pathlib import Path
from mathutils import Vector

VERSION="0.5.5"

def parse_args():
    a=sys.argv
    if "--" not in a: raise RuntimeError("Expected input blend and output blend")
    a=a[a.index("--")+1:]
    return Path(a[0]).resolve(), Path(a[1]).resolve()

def world_center(o):
    pts=[o.matrix_world@Vector(c) for c in o.bound_box]
    return sum(pts,Vector())/len(pts)

def transform_mesh_world(o, scale=(1,1,1), translate=(0,0,0), pivot=None):
    if pivot is None:
        pivot=world_center(o)
    inv=o.matrix_world.inverted()
    sx,sy,sz=scale
    d=Vector(translate)
    for v in o.data.vertices:
        w=o.matrix_world@v.co
        rel=w-pivot
        w2=pivot+Vector((rel.x*sx,rel.y*sy,rel.z*sz))+d
        v.co=inv@w2
    o.data.update()

def recalc(o):
    bm=bmesh.new(); bm.from_mesh(o.data)
    if bm.faces: bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
    bm.to_mesh(o.data); bm.free(); o.data.update()

def xf(name,scale=(1,1,1),translate=(0,0,0)):
    o=bpy.data.objects.get(name)
    if not o or o.type!="MESH": return False
    transform_mesh_world(o,scale,translate)
    recalc(o)
    return True

def group_xf(names,scale=(1,1,1),translate=(0,0,0),pivot=None):
    objs=[bpy.data.objects.get(n) for n in names]
    objs=[o for o in objs if o and o.type=="MESH"]
    if not objs: return []
    if pivot is None:
        pivot=sum((world_center(o) for o in objs),Vector())/len(objs)
    for o in objs:
        transform_mesh_world(o,scale,translate,pivot)
        recalc(o)
    return [o.name for o in objs]

inp,out=parse_args()
if Path(bpy.data.filepath).resolve()!=inp:
    bpy.ops.wm.open_mainfile(filepath=str(inp))

changes={}

# 1) Helmet: reduce pancake brim, keep pawn silhouette.
for n,s in {
    "HELM_Brim":(0.88,0.88,0.88),
    "HELM_BrimTrim":(0.90,0.90,0.90),
    "HELM_CrownBand":(0.96,0.96,0.92),
    "HELM_PawnSphere":(0.96,0.96,0.96),
}.items():
    if xf(n,s): changes[n]={"scale":s}

# 2) Face: slightly narrower/flatter vertically, more readable projection.
if xf("HEAD_FaceShell",(0.96,1.055,0.95),(0,0,0.004)):
    changes["HEAD_FaceShell"]={"scale":(0.96,1.055,0.95),"translate":(0,0,0.004)}
for n in ["HEAD_Eye_L","HEAD_Eye_R","HEAD_Lid_L","HEAD_Lid_R","HEAD_Brow_L","HEAD_Brow_R"]:
    if xf(n,(1.0,1.0,1.0),(0,0.007,0.0)):
        changes[n]={"translate":(0,0.007,0)}
if xf("HEAD_Nose",(0.90,0.88,0.94),(0,0.004,-0.002)):
    changes["HEAD_Nose"]={"scale":(0.90,0.88,0.94),"translate":(0,0.004,-0.002)}
if xf("HEAD_JawPlate",(0.94,0.95,0.90),(0,0.005,0.006)):
    changes["HEAD_JawPlate"]={"scale":(0.94,0.95,0.90),"translate":(0,0.005,0.006)}

# 3) Scarf collar: reduce ring/donut silhouette, keep cloth tail.
for n,s in {
    "CLOTH_ScarfCollar":(0.93,0.93,0.88),
    "CLOTH_ScarfCollar2":(0.91,0.91,0.88),
}.items():
    if xf(n,s): changes[n]={"scale":s}

# 4) Torso: slightly broader but thinner; flatten front plates a little.
if xf("CORE_Torso",(1.08,0.90,0.98)):
    changes["CORE_Torso"]={"scale":(1.08,0.90,0.98)}
for n in ["TORSO_ChestPlate_L","TORSO_ChestPlate_R"]:
    if xf(n,(1.035,0.82,0.95)):
        changes[n]={"scale":(1.035,0.82,0.95)}
for n in ["TORSO_AbPlate_0","TORSO_AbPlate_1","TORSO_AbPlate_2"]:
    if xf(n,(1.02,0.82,0.90)):
        changes[n]={"scale":(1.02,0.82,0.90)}

# 5) Backpack: pull toward the back and reduce boxiness.
if xf("GEAR_Backpack",(0.90,0.76,0.88),(0,0.022,0.015)):
    changes["GEAR_Backpack"]={"scale":(0.90,0.76,0.88),"translate":(0,0.022,0.015)}
back_names=["GEAR_Bedroll","GEAR_BedrollBand_L","GEAR_BedrollBand_R"]
done=group_xf(back_names,(0.88,0.84,0.84),(0,0.026,0.008))
for n in done: changes[n]={"group_scale":(0.88,0.84,0.84),"translate":(0,0.026,0.008)}

# 6) Boots: reduce stacked-ring appearance, emphasize boot body.
for side in ["L","R"]:
    n=f"LEG_{side}_AnkleCuff"
    if xf(n,(0.82,0.82,0.66),(0,0,-0.010)):
        changes[n]={"scale":(0.82,0.82,0.66),"translate":(0,0,-0.010)}
    n=f"LEG_{side}_BootUpper"
    if xf(n,(0.94,0.92,0.70),(0,0,-0.008)):
        changes[n]={"scale":(0.94,0.92,0.70),"translate":(0,0,-0.008)}
    n=f"LEG_{side}_BootBody"
    if xf(n,(1.03,1.00,1.12),(0,0,0.002)):
        changes[n]={"scale":(1.03,1.00,1.12),"translate":(0,0,0.002)}

# 7) Compact hip direction indicator only; folded belt segments stay untouched.
ring_names=["DEVICE_OuterRing","DEVICE_InnerRing","DEVICE_CoreDisk","DEVICE_DiamondCore"]
done=group_xf(ring_names,(0.90,0.90,0.90),(-0.012,-0.004,0.006),Vector((0.165,0.15,0.865)))
for n in done: changes[n]={"group_scale":(0.90,0.90,0.90),"translate":(-0.012,-0.004,0.006)}

bpy.context.scene["cherpg_version"]=VERSION
bpy.context.scene["cherpg_stage"]="silhouette correction pass"
bpy.context.scene["silhouette_goal"]="reduce blockiness and ring stacking while preserving pawn identity"

out.parent.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=str(out))
report=out.with_suffix(".json")
report.write_text(json.dumps({"version":VERSION,"changes":changes},indent=2),encoding="utf-8")
print(json.dumps({"version":VERSION,"changed_objects":len(changes),"changes":changes},indent=2))
