import bpy, bmesh, json, sys
from pathlib import Path
from mathutils import Vector

VERSION="0.5.6-arms"

def parse_args():
    a=sys.argv
    if "--" not in a: raise RuntimeError("Expected input blend and output blend")
    a=a[a.index("--")+1:]
    return Path(a[0]).resolve(), Path(a[1]).resolve()

def center(o):
    pts=[o.matrix_world@Vector(c) for c in o.bound_box]
    return sum(pts,Vector())/len(pts)

def recalc(o):
    bm=bmesh.new(); bm.from_mesh(o.data)
    if bm.faces: bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
    bm.to_mesh(o.data); bm.free(); o.data.update()

def radial_taper(o, a, b, r0, r1, length_scale=1.0, offset=Vector((0,0,0))):
    # Deform around the bone axis a->b while preserving the part's orientation.
    axis=b-a
    L=max(axis.length,1e-6)
    n=axis/L
    mid=(a+b)*0.5
    inv=o.matrix_world.inverted()
    for v in o.data.vertices:
        w=o.matrix_world@v.co
        rel=w-a
        s=rel.dot(n)
        t=max(0.0,min(1.0,s/L))
        along=n*s
        radial=rel-along
        r=r0+(r1-r0)*t
        # scale length around midpoint along axis
        new_s=(s-L*0.5)*length_scale+L*0.5
        w2=a+n*new_s+radial*r+offset
        v.co=inv@w2
    recalc(o)

def scale_about(o,pivot,scale=(1,1,1),translate=(0,0,0)):
    sx,sy,sz=scale; inv=o.matrix_world.inverted(); d=Vector(translate)
    for v in o.data.vertices:
        w=o.matrix_world@v.co; r=w-pivot
        v.co=inv@(pivot+Vector((r.x*sx,r.y*sy,r.z*sz))+d)
    recalc(o)

inp,out=parse_args()
if Path(bpy.data.filepath).resolve()!=inp:
    bpy.ops.wm.open_mainfile(filepath=str(inp))

# Blender-space joints from the known rig.
J={
"L":{"shoulder":Vector((-0.238,0,1.205)),"elbow":Vector((-0.355,0,1.005)),"wrist":Vector((-0.405,0.006,0.805)),"hand":Vector((-0.410,0.015,0.735))},
"R":{"shoulder":Vector((0.238,0,1.205)),"elbow":Vector((0.355,0,1.005)),"wrist":Vector((0.405,0.006,0.805)),"hand":Vector((0.410,0.015,0.735))}
}
changes={"upper":[],"forearm":[],"hand":[],"rings":[]}

for side in ("L","R"):
    # Upper arm: leave shoulder cap (high center) alone; slim lower upper arm.
    for o in bpy.context.scene.objects:
        if o.type!="MESH" or str(o.get("cherpg_group",""))!=f"UPPER_ARM_{side}":
            continue
        c=center(o)
        if c.z < 1.11:
            radial_taper(o,J[side]["shoulder"],J[side]["elbow"],0.90,0.84,0.99)
            changes["upper"].append(o.name)

    # Forearm: stronger taper toward wrist, less cylindrical.
    for o in bpy.context.scene.objects:
        if o.type!="MESH" or str(o.get("cherpg_group",""))!=f"FOREARM_{side}":
            continue
        if "ElbowRing" in o.name:
            scale_about(o,J[side]["elbow"],(0.84,0.84,0.62))
            changes["rings"].append(o.name)
            continue
        radial_taper(o,J[side]["elbow"],J[side]["wrist"],0.92,0.78,1.00)
        changes["forearm"].append(o.name)

    # Hand/fingers: slightly shorter along wrist->hand direction and thicker radially.
    for o in bpy.context.scene.objects:
        if o.type!="MESH" or str(o.get("cherpg_group",""))!=f"HAND_{side}":
            continue
        radial_taper(o,J[side]["wrist"],J[side]["hand"],1.08,1.06,0.90)
        changes["hand"].append(o.name)

# Extra cleanup of visibly ring-like wrist pieces if their names reveal them.
for o in bpy.context.scene.objects:
    if o.type!="MESH": continue
    n=o.name.lower()
    g=str(o.get("cherpg_group",""))
    if ("wrist" in n or "cuff" in n) and g in {"FOREARM_L","FOREARM_R","HAND_L","HAND_R"}:
        p=center(o)
        scale_about(o,p,(0.90,0.90,0.78))
        changes["rings"].append(o.name)

bpy.context.scene["cherpg_version"]=VERSION
bpy.context.scene["part_pass"]="ARMS_HANDS"
bpy.context.scene["part_pass_goal"]="tapered mechanical arms, reduced ring stacking, compact hands"

out.parent.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=str(out))
out.with_suffix(".json").write_text(json.dumps({"version":VERSION,"changes":changes},ensure_ascii=False,indent=2),encoding="utf-8")
print(json.dumps({"version":VERSION,**{k:len(v) for k,v in changes.items()}},indent=2))
