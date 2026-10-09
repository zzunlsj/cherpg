"""CheRPG v0.0.4 — retopologize the REAL Blender v0.0.3 head.
Replaces three UV face patches with integrated concentric quad loops:
left eyelid, right eyelid, and mouth. No sculpt-by-image generation.
"""
import bpy,sys,math,json
from pathlib import Path
from collections import Counter
from mathutils import Vector
a=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
if len(a)!=2: raise RuntimeError("Usage: -- v0.0.3.blend output-directory")
src,out=Path(a[0]).resolve(),Path(a[1]).resolve()
if not src.is_file(): raise RuntimeError("Source blend missing")
out.mkdir(parents=True,exist_ok=True)
if Path(bpy.data.filepath).resolve()!=src:bpy.ops.wm.open_mainfile(filepath=str(src))
head=bpy.data.objects.get("Pawn_Head_FaceBlockout")
if not head or head.type!="MESH" or head.get("facial_landmarks_version")!="0.0.3":
    raise RuntimeError("Expected v0.0.3 Pawn face")
if head.get("loop_retopology_version"):raise RuntimeError("Already applied")
mesh=head.data
NL,NJ=88,128
if len(mesh.vertices)!=(NL+1)*NJ or len(mesh.polygons)!=NL*NJ:
    raise RuntimeError("Source UV grid has unexpected topology")
def g(x,c,s):return math.exp(-((x-c)/s)**2)
def blend(a,b,t):return a*(1-t)+b*t
patches=[
 dict(name="left_eye",i0=35,i1=48,j0=79,j1=94,cx=-.034,z=.011,rx=.019,rz=.0063,kind="eye"),
 dict(name="right_eye",i0=35,i1=48,j0=98,j1=113,cx=.034,z=.011,rx=.019,rz=.0063,kind="eye"),
 dict(name="mouth",i0=54,i1=66,j0=87,j1=105,cx=0.,z=-.064,rx=.022,rz=.00085,kind="mouth")
]
def inside(idx,r):
    i,j=divmod(idx,NJ)
    return r["i0"]<i<r["i1"] and r["j0"]<j<r["j1"]
remove={idx for idx in range(len(mesh.vertices)) if any(inside(idx,r) for r in patches)}
oldmap={};points=[]
for idx,v in enumerate(mesh.vertices):
    if idx in remove:continue
    oldmap[idx]=len(points)
    p=v.co.copy();x,z=p.x,p.z-1.422
    # soften unnaturally pinched / overlong v0.0.3 jaw and nose
    p.x*=1+.14*g(z,-.103,.027)
    p.z+=.0050*g(z,-.120,.017)
    p.y+=.0031*g(x,0,.015)*g(z,-.037,.019)
    points.append(tuple(p))
faces=[];mat_indices=[]
for face in mesh.polygons:
    ids=list(face.vertices)
    i,j=divmod(ids[0],NJ)
    if any(r["i0"]<=i<r["i1"] and r["j0"]<=j<r["j1"] for r in patches):continue
    if any(k not in oldmap for k in ids):raise RuntimeError("Patch border mismatch")
    faces.append(tuple(oldmap[k] for k in reversed(ids))) # original winding inward
    mat_indices.append(0)
def baseline_y(x,z):
    zz=(z-1.422)/.126
    jaw=max(0.,(-zz-.12)/.85)
    width=.093*(.91+.11*g(zz,.42,.55)+.06*g(zz,-.12,.32)-.24*jaw**1.2)
    depth=.089*(1-.07*jaw)
    return -depth*math.sqrt(max(.035,1-zz*zz-(x/width)**2))
def boundary(r):
    i0,i1,j0,j1=(r[k] for k in ("i0","i1","j0","j1"))
    return ([(i0,j) for j in range(j0,j1+1)]+[(i,j1) for i in range(i0+1,i1+1)]
         +[(i1,j) for j in range(j1-1,j0-1,-1)]+[(i,j0) for i in range(i1-1,i0,-1)])
bridge_edges=[]
details={}
for r in patches:
    outer=[oldmap[i*NJ+j] for i,j in boundary(r)]
    border=[Vector(points[i]) for i in outer]
    cx,cz,rx,rz=r["cx"],1.422+r["z"],r["rx"],r["rz"]
    eye=r["kind"]=="eye"
    ellipse=[]
    # Match the rectangle perimeter using its OWN normalized scale.
    # Normalizing by the much smaller inner ellipse radii collapses
    # whole outer edges onto eye/mouth tips and creates triangular folds.
    bx=(max(v.x for v in border)-min(v.x for v in border))*0.5
    bz=(max(v.z for v in border)-min(v.z for v in border))*0.5
    for p in border:
        theta=math.atan2((p.z-cz)/max(bz,.001),(p.x-cx)/max(bx,.001))
        co,si=math.cos(theta),math.sin(theta)
        taper=.76+.24*(1-abs(co)**4) if eye else 1
        ellipse.append((cx+rx*co,cz+rz*si*taper+(.0015*co if eye else 0)))
    def make(t,offset,scale=1.0):
        ring=[]
        for p,(ex,ez) in zip(border,ellipse):
            x=blend(p.x,cx+(ex-cx)*scale,t)
            z=blend(p.z,cz+(ez-cz)*scale,t)
            y=blend(p.y,baseline_y(x,z),t)+offset
            if not eye:y-=(.0008 if z>=cz else .00045)*g(t,.77,.3)
            ring.append(len(points));points.append((x,y,z))
        return ring
    loops=[outer,make(.27,0),make(.56,-.0005),make(.80,-.0012),make(1,-.0017),
           make(1,.0011,.96),make(1,.0070 if eye else .002,.76),
           make(1,.010 if eye else .0024,.16)]
    n=len(outer)
    for layer,(rout,rin) in enumerate(zip(loops[:-1],loops[1:])):
        for k in range(n):
            nxt=(k+1)%n
            faces.append((rout[k],rin[k],rin[nxt],rout[nxt]))
            mat_indices.append(1 if layer>=5 else 0)
            if layer==0:bridge_edges.append(tuple(sorted((rout[k],rout[nxt]))))
    middle=len(points);points.append((cx,baseline_y(cx,cz)+(.0102 if eye else .0025),cz))
    last=loops[-1]
    for k in range(n):
        faces.append((last[k],middle,last[(k+1)%n]))
        mat_indices.append(1)
    details[r["name"]]={"perimeter":n,"integrated_quad_loops":len(loops)-1}
# Check grafts share exactly two faces per original border edge.
edges=Counter()
for face in faces:
    for a in range(len(face)):
        key=tuple(sorted((face[a],face[(a+1)%len(face)])))
        edges[key]+=1
if any(edges[e]!=2 for e in bridge_edges):raise RuntimeError("Unstitched retopology patch")
if any(x>2 for x in edges.values()):raise RuntimeError("Overlapping nonmanifold edge")
new=bpy.data.meshes.new("PawnFaceRetopo_v0004")
new.from_pydata(points,[],faces);new.update()
if len(new.polygons)!=len(faces):raise RuntimeError("Invalid retopo polygons")
head.data=new
clay=bpy.data.materials.get("Stone_clay_neutral")
if not clay:raise RuntimeError("Missing v0.0.3 material")
new.materials.append(clay)
dark=bpy.data.materials.new("AnatomicalSocketDepth")
dark.use_nodes=True
dark.diffuse_color=(.068,.055,.046,1)
n=dark.node_tree.nodes.get("Principled BSDF")
n.inputs["Base Color"].default_value=(.068,.055,.046,1)
n.inputs["Roughness"].default_value=.91
new.materials.append(dark)
for f,i in zip(new.polygons,mat_indices):
    f.material_index=i;f.use_smooth=True
# Eyeballs legitimately separate meshes behind integral eyelid topology.
def make_mat(name,rgb,rough):
    m=bpy.data.materials.new(name);m.use_nodes=True
    n=m.node_tree.nodes.get("Principled BSDF")
    n.inputs["Base Color"].default_value=(*rgb,1)
    n.inputs["Roughness"].default_value=rough
    return m
sclera=make_mat("StoneIvoryEyeball",(.75,.70,.61),.4)
iris=make_mat("AmberIris",(.45,.22,.08),.34)
pupil=make_mat("DarkPupil",(.026,.020,.016),.18)
def ball(name,xyz,r,mat,scale=(1,1,1)):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=32,ring_count=20,radius=r,location=xyz)
    obj=bpy.context.object;obj.name=name;obj.scale=scale
    obj.data.materials.append(mat)
    for f in obj.data.polygons:f.use_smooth=True
for name,x in (("L",-.034),("R",.034)):
    z=1.433
    surface=baseline_y(x,z)
    center=surface+.0128
    ball("Eyeball_"+name,(x,center,z),.0105,sclera,(1,.91,.86))
    ball("Iris_"+name,(x,surface+.0021,z-.0008),.00365,iris,(1,.42,1))
    ball("Pupil_"+name,(x,surface+.0008,z-.0008),.0016,pupil,(1,.42,1))
# Correct the transition surfaces around each patch, while keeping
# the constructed eyelid/lip loops and their cavity depths intact.
# Their previous rectangular-to-ellipse bridging produced steep relief folds.
def step(t):
    t=max(0.,min(1.,t))
    return t*t*(3-2*t)
for vertex in new.vertices:
    p=vertex.co
    x,z=p.x,p.z-1.422
    # Only the visible anterior face is affected.
    fw=step((-p.y-.012)/.056)
    eyes=0.
    for ex in (-.034,.034):
        dist=math.sqrt(((x-ex)/.019)**2+((z-.011)/.0063)**2)
        protect=step((dist-1.00)/.95)
        eyes=max(eyes,g(x,ex,.043)*g(z,.011,.044)*protect)
    lipdist=math.sqrt((x/.018)**2+((z+.064)/.00085)**2)
    lipprotect=step((lipdist-1.10)/3.2)
    mouth=g(x,0,.048)*g(z,-.064,.044)*lipprotect
    weight=.92*fw*max(eyes,mouth)
    # An anatomically restrained nose remains connected to the same mesh.
    nose=.0042*g(x,0,.013)*g(z,-.036,.020)
    target=baseline_y(x,p.z)-nose
    p.y=p.y*(1-weight)+target*weight
new.update()
# A small non-destructive mesh relaxer removes remaining transition chatter.
# Exclude eyelid margins and the mouth crease from the smoothing vertex group.
smooth_group=head.vertex_groups.new(name="Face_Transition_Relax")
weights=[]
for vertex in new.vertices:
    p=vertex.co
    x,z=p.x,p.z-1.422
    w=max(g(x,-.034,.047)*g(z,.011,.048),
          g(x,.034,.047)*g(z,.011,.048),
          g(x,0,.055)*g(z,-.064,.046))
    for ex in (-.034,.034):
        inner=math.sqrt(((x-ex)/.019)**2+((z-.011)/.0063)**2)
        w*=.22+.78*step((inner-1.05)/1.05)
    innerlip=math.sqrt((x/.018)**2+((z+.064)/.00085)**2)
    w*=.15+.85*step((innerlip-1.1)/3.0)
    if w>.02:
        smooth_group.add([vertex.index],min(1.,w),"REPLACE")
modifier=head.modifiers.new("OrganicFaceTransitionSmooth","SMOOTH")
modifier.factor=.68
modifier.iterations=12
modifier.vertex_group=smooth_group.name
head["loop_retopology_version"]="0.0.4"
head["validation"]="quad loops grafted to original continuous face; original preserved"
scene=bpy.context.scene
scene.render.engine="CYCLES";scene.cycles.samples=38
scene.render.resolution_x=900;scene.render.resolution_y=900;scene.render.resolution_percentage=100
scene.render.image_settings.file_format="PNG"
scene.view_settings.view_transform="Standard"
for lamp in bpy.data.objects:
    if lamp.type=="LIGHT":lamp.data.energy=115 if "key" in lamp.name.lower() else 54
views={"front":((0,-2,1.45),(0,0,1.422),.335),
       "profile":((2,0,1.45),(0,0,1.422),.335),
       "threequarter":((1.2,-1.8,1.46),(0,0,1.422),.335),
       "face-detail":((.30,-1.8,1.45),(0,0,1.409),.20)}
for name,(pos,target,scale) in views.items():
    cam=bpy.data.objects.get("Camera_"+name)
    if cam is None:
        bpy.ops.object.camera_add(location=pos);cam=bpy.context.object;cam.name="Camera_"+name
    cam.location=pos
    cam.rotation_euler=(Vector(target)-cam.location).to_track_quat("-Z","Y").to_euler()
    cam.data.type="ORTHO";cam.data.ortho_scale=scale
scene["build_version"]="face-retopo-v0.0.4"
scene.camera=bpy.data.objects["Camera_front"]
model=out/"pawn-face-retopo-v0.0.4.blend"
bpy.ops.wm.save_as_mainfile(filepath=str(model))
for name in views:
    scene.camera=bpy.data.objects["Camera_"+name]
    scene.render.filepath=str(out/("pawn-face-retopo-v0.0.4-"+name+".png"))
    bpy.ops.render.render(write_still=True)
report={"version":"0.0.4","head_vertices":len(new.vertices),"head_faces":len(new.polygons),
        "patches":details,"watertight_graft_edges":True,"head_and_eyelid_unified":True,
        "actual_blender_model":model.name,"views":list(views),
        "remaining":"concept-art comparison, blink topology and facial deformation review"}
(out/"report.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
print("CHERPG_V0004_SUCCESS",json.dumps(report))
