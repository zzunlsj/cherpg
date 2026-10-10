"""CheRPG Pawn head v0.0.10 – soften v0.0.9 anatomical ear sculpt.
Continue actual high-density Blender scene. NO eyeballs, iris or pupils.
Only integral auricle, nose and eyelid relief. Mouth preserved.
"""
import bpy,math,json,sys
from pathlib import Path
from mathutils import Vector
a=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
if len(a)!=2:raise RuntimeError("Usage: -- v0.0.9.blend output-directory")
src,out=Path(a[0]).resolve(),Path(a[1]).resolve()
if not src.is_file():raise FileNotFoundError(src)
out.mkdir(parents=True,exist_ok=True)
if Path(bpy.data.filepath).resolve()!=src:bpy.ops.wm.open_mainfile(filepath=str(src))
head=bpy.data.objects.get("Pawn_Head_FaceBlockout")
if head is None or head.type!="MESH" or head.get("facial_shape_version")!="0.0.9":
    raise RuntimeError("Expected published high-res v0.0.9 head")
if len(head.data.vertices)!=192368:raise RuntimeError("Unexpected high-density vertex count")
bad_names=("Eyeball_","Iris_","Pupil_")
if any(o.name.startswith(bad_names) for o in bpy.data.objects):
    raise RuntimeError("Unexpected ocular object")
def g(x,c,s):return math.exp(-((x-c)/s)**2)
def clamp(v):return max(0.,min(1.,v))
def smooth(v):v=clamp(v);return v*v*(3.-2.*v)
def distpoly(u,v,pts):
    best=1e6
    for (ax,ay),(bx,by) in zip(pts,pts[1:]):
        dx,dy=bx-ax,by-ay
        t=clamp(((u-ax)*dx+(v-ay)*dy)/(dx*dx+dy*dy+1e-10))
        best=min(best,math.hypot(u-ax-t*dx,v-ay-t*dy))
    return best
helix=[(-.58,.51),(-.53,.78),(-.29,.97),(.11,1.03),(.47,.94),(.73,.67),(.79,.22),(.74,-.26),(.54,-.66),(.19,-.85)]
anti=[(.22,-.56),(.32,-.35),(.39,-.08),(.35,.23),(.24,.42)]
crus1=[(.24,.42),(.23,.62),(.43,.78)]
crus2=[(.24,.42),(-.03,.60),(-.24,.63)]
def fields(y,z):
    u=(y-.014)/.025;v=(z-1.414)/.031
    e=math.hypot((u-.035-.065*v)/.96,(v+.010)/1.08)
    return u,v,e,distpoly(u,v,helix),distpoly(u,v,anti),distpoly(u,v,crus1),distpoly(u,v,crus2)
def ear_field(x,y,z,old):
    u,v,e,h,a,c1,c2=fields(y,z)
    side=smooth((abs(x)-.066)/.016)
    support=side*smooth((1.18-e)/.28)
    if old:
        amount=(.0072*g(h,0.,.112)+.0048*g(a,0.,.125)
                +.0035*g(c1,0.,.115)+.0033*g(c2,0.,.110)
                -.0042*g(u,-.26,.34)*g(v,-.09,.38)
                +.0034*g(u,-.57,.17)*g(v,-.29,.20)
                +.0030*g(u,.13,.29)*g(v,-.83,.20)
                +.0012*g(u,-.51,.19)*g(v,.54,.20)+.0010*g(e,.35,.60))
    else:
        # Broader, lower-amplitude fields prevent hard-edged spikes in v0.0.9.
        amount=(.00375*g(h,0.,.190)+.00235*g(a,0.,.200)
                +.00145*g(c1,0.,.190)+.00130*g(c2,0.,.180)
                -.00190*g(u,-.24,.38)*g(v,-.10,.39)
                +.00140*g(u,-.58,.21)*g(v,-.31,.24)
                +.00125*g(u,.13,.34)*g(v,-.78,.27)
                +.00065*g(u,-.51,.22)*g(v,.54,.26)+.00070*g(e,.35,.65))
    return support*amount
old_coords=[v.co.copy() for v in head.data.vertices]
counts={"ear":0,"nose":0,"eye_contour":0}
nose_group=head.vertex_groups.get("v00010_nose_relax") or head.vertex_groups.new(name="v00010_nose_relax")
ear_group=head.vertex_groups.get("v00010_ear_relax") or head.vertex_groups.new(name="v00010_ear_relax")
for vert in head.data.vertices:
    p=vert.co;x,y,z=p.x,p.y,p.z
    u,v,e,*_=fields(y,z)
    if abs(x)>.057 and e<1.25:
        # Invert the actual v0.0.9 displacement; then rebuild at less than
        # half the former amplitude. No disconnected mesh or add-on primitive.
        direction=1. if x>=0. else -1.
        x0=x
        for i in range(7):
            x0=x-direction*ear_field(x0,y,z,True)
        delta=direction*ear_field(x0,y,z,False)
        xnew=x0+delta
        if abs(xnew-x)>.0000003:
            p.x=xnew
            counts["ear"]+=1
        weight=smooth((abs(x0)-.071)/.013)*smooth((1.05-e)/.24)
        if weight>.02:ear_group.add([vert.index],min(1.,weight),"REPLACE")
    # Keep nose attached to the face, rounding the block-like tip and alae.
    frontal=smooth((-y-.043)/.050)
    target=(-.00220*g(x,0.,.013)*g(z,1.385,.014)
            -.00095*g(x,0.,.012)*g(z,1.409,.025)
            +.00065*(g(x,-.014,.006)+g(x,.014,.006))*g(z,1.382,.008))
    dy=frontal*target
    if abs(dy)>0.0000003:
        p.y+=dy;counts["nose"]+=1
    wn=frontal*g(x,0.,.031)*g(z,1.389,.030)
    if wn>.03:nose_group.add([vert.index],min(1.,wn),"REPLACE")
    # Only thin integrally sculpted upper/lower stone eyelid folds.
    eye_front=smooth((-y-.048)/.035)
    eyelid=0.
    for cx in (-.034,.034):
        eyelid+=(-.0008*g(x,cx,.023)*g(z,1.437,.0035)
                  +.00025*g(x,cx,.023)*g(z,1.428,.0037))
    eye_delta=eye_front*eyelid
    if abs(eye_delta)>0.0000003:
        p.y+=eye_delta;counts["eye_contour"]+=1
# Mesh regularization in deliberately masked ear and nose regions.
bpy.ops.object.select_all(action="DESELECT")
head.select_set(True);bpy.context.view_layer.objects.active=head
for name,group,factor,iterations in (
    ("Nose_OrganicRelax_v00010",nose_group,.55,36),
    ("Ear_OrganicRelax_v00010",ear_group,.46,18)):
    modifier=head.modifiers.new(name,"SMOOTH")
    modifier.factor=factor;modifier.iterations=iterations
    modifier.vertex_group=group.name
    bpy.ops.object.modifier_apply(modifier=modifier.name)
for face in head.data.polygons:face.use_smooth=True
head.data.update()
max_move=max((v.co-previous).length for v,previous in zip(head.data.vertices,old_coords))
if not (counts["ear"]>1000 and counts["nose"]>500 and counts["eye_contour"]>200):
    raise RuntimeError("Insufficient facial-sculpt coverage "+repr(counts))
if max_move>.030:raise RuntimeError("Unstable vertex movement "+str(max_move))
if any(not all(math.isfinite(float(c)) for c in vert.co) for vert in head.data.vertices):
    raise RuntimeError("Non-finite vertex coordinate")
if any(o.name.startswith(bad_names) for o in bpy.data.objects):
    raise RuntimeError("Ocular geometry reappeared")
head["facial_shape_version"]="0.0.10"
head["eye_policy"]="shallow stone eyelid shape only; NO eyeballs/iris/pupils"
head["ear_construction"]="softened non-concentric helix/antihelix/concha with localized regularization"
head["status"]="SCULPT CHECKPOINT: manual likeness approval pending"
scene=bpy.context.scene
scene["build_version"]="pawn-head-shapes-v0.0.10"
scene["approval"]="NO: visual review required"
scene.render.engine="CYCLES";scene.cycles.samples=22
scene.render.resolution_x=768;scene.render.resolution_y=768
scene.render.resolution_percentage=100
scene.render.image_settings.file_format="PNG"
scene.view_settings.view_transform="Standard"
views={
"front":((0,-2,1.45),(0,0,1.422),.335),
"profile":((2,0,1.45),(0,0,1.422),.335),
"threequarter":((1.25,-1.7,1.48),(0,0,1.422),.335),
"face-detail":((.32,-1.8,1.45),(0,0,1.418),.205),
"ear-detail":((1.65,-.54,1.46),(0,.015,1.411),.172)}
for name,(loc,target,scale) in views.items():
    cam=bpy.data.objects.get("Camera_"+name)
    if cam is None:
        bpy.ops.object.camera_add(location=loc);cam=bpy.context.object;cam.name="Camera_"+name
    cam.location=loc
    cam.rotation_euler=(Vector(target)-cam.location).to_track_quat("-Z","Y").to_euler()
    cam.data.type="ORTHO";cam.data.ortho_scale=scale
scene.camera=bpy.data.objects["Camera_front"]
dst=out/"pawn-head-shapes-v0.0.10.blend"
bpy.ops.wm.save_as_mainfile(filepath=str(dst))
for name in views:
    scene.camera=bpy.data.objects["Camera_"+name]
    scene.render.filepath=str(out/("pawn-head-shapes-v0.0.10-"+name+".png"))
    bpy.ops.render.render(write_still=True)
report={"version":"0.0.10","source":src.name,"blend":dst.name,
"modified_vertices":counts,"head_vertices":len(head.data.vertices),
"max_displacement_m":round(max_move,7),"eye_objects":[],
"eye_policy":"shallow stone eyelid shape only",
"views":list(views),"approved":False,
"note":"Softened ear spikes and nose plane; mouth intentionally unchanged"}
(out/"report.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
print("CHERPG_V00010_SUCCESS",json.dumps(report))
