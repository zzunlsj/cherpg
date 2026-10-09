import bpy,bmesh,math,json,sys
from pathlib import Path
from mathutils import Vector

VERSION="0.5.11-head-match"

def parse_args():
    a=sys.argv
    if "--" not in a:raise RuntimeError("expected input output")
    a=a[a.index("--")+1:];return Path(a[0]).resolve(),Path(a[1]).resolve()

def mat_like(*hints):
    for h in hints:
        for m in bpy.data.materials:
            if h.lower() in m.name.lower():return m
    return bpy.data.materials[0] if bpy.data.materials else None

def recalc(o):
    bm=bmesh.new();bm.from_mesh(o.data)
    if bm.faces:bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
    bm.to_mesh(o.data);bm.free();o.data.update()

def center(o):
    pts=[o.matrix_world@Vector(c) for c in o.bound_box]
    return sum(pts,Vector())/len(pts)

def scale_about(o,pivot,scale=(1,1,1),trans=(0,0,0)):
    inv=o.matrix_world.inverted();sx,sy,sz=scale;d=Vector(trans)
    for v in o.data.vertices:
        w=o.matrix_world@v.co;r=w-pivot
        v.co=inv@(pivot+Vector((r.x*sx,r.y*sy,r.z*sz))+d)
    recalc(o)

def arm():
    return bpy.data.objects.get("RIG_PawnHero")

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

def add_uv(name,loc,scale,mat,group="HEAD",segments=32,rings=16):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments,ring_count=rings,radius=1,location=loc)
    o=bpy.context.object;o.name=name;o.scale=scale;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    if mat:o.data.materials.append(mat)
    skin(o,group)
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

def hair_ribbon(name,centers,widths,depth,mat):
    verts=[]
    # local horizontal basis X; all locks are frontal ribbons with curved centers
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
    md=o.modifiers.new("Bevel","BEVEL");md.width=0.0045;md.segments=3
    bpy.context.view_layer.objects.active=o;bpy.ops.object.modifier_apply(modifier=md.name)
    if mat:o.data.materials.append(mat)
    skin(o,"HEAD")
    return o

inp,out=parse_args()
if Path(bpy.data.filepath).resolve()!=inp:bpy.ops.wm.open_mainfile(filepath=str(inp))
stone=mat_like("marble","stone");iron=mat_like("iron","metal");brass=mat_like("brass","gold");amber=mat_like("amber","eye","glow") or brass
changes=[]

# --- Face proportion: slightly narrower jaw, stronger chin, youthful cheek plane ---
face=bpy.data.objects.get("HEAD4_Face")
if face:
    inv=face.matrix_world.inverted()
    for v in face.data.vertices:
        w=face.matrix_world@v.co
        x,y,z=w.x,w.y,w.z
        if z<1.395:
            t=max(0,min(1,(1.395-z)/0.075))
            x*=1.0-0.08*t
            y+=0.002*t
        if 1.410<z<1.455 and 0.040<abs(x)<0.085:
            sign=1 if x>0 else -1
            x+=sign*0.003
            y+=0.0025
        if z<1.345:
            z-=0.003
        v.co=inv@Vector((x,y,z))
    recalc(face)
    # subdivision for smoother sculpt without changing silhouette
    md=face.modifiers.new("HeadFineSubdivision","SUBSURF");md.levels=1;md.render_levels=1
    bpy.context.view_layer.objects.active=face;bpy.ops.object.modifier_apply(modifier=md.name)
    changes.append("face refine")

# --- Eyes: larger aperture + pupils/highlights ---
for side,x in [("L",-0.038),("R",0.038)]:
    for prefix in ["HEAD4_Socket_","HEAD4_Eye_","HEAD4_UpperLid_","HEAD4_LowerLid_","HEAD4_Brow_"]:
        o=bpy.data.objects.get(prefix+side)
        if o:
            c=center(o)
            sx=1.10 if "Eye_" in prefix or "Socket_" in prefix else 1.05
            sz=1.08 if "Eye_" in prefix or "Socket_" in prefix else 1.04
            scale_about(o,c,(sx,1.0,sz),(0,0,0))
    # dark pupil with tiny warm highlight
    add_uv(f"HEAD5_Pupil_{side}",(x,0.1135,1.448),(0.0065,0.0032,0.0075),iron)
    add_uv(f"HEAD5_EyeHighlight_{side}",(x-0.004,0.1165,1.453),(0.0023,0.0015,0.0023),brass)
changes.append("eyes/pupils")

# --- Nose: subtle tip and nostril shadow rather than blade ---
add_uv("HEAD5_NoseTip",(0,0.1125,1.399),(0.0135,0.008,0.010),stone)
curve("HEAD5_NostrilL",[(-0.010,0.114,1.396),(-0.005,0.116,1.394)],0.0012,iron)
curve("HEAD5_NostrilR",[(0.005,0.116,1.394),(0.010,0.114,1.396)],0.0012,iron)
changes.append("nose tip")

# --- Mouth: neutral youthful mouth with small lower-lip plane ---
old=bpy.data.objects.get("HEAD4_Mouth")
if old:bpy.data.objects.remove(old,do_unlink=True)
curve("HEAD5_Mouth",[(-0.025,0.103,1.369),(-0.010,0.105,1.368),(0,0.106,1.368),(0.010,0.105,1.368),(0.025,0.103,1.369)],0.0015,iron)
curve("HEAD5_LowerLip",[(-0.016,0.102,1.362),(0,0.104,1.361),(0.016,0.102,1.362)],0.0014,stone)
changes.append("mouth/lip")

# --- Hair: replace vertical fringe with six broad swept sculpted locks ---
for o in list(bpy.context.scene.objects):
    if o.type=="MESH" and (o.name.startswith("HEAD4_Hair_") or o.name.startswith("HEAD4_SideHair_")):
        bpy.data.objects.remove(o,do_unlink=True)

specs=[
("L_outer",[(-0.100,0.080,1.538),(-0.092,0.105,1.500),(-0.078,0.118,1.455)],[0.040,0.033,0.006]),
("L_mid",[(-0.072,0.084,1.542),(-0.060,0.110,1.506),(-0.044,0.122,1.472)],[0.043,0.034,0.006]),
("L_inner",[(-0.040,0.087,1.544),(-0.024,0.114,1.508),(-0.010,0.124,1.462)],[0.045,0.034,0.006]),
("R_inner",[(0.000,0.089,1.545),(0.012,0.115,1.509),(0.022,0.124,1.474)],[0.044,0.034,0.006]),
("R_mid",[(0.034,0.087,1.544),(0.048,0.112,1.506),(0.056,0.121,1.465)],[0.044,0.033,0.006]),
("R_outer",[(0.070,0.083,1.540),(0.086,0.106,1.500),(0.094,0.117,1.452)],[0.040,0.031,0.006]),
]
for n,c,w in specs:hair_ribbon("HEAD5_Hair_"+n,c,w,0.020,stone)
# side swept locks cover temple joint
hair_ribbon("HEAD5_Side_L",[(-0.095,0.040,1.525),(-0.108,0.060,1.485),(-0.105,0.072,1.445)],[0.035,0.028,0.006],0.020,stone)
hair_ribbon("HEAD5_Side_R",[(0.095,0.040,1.525),(0.108,0.060,1.485),(0.105,0.072,1.445)],[0.035,0.028,0.006],0.020,stone)
changes.append("swept hair")

# --- Temple joints: smaller, tucked back ---
for n in ["HEAD4_Temple_L","HEAD4_Temple_R","HEAD4_TemplePin_L","HEAD4_TemplePin_R"]:
    o=bpy.data.objects.get(n)
    if o:
        c=center(o);scale_about(o,c,(0.72,0.72,0.72),(0,-0.010,0))
changes.append("temple hidden")

# --- Helmet proportion: 8% smaller and lower, sphere/stem also reduced ---
helmet_names=["HELM4_Main","HELM4_BrimTrim","HELM4_CrownTrim","HELM4_PawnStem","HELM4_PawnSphere"]
hp=Vector((0,0,1.590))
for n in helmet_names:
    o=bpy.data.objects.get(n)
    if not o:continue
    s=(0.92,0.92,0.94)
    if n=="HELM4_PawnSphere":s=(0.90,0.90,0.90)
    scale_about(o,hp,s,(0,0,-0.012))
changes.append("helmet scale")

# Add subtle 8-panel seam accents on helmet dome, like carved plate divisions.
for i,ang in enumerate([math.radians(a) for a in range(0,360,45)]):
    x=0.119*math.sin(ang);y=0.119*math.cos(ang)
    # short diagonal/vertical surface mark represented by slim dark rod
    curve(f"HELM5_Seam_{i}",[(x*1.06,y*1.06,1.565),(x*0.96,y*0.96,1.604),(x*0.82,y*0.82,1.625)],0.0017,iron,"HELMET")
changes.append("helmet panel seams")

bpy.context.scene["cherpg_version"]=VERSION;bpy.context.scene["part_pass"]="HEAD_CONCEPT_MATCH"
bpy.context.scene["part_pass_goal"]="match concept head proportions, swept stone hair, expressive amber eyes, compact layered pawn helmet"
out.parent.mkdir(parents=True,exist_ok=True);bpy.ops.wm.save_as_mainfile(filepath=str(out))
out.with_suffix(".json").write_text(json.dumps({"version":VERSION,"changes":changes},ensure_ascii=False,indent=2),encoding="utf-8")
print(json.dumps({"version":VERSION,"changes":changes},ensure_ascii=False,indent=2))
