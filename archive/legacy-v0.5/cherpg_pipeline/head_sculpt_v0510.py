import bpy,bmesh,math,json,sys
from pathlib import Path
from mathutils import Vector

VERSION="0.5.10-head-sculpt"

def parse_args():
    a=sys.argv
    if "--" not in a: raise RuntimeError("Expected input output")
    a=a[a.index("--")+1:]; return Path(a[0]).resolve(),Path(a[1]).resolve()

def mat_like(*hints):
    for h in hints:
        for m in bpy.data.materials:
            if h.lower() in m.name.lower(): return m
    return bpy.data.materials[0] if bpy.data.materials else None

def recalc(o):
    bm=bmesh.new();bm.from_mesh(o.data)
    if bm.faces:bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
    bm.to_mesh(o.data);bm.free();o.data.update()

def rig(o,group="HEAD"):
    arm=bpy.data.objects.get("RIG_PawnHero")
    o["cherpg_group"]=group
    if not arm:return
    for vg in list(o.vertex_groups):o.vertex_groups.remove(vg)
    vg=o.vertex_groups.new(name="Head")
    if len(o.data.vertices):vg.add(list(range(len(o.data.vertices))),1.0,"REPLACE")
    for m in list(o.modifiers):
        if m.type=="ARMATURE":o.modifiers.remove(m)
    md=o.modifiers.new("CheRPG_Armature","ARMATURE");md.object=arm
    o["cherpg_primary_bone"]="Head";o["cherpg_skin_mode"]="rigid"

def assign(o,mat,group="HEAD",smooth=False):
    if mat:o.data.materials.append(mat)
    rig(o,group)
    if smooth:
        for p in o.data.polygons:p.use_smooth=True
    return o

def remove_head():
    removed=[]
    for o in list(bpy.context.scene.objects):
        if o.type!="MESH":continue
        g=str(o.get("cherpg_group",""))
        if g in {"HEAD","HELMET"} or o.name.startswith(("HEAD2_","HEAD3_","HELM2_","HELM3_")):
            removed.append(o.name);bpy.data.objects.remove(o,do_unlink=True)
    return removed

def lerp_profile(z,profile):
    # profile sorted by z: (z, rx, ry)
    if z<=profile[0][0]:return profile[0][1],profile[0][2]
    if z>=profile[-1][0]:return profile[-1][1],profile[-1][2]
    for a,b in zip(profile,profile[1:]):
        if a[0]<=z<=b[0]:
            t=(z-a[0])/(b[0]-a[0])
            return a[1]*(1-t)+b[1]*t,a[2]*(1-t)+b[2]*t
    return profile[-1][1],profile[-1][2]

def create_head():
    # Human-readable youthful carved-stone head profile.
    profile=[
      (1.320,0.030,0.035),
      (1.335,0.060,0.052),
      (1.360,0.078,0.064),
      (1.390,0.090,0.073),
      (1.425,0.101,0.083),
      (1.455,0.100,0.082),
      (1.485,0.093,0.078),
      (1.515,0.079,0.071),
      (1.535,0.055,0.050),
    ]
    rings=35;segs=72
    verts=[];faces=[]
    zmin,zmax=profile[0][0],profile[-1][0]
    for i in range(rings):
        z=zmin+(zmax-zmin)*i/(rings-1)
        rx,ry=lerp_profile(z,profile)
        for j in range(segs):
            th=2*math.pi*j/segs
            st,ct=math.sin(th),math.cos(th)
            x=rx*st
            # front +Y made flatter, back round.
            if ct>=0:
                yy=ry*(ct**0.67)
            else:
                yy=-ry*((-ct)**0.90)
            y=0.020+yy

            front=max(ct,0.0)
            # cheekbone projection at +/-35–55 deg
            ang=abs(math.degrees(math.atan2(st,ct)))
            if front>0 and 1.405<z<1.455 and 25<ang<65:
                y+=0.008*math.sin(math.pi*(z-1.405)/0.050)
                x*=1.018

            # integrated brow ridge
            if front>0 and 1.465<z<1.486 and 0.020<abs(x)<0.075:
                y+=0.0045

            # integrated nose bridge/tip centered at front
            if front>0 and abs(x)<0.017:
                if 1.402<z<1.470:
                    t=(z-1.402)/(1.470-1.402)
                    y+=0.010*(1-0.35*t)
                elif 1.388<z<=1.402:
                    y+=0.009*(z-1.388)/0.014

            # philtrum/chin plane
            if front>0 and abs(x)<0.030 and 1.335<z<1.380:
                y+=0.0035

            verts.append((x,y,z))
    for i in range(rings-1):
        for j in range(segs):
            a=i*segs+j;b=i*segs+(j+1)%segs;c=(i+1)*segs+(j+1)%segs;d=(i+1)*segs+j
            faces.append((a,b,c,d))
    me=bpy.data.meshes.new("HEAD4_FaceMesh");me.from_pydata(verts,[],faces);me.update()
    o=bpy.data.objects.new("HEAD4_Face",me);bpy.context.scene.collection.objects.link(o);recalc(o)
    return assign(o,stone,"HEAD",smooth=True)

def almond(name,cx,cy,cz,w,h,depth,mat):
    n=20;ring=[]
    for k in range(n):
        t=2*math.pi*k/n;x=math.cos(t);z=math.sin(t)
        zz=z*((1-abs(x))**0.28)
        ring.append((cx+w*x,cy-depth/2,cz+h*zz))
    verts=ring+[(x,cy+depth/2,z) for x,_,z in ring]
    faces=[]
    for k in range(n):
        q=(k+1)%n;faces.append((k,q,n+q,n+k))
    faces+=[tuple(range(n-1,-1,-1)),tuple(range(n,2*n))]
    me=bpy.data.meshes.new(name+"Mesh");me.from_pydata(verts,[],faces);me.update()
    o=bpy.data.objects.new(name,me);bpy.context.scene.collection.objects.link(o);recalc(o)
    return assign(o,mat,"HEAD",smooth=True)

def curve(name,pts,bev,mat,group="HEAD"):
    cu=bpy.data.curves.new(name+"Curve","CURVE");cu.dimensions="3D";cu.bevel_depth=bev;cu.bevel_resolution=3
    sp=cu.splines.new("BEZIER");sp.bezier_points.add(len(pts)-1)
    for bp,p in zip(sp.bezier_points,pts):bp.co=p;bp.handle_left_type="AUTO";bp.handle_right_type="AUTO"
    o=bpy.data.objects.new(name,cu);bpy.context.scene.collection.objects.link(o)
    if mat:o.data.materials.append(mat)
    bpy.context.view_layer.objects.active=o;o.select_set(True);bpy.ops.object.convert(target="MESH");o=bpy.context.object
    rig(o,group);return o

def hair_lock(name,root,mid,tip,widths,depth,mat):
    # 3 cross sections, each L/R at front/back -> volumetric tapered bent stone lock
    centers=[Vector(root),Vector(mid),Vector(tip)]
    verts=[]
    for c,w in zip(centers,widths):
        for yoff in (-depth/2,depth/2):
            verts.append((c.x-w/2,c.y+yoff,c.z))
            verts.append((c.x+w/2,c.y+yoff,c.z))
    # index per section: backL backR frontL frontR
    faces=[]
    for s in range(2):
        a=s*4;b=(s+1)*4
        faces += [
          (a,a+1,b+1,b),
          (a+2,b+2,b+3,a+3),
          (a,b,b+2,a+2),
          (a+1,a+3,b+3,b+1)
        ]
    faces += [(0,2,3,1),(8,9,11,10)]
    me=bpy.data.meshes.new(name+"Mesh");me.from_pydata(verts,[],faces);me.update()
    o=bpy.data.objects.new(name,me);bpy.context.scene.collection.objects.link(o)
    md=o.modifiers.new("Bevel","BEVEL");md.width=0.004;md.segments=2
    bpy.context.view_layer.objects.active=o;bpy.ops.object.modifier_apply(modifier=md.name)
    return assign(o,mat,"HEAD")

def revolve(name,profile,mat,group="HELMET",segs=96):
    # profile list (radius,z)
    verts=[];faces=[]
    for r,z in profile:
        for j in range(segs):
            th=2*math.pi*j/segs
            verts.append((r*math.sin(th),r*math.cos(th),z))
    rows=len(profile)
    for i in range(rows-1):
        for j in range(segs):
            a=i*segs+j;b=i*segs+(j+1)%segs;c=(i+1)*segs+(j+1)%segs;d=(i+1)*segs+j
            faces.append((a,b,c,d))
    me=bpy.data.meshes.new(name+"Mesh");me.from_pydata(verts,[],faces);me.update()
    o=bpy.data.objects.new(name,me);bpy.context.scene.collection.objects.link(o);recalc(o)
    return assign(o,mat,group,smooth=True)

def cyl(name,z,r,d,mat,group="HELMET"):
    bpy.ops.mesh.primitive_cylinder_add(vertices=64,radius=r,depth=d,location=(0,0,z))
    o=bpy.context.object;o.name=name
    md=o.modifiers.new("Bevel","BEVEL");md.width=0.0025;md.segments=2
    bpy.context.view_layer.objects.active=o;bpy.ops.object.modifier_apply(modifier=md.name)
    return assign(o,mat,group)

def sphere(name,loc,scale,mat,group="HELMET"):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=48,ring_count=24,radius=1,location=loc)
    o=bpy.context.object;o.name=name;o.scale=scale;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    return assign(o,mat,group,smooth=True)

inp,out=parse_args()
if Path(bpy.data.filepath).resolve()!=inp:bpy.ops.wm.open_mainfile(filepath=str(inp))
stone=mat_like("marble","stone");iron=mat_like("iron","metal");brass=mat_like("brass","gold");amber=mat_like("amber","eye","glow") or brass
removed=remove_head();created=[]
created.append(create_head().name)

# Eyes: youthful almond amber eyes, recessed socket, stone lids.
for side,x in [("L",-0.038),("R",0.038)]:
    created.append(almond(f"HEAD4_Socket_{side}",x,0.101,1.448,0.031,0.018,0.009,iron).name)
    created.append(almond(f"HEAD4_Eye_{side}",x,0.108,1.448,0.0225,0.0125,0.005,amber).name)
    created.append(curve(f"HEAD4_UpperLid_{side}",[(x-0.028,0.110,1.454),(x,0.115,1.463),(x+0.028,0.110,1.454)],0.0040,stone).name)
    created.append(curve(f"HEAD4_LowerLid_{side}",[(x-0.024,0.108,1.441),(x,0.110,1.438),(x+0.024,0.108,1.441)],0.0024,stone).name)
    # restrained brow, integrated with carved face
    created.append(curve(f"HEAD4_Brow_{side}",[(x-0.026,0.099,1.480),(x,0.105,1.487),(x+0.026,0.100,1.482)],0.0042,stone).name)

# Neutral mouth, almost straight.
created.append(curve("HEAD4_Mouth",[(-0.027,0.102,1.369),(0,0.104,1.367),(0.027,0.102,1.369)],0.0018,iron).name)

# Tiny temple joints, mostly hidden.
for side,x in [("L",-0.096),("R",0.096)]:
    bpy.ops.mesh.primitive_cylinder_add(vertices=40,radius=0.021,depth=0.014,location=(x,-0.002,1.438),rotation=(0,math.radians(90),0))
    o=bpy.context.object;o.name=f"HEAD4_Temple_{side}";created.append(assign(o,iron,"HEAD").name)
    bpy.ops.mesh.primitive_cylinder_add(vertices=32,radius=0.007,depth=0.018,location=(x,-0.002,1.438),rotation=(0,math.radians(90),0))
    o=bpy.context.object;o.name=f"HEAD4_TemplePin_{side}";created.append(assign(o,brass,"HEAD").name)

# Sculpted stone fringe, curved and layered.
lock_specs=[
("00",(-0.095,0.082,1.535),(-0.090,0.105,1.505),(-0.076,0.116,1.455),(0.034,0.026,0.005)),
("01",(-0.070,0.087,1.540),(-0.060,0.110,1.505),(-0.048,0.120,1.470),(0.038,0.028,0.006)),
("02",(-0.040,0.090,1.542),(-0.030,0.114,1.505),(-0.020,0.122,1.460),(0.040,0.028,0.006)),
("03",(-0.010,0.092,1.544),( 0.000,0.116,1.508),( 0.010,0.123,1.478),(0.038,0.026,0.006)),
("04",( 0.020,0.091,1.543),( 0.026,0.114,1.505),( 0.020,0.122,1.458),(0.040,0.028,0.006)),
("05",( 0.052,0.088,1.540),( 0.058,0.110,1.505),( 0.050,0.119,1.468),(0.038,0.027,0.006)),
("06",( 0.082,0.084,1.535),( 0.088,0.104,1.500),( 0.078,0.115,1.452),(0.034,0.025,0.005)),
]
for n,r,m,t,w in lock_specs:created.append(hair_lock("HEAD4_Hair_"+n,r,m,t,w,0.020,stone).name)

# Side locks covering temple mechanisms.
created.append(hair_lock("HEAD4_SideHair_L",(-0.092,0.050,1.520),(-0.105,0.070,1.485),(-0.106,0.073,1.438),(0.030,0.024,0.006),0.020,stone).name)
created.append(hair_lock("HEAD4_SideHair_R",(0.092,0.050,1.520),(0.105,0.070,1.485),(0.106,0.073,1.438),(0.030,0.024,0.006),0.020,stone).name)

# Helmet profile: rounded layered stone helmet rather than cone.
helmet_profile=[
(0.177,1.532),
(0.179,1.542),
(0.171,1.551),
(0.157,1.554),
(0.153,1.566),
(0.150,1.585),
(0.145,1.602),
(0.137,1.618),
(0.125,1.633),
(0.111,1.644),
(0.091,1.651),
(0.066,1.656),
]
created.append(revolve("HELM4_Main",helmet_profile,stone).name)
created.append(cyl("HELM4_BrimTrim",1.549,0.160,0.009,iron).name)
created.append(cyl("HELM4_CrownTrim",1.651,0.093,0.009,brass).name)
created.append(cyl("HELM4_PawnStem",1.666,0.045,0.028,stone).name)
created.append(sphere("HELM4_PawnSphere",(0,0,1.711),(0.055,0.055,0.055),stone).name)

bpy.context.scene["cherpg_version"]=VERSION;bpy.context.scene["part_pass"]="HEAD_SCULPT_D"
bpy.context.scene["part_pass_goal"]="concept-level youthful carved-stone face and rounded layered pawn helmet"

out.parent.mkdir(parents=True,exist_ok=True);bpy.ops.wm.save_as_mainfile(filepath=str(out))
out.with_suffix(".json").write_text(json.dumps({"version":VERSION,"removed":removed,"created":created},ensure_ascii=False,indent=2),encoding="utf-8")
print(json.dumps({"version":VERSION,"removed":len(removed),"created":len(created)},indent=2))
