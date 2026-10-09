import bpy, bmesh, math, json, sys
from pathlib import Path
from mathutils import Vector

VERSION="0.5.7-head"

def parse_args():
    a=sys.argv
    if "--" not in a: raise RuntimeError("Expected input blend and output blend")
    a=a[a.index("--")+1:]
    return Path(a[0]).resolve(), Path(a[1]).resolve()

def recalc(o):
    if not o or o.type!="MESH": return
    bm=bmesh.new(); bm.from_mesh(o.data)
    if bm.faces: bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    bm.to_mesh(o.data); bm.free(); o.data.update()

def center(o):
    pts=[o.matrix_world@Vector(c) for c in o.bound_box]
    return sum(pts, Vector())/len(pts)

def scale_about(o,pivot,scale=(1,1,1),translate=(0,0,0)):
    inv=o.matrix_world.inverted()
    sx,sy,sz=scale; d=Vector(translate)
    for v in o.data.vertices:
        w=o.matrix_world@v.co
        r=w-pivot
        v.co=inv@(pivot+Vector((r.x*sx,r.y*sy,r.z*sz))+d)
    recalc(o)

def mat_like(name_hint, fallback=None):
    for m in bpy.data.materials:
        if name_hint.lower() in m.name.lower():
            return m
    return fallback or (bpy.data.materials[0] if bpy.data.materials else None)

def add_box(name, loc, dims, mat=None, bevel=0.0, rot=(0,0,0)):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot)
    o=bpy.context.object; o.name=name; o.dimensions=dims
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if bevel>0:
        mod=o.modifiers.new("Bevel","BEVEL"); mod.width=bevel; mod.segments=2
        bpy.context.view_layer.objects.active=o
        bpy.ops.object.modifier_apply(modifier=mod.name)
    if mat: o.data.materials.append(mat)
    return o

def add_cylinder(name, loc, radius, depth, mat=None, rot=(0,0,0), verts=32):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=radius, depth=depth, location=loc, rotation=rot)
    o=bpy.context.object; o.name=name
    if mat: o.data.materials.append(mat)
    return o

inp,out=parse_args()
if Path(bpy.data.filepath).resolve()!=inp:
    bpy.ops.wm.open_mainfile(filepath=str(inp))

changes={}
stone=mat_like("stone") or mat_like("marble")
iron=mat_like("iron")
brass=mat_like("brass")

# --- A. FACE SHELL: stronger carved planes, less mask/blob ---
face=bpy.data.objects.get("HEAD_FaceShell")
if face:
    inv=face.matrix_world.inverted()
    for v in face.data.vertices:
        w=face.matrix_world@v.co
        x,y,z=w.x,w.y,w.z

        # Normalize rough facial zones.
        ax=abs(x)

        # Temple/cheek plane separation.
        if z>1.445:
            y -= 0.004*(1.0-min(ax/0.11,1.0))
        elif 1.385<z<=1.445:
            cheek=max(0.0,1.0-abs(ax-0.060)/0.060)
            y += 0.010*cheek
        elif z<=1.385:
            # Chin becomes compact wedge.
            taper=max(0.0,min(1.0,(1.385-z)/0.085))
            x *= (1.0-0.12*taper)
            y += 0.010*taper

        # Side planes flatter than front plane.
        if ax>0.075:
            side=(ax-0.075)/0.055
            y -= 0.010*max(0.0,min(side,1.0))

        # Slight vertical shortening below nose.
        if z<1.405:
            z=1.405+(z-1.405)*0.96

        v.co=inv@Vector((x,y,z))
    recalc(face)
    changes["HEAD_FaceShell"]="carved facial planes + compact jaw"

# --- B. EYE SOCKET: recess eye cores and tighten lids/brows ---
for name in ["HEAD_Eye_L","HEAD_Eye_R"]:
    o=bpy.data.objects.get(name)
    if o:
        scale_about(o,center(o),(0.88,0.74,0.86),(0,-0.006,0.001))
        changes[name]="smaller/recessed eye core"
for name in ["HEAD_Lid_L","HEAD_Lid_R"]:
    o=bpy.data.objects.get(name)
    if o:
        scale_about(o,center(o),(0.92,0.68,0.78),(0,-0.004,0))
        changes[name]="thin carved lid"
for name in ["HEAD_Brow_L","HEAD_Brow_R"]:
    o=bpy.data.objects.get(name)
    if o:
        scale_about(o,center(o),(0.86,0.72,0.76),(0,-0.005,-0.002))
        changes[name]="reduced block brow"

# New recessed dark-metal orbital liners.
for side,x in [("L",-0.038),("R",0.038)]:
    o=add_cylinder(
        f"HEAD_OrbitFrame_{side}",
        (x,0.123,1.435),
        0.029,0.012,iron,
        rot=(math.radians(90),0,0),
        verts=32
    )
    o.scale.z=0.72
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    o["cherpg_group"]="HEAD"
    changes[o.name]="new iron orbital liner"

# --- C. NOSE / MOUTH / JAW ---
nose=bpy.data.objects.get("HEAD_Nose")
if nose:
    scale_about(nose,center(nose),(0.80,0.70,0.90),(0,-0.004,-0.002))
    changes[nose.name]="narrow carved ridge"
jaw=bpy.data.objects.get("HEAD_JawPlate")
if jaw:
    scale_about(jaw,center(jaw),(0.92,0.82,0.88),(0,0.003,0.006))
    changes[jaw.name]="compact stone jaw wedge"
mouth=bpy.data.objects.get("HEAD_MouthSeam")
if mouth:
    scale_about(mouth,center(mouth),(0.80,0.65,0.65),(0,-0.004,0.004))
    changes[mouth.name]="short recessed mouth seam"

# Add tiny chin keel / center plane.
chin=add_box("HEAD_ChinKeel",(0,0.103,1.342),(0.052,0.025,0.040),stone,bevel=0.006)
chin["cherpg_group"]="HEAD"
changes[chin.name]="new center chin plane"

# --- D. TEMPLE / SIDE STRUCTURE ---
for side,x,sgn in [("L",-0.103,-1),("R",0.103,1)]:
    plate=add_box(
        f"HEAD_TemplePlate_{side}",
        (x,0.008,1.445),
        (0.028,0.095,0.095),
        iron,bevel=0.008,
        rot=(0,math.radians(7)*sgn,0)
    )
    plate["cherpg_group"]="HEAD"
    changes[plate.name]="new side structural iron plate"

    pin=add_cylinder(
        f"HEAD_TemplePin_{side}",
        (x*1.015,0.015,1.447),
        0.012,0.032,brass,
        rot=(0,math.radians(90),0),
        verts=24
    )
    pin["cherpg_group"]="HEAD"
    changes[pin.name]="brass temple pin"

# --- E. HELMET / PAWN CAP: integrate, less pancake, stronger pawn read ---
for name,scale,trans in [
    ("HELM_Brim",(0.93,0.93,0.76),(0,0,0.008)),
    ("HELM_BrimTrim",(0.94,0.94,0.72),(0,0,0.008)),
    ("HELM_Cap",(0.98,0.98,1.06),(0,0,0.004)),
    ("HELM_CrownBand",(0.96,0.96,0.82),(0,0,0.006)),
    ("HELM_PawnSphere",(0.94,0.94,0.96),(0,0,0.010)),
]:
    o=bpy.data.objects.get(name)
    if o:
        scale_about(o,center(o),scale,trans)
        changes[name]="refined pawn-cap proportion"

# Add central forehead transition plate to visually merge cap and face.
fore=add_box("HELM_ForeheadBridge",(0,0.047,1.518),(0.082,0.036,0.050),stone,bevel=0.010)
fore["cherpg_group"]="HELMET"
changes[fore.name]="new cap-to-face transition block"

# --- F. HAIR/STONE FRINGE: reduce anime spikes further and cluster under brim ---
for o in bpy.context.scene.objects:
    if o.type=="MESH" and o.name.startswith("HEAD_HairLock_"):
        scale_about(o,center(o),(0.90,0.78,0.80),(0,-0.008,-0.006))
        changes[o.name]="subdued carved stone fringe"

# --- G. Smooth shading only on face shell + eyes; keep hard stone planes elsewhere ---
for name in ["HEAD_FaceShell","HEAD_Eye_L","HEAD_Eye_R"]:
    o=bpy.data.objects.get(name)
    if o:
        for p in o.data.polygons: p.use_smooth=True

bpy.context.scene["cherpg_version"]=VERSION
bpy.context.scene["part_pass"]="HEAD_SCULPT_B"
bpy.context.scene["part_pass_goal"]="illustration-grade head silhouette, carved planes, layered eye sockets, integrated pawn cap"

out.parent.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=str(out))
out.with_suffix(".json").write_text(json.dumps({"version":VERSION,"changes":changes},ensure_ascii=False,indent=2),encoding="utf-8")
print(json.dumps({"version":VERSION,"changed_objects":len(changes)},indent=2))
