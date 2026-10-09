import bpy, bmesh, math, json, sys
from pathlib import Path
from mathutils import Vector

VERSION="0.5.8-head-rebuild"

def parse_args():
    a=sys.argv
    if "--" not in a: raise RuntimeError("Expected input blend and output blend")
    a=a[a.index("--")+1:]
    return Path(a[0]).resolve(), Path(a[1]).resolve()

def mat_like(*hints):
    for h in hints:
        for m in bpy.data.materials:
            if h.lower() in m.name.lower():
                return m
    return bpy.data.materials[0] if bpy.data.materials else None

def recalc(o):
    bm=bmesh.new(); bm.from_mesh(o.data)
    if bm.faces: bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
    bm.to_mesh(o.data); bm.free(); o.data.update()

def armature():
    return bpy.data.objects.get("RIG_PawnHero")

def rigid_skin(o,bone="Head"):
    arm=armature()
    if not arm: return
    for vg in list(o.vertex_groups): o.vertex_groups.remove(vg)
    vg=o.vertex_groups.new(name=bone)
    if len(o.data.vertices): vg.add(list(range(len(o.data.vertices))),1.0,"REPLACE")
    for m in list(o.modifiers):
        if m.type=="ARMATURE": o.modifiers.remove(m)
    mod=o.modifiers.new("CheRPG_Armature","ARMATURE"); mod.object=arm
    o["cherpg_primary_bone"]=bone; o["cherpg_skin_mode"]="rigid"

def assign(o,mat,group):
    if mat: o.data.materials.append(mat)
    o["cherpg_group"]=group
    rigid_skin(o,"Head")
    return o

def make_face(name, center=(0,0.028,1.425), seg_u=32, seg_v=64):
    cx,cy,cz=center
    verts=[]; faces=[]
    for i in range(seg_u+1):
        lat=-math.pi/2 + math.pi*i/seg_u
        sl=math.sin(lat); cl=math.cos(lat)
        zloc=0.125*sl
        # jaw taper below mouth; slightly wider cheek band.
        lower=max(0.0,min(1.0,(-zloc-0.015)/0.10))
        cheek=math.exp(-((zloc+0.005)/0.050)**2)
        rx=0.101*(1.0-0.18*lower)*(1.0+0.05*cheek)
        rz=0.125
        for j in range(seg_v):
            lon=2*math.pi*j/seg_v
            s=math.sin(lon); c=math.cos(lon)
            # +Y is face front.
            front=max(c,0.0); back=max(-c,0.0)
            # front is flatter, back rounder.
            ry=0.088*(0.92+0.08*back)
            x=rx*cl*s
            y=ry*cl*c
            z=rz*sl
            # Brow/cheek plane shaping.
            if front>0.0:
                # flatten central facial plane
                y*=0.88
                # cheek projection under eyes
                cheek2=math.exp(-((z-0.005)/0.040)**2) * min(abs(x)/0.07,1.0)
                y += 0.010*cheek2
                # forehead slightly recessed
                if z>0.045: y-=0.004*(z-0.045)/0.080
                # chin forward wedge
                if z<-0.050: y += 0.010*min((-z-0.050)/0.070,1.0)
            verts.append((cx+x,cy+y,cz+z))
    for i in range(seg_u):
        for j in range(seg_v):
            a=i*seg_v+j
            b=i*seg_v+(j+1)%seg_v
            c=(i+1)*seg_v+(j+1)%seg_v
            d=(i+1)*seg_v+j
            faces.append((a,b,c,d))
    me=bpy.data.meshes.new(name+"Mesh"); me.from_pydata(verts,[],faces); me.update()
    o=bpy.data.objects.new(name,me); bpy.context.scene.collection.objects.link(o)
    recalc(o)
    for p in me.polygons: p.use_smooth=True
    return o

def add_uv_sphere(name,loc,scale,mat,group,segments=48,rings=24):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments, ring_count=rings, radius=1, location=loc)
    o=bpy.context.object; o.name=name; o.scale=scale
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    for p in o.data.polygons: p.use_smooth=True
    return assign(o,mat,group)

def add_cyl(name,loc,radius,depth,mat,group,rot=(0,0,0),verts=64,bevel=0.0):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts,radius=radius,depth=depth,location=loc,rotation=rot)
    o=bpy.context.object; o.name=name
    if bevel:
        md=o.modifiers.new("Bevel","BEVEL"); md.width=bevel; md.segments=3
        bpy.context.view_layer.objects.active=o; bpy.ops.object.modifier_apply(modifier=md.name)
    return assign(o,mat,group)

def add_cone(name,loc,r1,r2,depth,mat,group,bevel=0.0):
    bpy.ops.mesh.primitive_cone_add(vertices=64,radius1=r1,radius2=r2,depth=depth,location=loc)
    o=bpy.context.object; o.name=name
    if bevel:
        md=o.modifiers.new("Bevel","BEVEL"); md.width=bevel; md.segments=3
        bpy.context.view_layer.objects.active=o; bpy.ops.object.modifier_apply(modifier=md.name)
    return assign(o,mat,group)

def add_curve_strip(name,points,bevel,mat,group):
    cu=bpy.data.curves.new(name+"Curve","CURVE"); cu.dimensions="3D"; cu.resolution_u=2; cu.bevel_depth=bevel; cu.bevel_resolution=3
    sp=cu.splines.new("BEZIER"); sp.bezier_points.add(len(points)-1)
    for bp,co in zip(sp.bezier_points,points):
        bp.co=co; bp.handle_left_type="AUTO"; bp.handle_right_type="AUTO"
    o=bpy.data.objects.new(name,cu); bpy.context.scene.collection.objects.link(o)
    if mat: o.data.materials.append(mat)
    bpy.context.view_layer.objects.active=o; o.select_set(True); bpy.ops.object.convert(target="MESH"); o=bpy.context.object
    o["cherpg_group"]=group; rigid_skin(o,"Head")
    return o

def add_hair_lock(name,x,z,angle=0.0,scale=1.0):
    # front prism tapering to a point, slightly forward of forehead
    w=0.030*scale; h=0.070*scale; dep=0.022
    verts=[
        (-w/2,-dep/2,h/2),(w/2,-dep/2,h/2),(0,-dep/2,-h/2),
        (-w/2,dep/2,h/2),(w/2,dep/2,h/2),(0,dep/2,-h/2)
    ]
    faces=[(0,1,2),(3,5,4),(0,3,4,1),(1,4,5,2),(2,5,3,0)]
    me=bpy.data.meshes.new(name+"Mesh"); me.from_pydata(verts,[],faces); me.update()
    o=bpy.data.objects.new(name,me); bpy.context.scene.collection.objects.link(o)
    o.location=(x,0.113,z); o.rotation_euler[1]=angle
    md=o.modifiers.new("Bevel","BEVEL"); md.width=0.004; md.segments=2
    bpy.context.view_layer.objects.active=o; bpy.ops.object.modifier_apply(modifier=md.name)
    return assign(o,stone,"HEAD")

inp,out=parse_args()
if Path(bpy.data.filepath).resolve()!=inp:
    bpy.ops.wm.open_mainfile(filepath=str(inp))

stone=mat_like("marble","stone")
iron=mat_like("iron","metal")
brass=mat_like("brass","gold")
amber=mat_like("amber","eye","glow") or brass

# Remove all previous head/helmet visual meshes, keep neck/scarf and armature.
removed=[]
for o in list(bpy.context.scene.objects):
    if o.type!="MESH": continue
    g=str(o.get("cherpg_group",""))
    if g in {"HEAD","HELMET"} or o.name.startswith(("HEAD_","HELM_")):
        removed.append(o.name); bpy.data.objects.remove(o,do_unlink=True)

created=[]

# Core head.
face=assign(make_face("HEAD2_FaceShell"),stone,"HEAD"); created.append(face.name)

# Dark recessed eye sockets + amber eye cores.
for side,x in [("L",-0.036),("R",0.036)]:
    sock=add_uv_sphere(f"HEAD2_Socket_{side}",(x,0.107,1.447),(0.030,0.010,0.021),iron,"HEAD",32,16); created.append(sock.name)
    eye=add_uv_sphere(f"HEAD2_Eye_{side}",(x,0.116,1.447),(0.0205,0.0065,0.0135),amber,"HEAD",32,16); created.append(eye.name)
    # upper and lower stone lids: curved strips
    sx=-1 if side=="L" else 1
    upper=[(x-0.023,0.119,1.454),(x,0.122,1.463),(x+0.023,0.119,1.454)]
    lower=[(x-0.019,0.118,1.440),(x,0.120,1.436),(x+0.019,0.118,1.440)]
    created.append(add_curve_strip(f"HEAD2_UpperLid_{side}",upper,0.0046,stone,"HEAD").name)
    created.append(add_curve_strip(f"HEAD2_LowerLid_{side}",lower,0.0032,stone,"HEAD").name)
    # brow ridge, slight diagonal
    dz=-0.003 if side=="L" else 0.003
    brow=[(x-0.025,0.111,1.481+dz),(x,0.115,1.486),(x+0.025,0.111,1.480-dz)]
    created.append(add_curve_strip(f"HEAD2_Brow_{side}",brow,0.0055,stone,"HEAD").name)

# Nose bridge as a narrow stone wedge.
verts=[
    (-0.010,0.107,1.458),(0.010,0.107,1.458),
    (-0.016,0.111,1.405),(0.016,0.111,1.405),
    (0.0,0.128,1.402),(0.0,0.116,1.455)
]
faces=[(0,1,5),(0,5,2),(1,3,5),(2,5,4),(5,3,4),(2,4,3)]
me=bpy.data.meshes.new("HEAD2_NoseMesh"); me.from_pydata(verts,[],faces); me.update()
nose=bpy.data.objects.new("HEAD2_Nose",me); bpy.context.scene.collection.objects.link(nose)
assign(nose,stone,"HEAD"); recalc(nose); created.append(nose.name)

# Mouth seam, understated.
mouth=add_curve_strip("HEAD2_Mouth",[(-0.025,0.113,1.375),(0,0.115,1.371),(0.025,0.113,1.375)],0.0022,iron,"HEAD"); created.append(mouth.name)

# Temple joint plates smaller and circular, integrated.
for side,x in [("L",-0.103),("R",0.103)]:
    plate=add_cyl(f"HEAD2_Temple_{side}",(x,0.006,1.438),0.030,0.018,iron,"HEAD",rot=(0,math.radians(90),0),verts=40,bevel=0.003); created.append(plate.name)
    pin=add_cyl(f"HEAD2_TemplePin_{side}",(x*1.006,0.006,1.438),0.009,0.022,brass,"HEAD",rot=(0,math.radians(90),0),verts=28); created.append(pin.name)

# Carved stone fringe / hair, under helmet.
for idx,(x,z,ang,sc) in enumerate([
    (-0.078,1.503, math.radians(-12),0.95),
    (-0.050,1.510, math.radians(-8),1.05),
    (-0.020,1.514, math.radians(-4),1.10),
    ( 0.012,1.514, math.radians(3),1.10),
    ( 0.043,1.509, math.radians(8),1.03),
    ( 0.072,1.500, math.radians(12),0.95),
]):
    created.append(add_hair_lock(f"HEAD2_Hair_{idx:02d}",x,z,ang,sc).name)

# Helmet - layered pawn silhouette.
created.append(add_cyl("HELM2_LowerBrim",(0,0.000,1.535),0.172,0.024,stone,"HELMET",bevel=0.006).name)
created.append(add_cyl("HELM2_BrimTrim",(0,0.000,1.548),0.156,0.014,iron,"HELMET",bevel=0.003).name)
created.append(add_cone("HELM2_Cap",(0,0.000,1.588),0.148,0.112,0.086,stone,"HELMET",bevel=0.006).name)
created.append(add_cyl("HELM2_CrownBand",(0,0.000,1.625),0.119,0.016,brass,"HELMET",bevel=0.003).name)
created.append(add_uv_sphere("HELM2_PawnSphere",(0,0.000,1.692),(0.060,0.060,0.060),stone,"HELMET",48,24).name)

# Small stone forehead bridge under brim to integrate helmet and face.
bridge=add_cone("HELM2_ForeheadBridge",(0,0.035,1.525),0.070,0.055,0.035,stone,"HELMET",bevel=0.004); created.append(bridge.name)

# Ensure materials and smoothing.
for o in bpy.context.scene.objects:
    if o.type!="MESH" or o.name not in created: continue
    if o.name.startswith("HEAD2_Face"):
        for p in o.data.polygons: p.use_smooth=True

bpy.context.scene["cherpg_version"]=VERSION
bpy.context.scene["part_pass"]="HEAD_REBUILD"
bpy.context.scene["part_pass_goal"]="rebuild head from scratch toward concept illustration"
bpy.context.scene["head_old_meshes_removed"]=len(removed)
bpy.context.scene["head_new_meshes_created"]=len(created)

out.parent.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=str(out))
out.with_suffix(".json").write_text(json.dumps({"version":VERSION,"removed":removed,"created":created},ensure_ascii=False,indent=2),encoding="utf-8")
print(json.dumps({"version":VERSION,"removed":len(removed),"created":len(created)},indent=2))
