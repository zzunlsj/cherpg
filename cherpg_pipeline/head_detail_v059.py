import bpy,bmesh,math,json,sys
from pathlib import Path
from mathutils import Vector

VERSION="0.5.9-head-detail"

def parse_args():
    a=sys.argv
    if "--" not in a: raise RuntimeError("Expected input blend output blend")
    a=a[a.index("--")+1:]
    return Path(a[0]).resolve(),Path(a[1]).resolve()

def recalc(o):
    bm=bmesh.new(); bm.from_mesh(o.data)
    if bm.faces: bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
    bm.to_mesh(o.data); bm.free(); o.data.update()

def mat_like(*hints):
    for h in hints:
        for m in bpy.data.materials:
            if h.lower() in m.name.lower(): return m
    return bpy.data.materials[0] if bpy.data.materials else None

def arm():
    return bpy.data.objects.get("RIG_PawnHero")

def skin(o,bone="Head"):
    a=arm()
    if not a:return
    for vg in list(o.vertex_groups): o.vertex_groups.remove(vg)
    vg=o.vertex_groups.new(name=bone)
    if len(o.data.vertices): vg.add(list(range(len(o.data.vertices))),1.0,"REPLACE")
    for m in list(o.modifiers):
        if m.type=="ARMATURE": o.modifiers.remove(m)
    md=o.modifiers.new("CheRPG_Armature","ARMATURE"); md.object=a
    o["cherpg_group"]="HEAD"; o["cherpg_primary_bone"]=bone

def assign(o,mat,group="HEAD"):
    if mat:o.data.materials.append(mat)
    o["cherpg_group"]=group
    skin(o,"Head")
    o["cherpg_group"]=group
    return o

def remove_prefix(prefixes):
    for o in list(bpy.context.scene.objects):
        if o.type=="MESH" and any(o.name.startswith(p) for p in prefixes):
            bpy.data.objects.remove(o,do_unlink=True)

def add_curve(name,pts,bev,mat,group="HEAD"):
    cu=bpy.data.curves.new(name+"Curve","CURVE"); cu.dimensions="3D"; cu.bevel_depth=bev; cu.bevel_resolution=3
    sp=cu.splines.new("BEZIER"); sp.bezier_points.add(len(pts)-1)
    for bp,p in zip(sp.bezier_points,pts):
        bp.co=p; bp.handle_left_type="AUTO"; bp.handle_right_type="AUTO"
    o=bpy.data.objects.new(name,cu); bpy.context.scene.collection.objects.link(o)
    if mat:o.data.materials.append(mat)
    bpy.context.view_layer.objects.active=o; o.select_set(True); bpy.ops.object.convert(target="MESH")
    o=bpy.context.object; o["cherpg_group"]=group; skin(o,"Head"); o["cherpg_group"]=group
    return o

def almond(name,cx,cy,cz,w,h,depth,mat,group="HEAD",segments=16):
    # lens-like extruded almond in X/Z, thickness along Y
    ring=[]
    for k in range(segments):
        t=2*math.pi*k/segments
        x=math.cos(t)
        z=math.sin(t)
        # sharpen lateral tips, soften top/bottom
        shape=(1-abs(x))**0.35
        zz=z*shape
        ring.append((cx+w*x,cy-depth/2,cz+h*zz))
    verts=ring+[(x,cy+depth/2,z) for x,_,z in ring]
    faces=[]
    for k in range(segments):
        nk=(k+1)%segments
        faces.append((k,nk,segments+nk,segments+k))
    faces.append(tuple(range(segments-1,-1,-1)))
    faces.append(tuple(range(segments,2*segments)))
    me=bpy.data.meshes.new(name+"Mesh"); me.from_pydata(verts,[],faces); me.update()
    o=bpy.data.objects.new(name,me); bpy.context.scene.collection.objects.link(o); recalc(o)
    for p in me.polygons:p.use_smooth=True
    return assign(o,mat,group)

def lock_mesh(name,rootx,tipx,rootz,tipz,width,depth,mat):
    # tapered front-facing prism, root wide and tip pointed
    y0=0.108; y1=0.132
    rl=rootx-width/2; rr=rootx+width/2
    verts=[
      (rl,y0,rootz),(rr,y0,rootz),(tipx,y0,tipz),
      (rl,y1,rootz),(rr,y1,rootz),(tipx,y1,tipz)
    ]
    faces=[(0,1,2),(3,5,4),(0,3,4,1),(1,4,5,2),(2,5,3,0)]
    me=bpy.data.meshes.new(name+"Mesh"); me.from_pydata(verts,[],faces); me.update()
    o=bpy.data.objects.new(name,me); bpy.context.scene.collection.objects.link(o)
    md=o.modifiers.new("Bevel","BEVEL"); md.width=0.0045; md.segments=2
    bpy.context.view_layer.objects.active=o; bpy.ops.object.modifier_apply(modifier=md.name)
    return assign(o,mat,"HEAD")

inp,out=parse_args()
if Path(bpy.data.filepath).resolve()!=inp:bpy.ops.wm.open_mainfile(filepath=str(inp))
stone=mat_like("marble","stone"); iron=mat_like("iron","metal"); brass=mat_like("brass","gold"); amber=mat_like("amber","eye","glow") or brass
changes=[]

# 1. Refine the rebuilt face shell into a more youthful carved head.
face=bpy.data.objects.get("HEAD2_FaceShell")
if face:
    inv=face.matrix_world.inverted()
    for v in face.data.vertices:
        w=face.matrix_world@v.co
        x,y,z=w.x,w.y,w.z
        az=abs(x)
        # Broad forehead, narrow temples, pronounced cheek plane, compact jaw.
        if z>1.470:
            x*=1.025
            y-=0.002
        if 1.420<z<1.465 and 0.045<az<0.095:
            # cheekbone: widen and bring forward
            sign=1 if x>=0 else -1
            x+=sign*0.0045
            y+=0.007
        if 1.405<z<1.475 and az>0.082:
            y-=0.004
        if z<1.392:
            t=max(0,min(1,(1.392-z)/0.085))
            x*=1.0-0.20*t
            y+=0.006*t
            # shorten and flatten lower face
            z=1.392+(z-1.392)*0.80
        if z<1.340:
            z=1.340+(z-1.340)*0.35
        # subtle front facial plane: reduce bulbous center except cheeks
        if y>0.075 and z>1.390:
            y=0.075+(y-0.075)*0.88
        v.co=inv@Vector((x,y,z))
    recalc(face)
    changes.append("face planes/jaw")

# 2. Replace old lenses/sockets/lids/brows with almond eye construction.
remove_prefix(["HEAD2_Socket_","HEAD2_Eye_","HEAD2_UpperLid_","HEAD2_LowerLid_","HEAD2_Brow_"])
for side,x,tilt in [("L",-0.037,0.002),("R",0.037,-0.002)]:
    almond(f"HEAD3_Socket_{side}",x,0.108,1.445,0.030,0.019,0.010,iron)
    almond(f"HEAD3_Eye_{side}",x,0.115,1.445,0.0215,0.013,0.006,amber)
    # stone eyelids follow almond silhouette, upper stronger than lower
    upper=[(x-0.027,0.116,1.451+tilt),(x,0.121,1.461),(x+0.027,0.116,1.451-tilt)]
    lower=[(x-0.023,0.115,1.440),(x,0.118,1.436),(x+0.023,0.115,1.440)]
    add_curve(f"HEAD3_UpperLid_{side}",upper,0.0043,stone)
    add_curve(f"HEAD3_LowerLid_{side}",lower,0.0027,stone)
    # brow ridge as carved stone strip, slightly serious but not angry
    if side=="L":
        brow=[(x-0.026,0.106,1.479),(x,0.111,1.486),(x+0.026,0.106,1.481)]
    else:
        brow=[(x-0.026,0.106,1.481),(x,0.111,1.486),(x+0.026,0.106,1.479)]
    add_curve(f"HEAD3_Brow_{side}",brow,0.0046,stone)
changes.append("almond eyes")

# 3. Rebuild nose with smoother bridge and smaller tip.
for n in ["HEAD2_Nose"]:
    o=bpy.data.objects.get(n)
    if o:bpy.data.objects.remove(o,do_unlink=True)
verts=[
(-0.008,0.100,1.466),(0.008,0.100,1.466),
(-0.013,0.106,1.414),(0.013,0.106,1.414),
(-0.010,0.112,1.397),(0.010,0.112,1.397),
(0.0,0.125,1.399),(0.0,0.110,1.462)
]
faces=[(0,1,7),(0,7,2),(1,3,7),(2,7,4),(3,5,7),(4,7,6),(7,5,6),(4,6,5),(2,4,5,3)]
me=bpy.data.meshes.new("HEAD3_NoseMesh"); me.from_pydata(verts,[],faces); me.update()
o=bpy.data.objects.new("HEAD3_Nose",me); bpy.context.scene.collection.objects.link(o); assign(o,stone); recalc(o)
changes.append("nose bridge")

# 4. Replace fringe with broader, irregular carved-stone locks.
remove_prefix(["HEAD2_Hair_"])
locks=[
(-0.090,-0.074,1.526,1.462,0.034),
(-0.062,-0.050,1.532,1.475,0.038),
(-0.032,-0.022,1.536,1.468,0.040),
(-0.004, 0.008,1.537,1.483,0.036),
( 0.026, 0.020,1.536,1.465,0.041),
( 0.057, 0.050,1.531,1.474,0.038),
( 0.088, 0.074,1.524,1.460,0.034),
]
for i,(rx,tx,rz,tz,w) in enumerate(locks):
    lock_mesh(f"HEAD3_Hair_{i:02d}",rx,tx,rz,tz,w,0.024,stone)
changes.append("stone hair locks")

# 5. Temple mechanism smaller and tucked under hair.
for n in ["HEAD2_Temple_L","HEAD2_Temple_R","HEAD2_TemplePin_L","HEAD2_TemplePin_R"]:
    o=bpy.data.objects.get(n)
    if o:
        # simple scale in local object coordinates
        o.scale*=0.82
        bpy.context.view_layer.objects.active=o; bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
changes.append("temple compact")

# 6. Helmet: soften cone impression using an upper dome and lower sphere.
sphere=bpy.data.objects.get("HELM2_PawnSphere")
if sphere:
    sphere.scale*=0.90; sphere.location.z-=0.010
    bpy.context.view_layer.objects.active=sphere; bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
cap=bpy.data.objects.get("HELM2_Cap")
if cap:
    cap.scale.z*=0.90
    bpy.context.view_layer.objects.active=cap; bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)

# shallow stone dome layer atop the cap
bpy.ops.mesh.primitive_uv_sphere_add(segments=48,ring_count=24,radius=1,location=(0,0,1.622))
dome=bpy.context.object; dome.name="HELM3_UpperDome"; dome.scale=(0.118,0.118,0.043)
bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
assign(dome,stone,"HELMET")
for p in dome.data.polygons:p.use_smooth=True

# narrow iron/brass detail rings for layered silhouette
def cyl(name,z,r,dep,mat):
    bpy.ops.mesh.primitive_cylinder_add(vertices=64,radius=r,depth=dep,location=(0,0,z))
    oo=bpy.context.object; oo.name=name
    md=oo.modifiers.new("Bevel","BEVEL"); md.width=0.0025; md.segments=2
    bpy.context.view_layer.objects.active=oo;bpy.ops.object.modifier_apply(modifier=md.name)
    assign(oo,mat,"HELMET")
    return oo
cyl("HELM3_UpperTrim",1.640,0.112,0.010,brass)
changes.append("helmet layered dome")

bpy.context.scene["cherpg_version"]=VERSION
bpy.context.scene["part_pass"]="HEAD_DETAIL_C"
bpy.context.scene["part_pass_goal"]="human-readable carved stone face with almond amber eyes and layered pawn helmet"

out.parent.mkdir(parents=True,exist_ok=True); bpy.ops.wm.save_as_mainfile(filepath=str(out))
out.with_suffix(".json").write_text(json.dumps({"version":VERSION,"changes":changes},ensure_ascii=False,indent=2),encoding="utf-8")
print(json.dumps({"version":VERSION,"changes":changes},ensure_ascii=False,indent=2))
