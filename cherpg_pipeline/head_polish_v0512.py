import bpy,bmesh,math,json,sys
from pathlib import Path
from mathutils import Vector

VERSION="0.5.12-head-polish"

def parse_args():
    a=sys.argv
    if "--" not in a: raise RuntimeError("expected input output")
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

def arm(): return bpy.data.objects.get("RIG_PawnHero")

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

def assign(o,mat,group="HEAD",smooth=False):
    if mat:o.data.materials.append(mat)
    skin(o,group)
    if smooth:
        for p in o.data.polygons:p.use_smooth=True
    return o

def curve(name,pts,bev,mat,group="HEAD"):
    cu=bpy.data.curves.new(name+"Curve","CURVE");cu.dimensions="3D";cu.bevel_depth=bev;cu.bevel_resolution=3
    sp=cu.splines.new("BEZIER");sp.bezier_points.add(len(pts)-1)
    for bp,p in zip(sp.bezier_points,pts):bp.co=p;bp.handle_left_type="AUTO";bp.handle_right_type="AUTO"
    o=bpy.data.objects.new(name,cu);bpy.context.scene.collection.objects.link(o)
    if mat:o.data.materials.append(mat)
    bpy.context.view_layer.objects.active=o;o.select_set(True);bpy.ops.object.convert(target="MESH");o=bpy.context.object
    skin(o,group);return o

def hair_lock(name,centers,widths,depth,mat):
    verts=[]
    for c,w in zip(centers,widths):
        c=Vector(c)
        for yoff in (-depth/2,depth/2):
            verts.append((c.x-w/2,c.y+yoff,c.z))
            verts.append((c.x+w/2,c.y+yoff,c.z))
    faces=[]
    for s in range(len(centers)-1):
        a=s*4;b=(s+1)*4
        faces += [(a,a+1,b+1,b),(a+2,b+2,b+3,a+3),(a,b,b+2,a+2),(a+1,a+3,b+3,b+1)]
    faces += [(0,2,3,1),(len(verts)-4,len(verts)-3,len(verts)-1,len(verts)-2)]
    me=bpy.data.meshes.new(name+"Mesh");me.from_pydata(verts,[],faces);me.update()
    o=bpy.data.objects.new(name,me);bpy.context.scene.collection.objects.link(o)
    md=o.modifiers.new("Bevel","BEVEL");md.width=0.0034;md.segments=3
    bpy.context.view_layer.objects.active=o;bpy.ops.object.modifier_apply(modifier=md.name)
    return assign(o,mat,"HEAD")

def scale_about(o,pivot,scale=(1,1,1),trans=(0,0,0)):
    inv=o.matrix_world.inverted();sx,sy,sz=scale;d=Vector(trans)
    for v in o.data.vertices:
        w=o.matrix_world@v.co;r=w-pivot
        v.co=inv@(pivot+Vector((r.x*sx,r.y*sy,r.z*sz))+d)
    recalc(o)

def center(o):
    pts=[o.matrix_world@Vector(c) for c in o.bound_box]
    return sum(pts,Vector())/len(pts)

inp,out=parse_args()
if Path(bpy.data.filepath).resolve()!=inp:bpy.ops.wm.open_mainfile(filepath=str(inp))
stone=mat_like("marble","stone");iron=mat_like("iron","metal");brass=mat_like("brass","gold")
changes=[]

# 1. Remove button nose and build a carved nose ridge + small wedge tip.
for n in ["HEAD5_NoseTip","HEAD5_NostrilL","HEAD5_NostrilR"]:
    o=bpy.data.objects.get(n)
    if o:bpy.data.objects.remove(o,do_unlink=True)

verts=[
(-0.007,0.101,1.458),(0.007,0.101,1.458),
(-0.010,0.106,1.418),(0.010,0.106,1.418),
(-0.012,0.109,1.401),(0.012,0.109,1.401),
(0.0,0.121,1.398),(0.0,0.109,1.455)
]
faces=[(0,1,7),(0,7,2),(1,3,7),(2,7,4),(3,5,7),(4,7,6),(7,5,6),(4,6,5),(2,4,5,3)]
me=bpy.data.meshes.new("HEAD6_NoseMesh");me.from_pydata(verts,[],faces);me.update()
o=bpy.data.objects.new("HEAD6_Nose",me);bpy.context.scene.collection.objects.link(o);assign(o,stone,"HEAD");recalc(o)
curve("HEAD6_NostrilL",[(-0.010,0.111,1.397),(-0.005,0.113,1.396)],0.0009,iron)
curve("HEAD6_NostrilR",[(0.005,0.113,1.396),(0.010,0.111,1.397)],0.0009,iron)
changes.append("carved nose")

# 2. Hair: replace thick slabs with 9 thinner layered swept locks.
for o in list(bpy.context.scene.objects):
    if o.type=="MESH" and (o.name.startswith("HEAD5_Hair_") or o.name.startswith("HEAD5_Side_")):
        bpy.data.objects.remove(o,do_unlink=True)

locks=[
("00",[(-0.102,0.078,1.532),(-0.096,0.101,1.502),(-0.087,0.115,1.468)],[0.028,0.022,0.004]),
("01",[(-0.080,0.080,1.538),(-0.071,0.105,1.503),(-0.060,0.120,1.455)],[0.032,0.024,0.004]),
("02",[(-0.057,0.083,1.541),(-0.046,0.109,1.505),(-0.034,0.123,1.472)],[0.033,0.024,0.004]),
("03",[(-0.032,0.086,1.544),(-0.018,0.113,1.507),(-0.007,0.125,1.456)],[0.034,0.025,0.004]),
("04",[(-0.006,0.088,1.545),(0.004,0.115,1.510),(0.014,0.126,1.480)],[0.032,0.023,0.004]),
("05",[(0.020,0.087,1.544),(0.030,0.113,1.507),(0.026,0.125,1.462)],[0.034,0.025,0.004]),
("06",[(0.046,0.084,1.542),(0.055,0.109,1.504),(0.052,0.121,1.474)],[0.033,0.024,0.004]),
("07",[(0.071,0.081,1.538),(0.080,0.104,1.501),(0.075,0.118,1.455)],[0.031,0.023,0.004]),
("08",[(0.095,0.078,1.532),(0.101,0.100,1.498),(0.095,0.114,1.468)],[0.027,0.021,0.004]),
]
for n,c,w in locks:hair_lock("HEAD6_Hair_"+n,c,w,0.016,stone)
hair_lock("HEAD6_Side_L",[(-0.105,0.046,1.523),(-0.111,0.064,1.486),(-0.106,0.076,1.445)],[0.028,0.021,0.004],0.016,stone)
hair_lock("HEAD6_Side_R",[(0.105,0.046,1.523),(0.111,0.064,1.486),(0.106,0.076,1.445)],[0.028,0.021,0.004],0.016,stone)
changes.append("layered hair")

# 3. Face: tiny lower-face shortening and cheek refinement.
face=bpy.data.objects.get("HEAD4_Face")
if face:
    inv=face.matrix_world.inverted()
    for v in face.data.vertices:
        w=face.matrix_world@v.co
        x,y,z=w.x,w.y,w.z
        if z<1.390:
            z=1.390+(z-1.390)*0.92
        if 1.415<z<1.450 and 0.045<abs(x)<0.085:
            y+=0.0018
        if z<1.350:
            x*=0.98
        v.co=inv@Vector((x,y,z))
    recalc(face)
changes.append("face proportion")

# 4. Helmet: flatten top slightly, make layered brim and visible segmented trims.
helmet=bpy.data.objects.get("HELM4_Main")
if helmet:
    c=Vector((0,0,1.590));scale_about(helmet,c,(0.98,0.98,0.93),(0,0,-0.004))
sphere=bpy.data.objects.get("HELM4_PawnSphere")
if sphere:
    c=center(sphere);scale_about(sphere,c,(0.95,0.95,0.95),(0,0,-0.006))
stem=bpy.data.objects.get("HELM4_PawnStem")
if stem:
    c=center(stem);scale_about(stem,c,(0.95,0.95,0.82),(0,0,-0.004))

# Additional layered stone lip just above lower brim.
bpy.ops.mesh.primitive_cylinder_add(vertices=64,radius=0.147,depth=0.010,location=(0,0,1.556))
lip=bpy.context.object;lip.name="HELM6_StoneLip"
md=lip.modifiers.new("Bevel","BEVEL");md.width=0.0028;md.segments=2
bpy.context.view_layer.objects.active=lip;bpy.ops.object.modifier_apply(modifier=md.name);assign(lip,stone,"HELMET")
# brass upper collar under sphere
bpy.ops.mesh.primitive_cylinder_add(vertices=64,radius=0.064,depth=0.008,location=(0,0,1.650))
band=bpy.context.object;band.name="HELM6_PawnCollar";assign(band,brass,"HELMET")
changes.append("helmet layering")

# Make panel seams darker/closer to shell.
for o in bpy.context.scene.objects:
    if o.name.startswith("HELM5_Seam_"):
        o.scale*=0.85
        o.location.z-=0.004

# 5. Brows/lids: small reduction so eyes dominate like concept.
for o in bpy.context.scene.objects:
    if o.name.startswith("HEAD4_Brow_"):
        c=center(o);scale_about(o,c,(0.93,0.93,0.90),(0,0,-0.001))
    if o.name.startswith("HEAD4_UpperLid_"):
        c=center(o);scale_about(o,c,(1.02,1.0,0.94),(0,0,0))

bpy.context.scene["cherpg_version"]=VERSION;bpy.context.scene["part_pass"]="HEAD_ILLUSTRATION_POLISH"
bpy.context.scene["part_pass_goal"]="thin layered stone hair, carved nose, layered pawn helmet, illustration-like youthful proportions"
out.parent.mkdir(parents=True,exist_ok=True);bpy.ops.wm.save_as_mainfile(filepath=str(out))
out.with_suffix(".json").write_text(json.dumps({"version":VERSION,"changes":changes},ensure_ascii=False,indent=2),encoding="utf-8")
print(json.dumps({"version":VERSION,"changes":changes},ensure_ascii=False,indent=2))
