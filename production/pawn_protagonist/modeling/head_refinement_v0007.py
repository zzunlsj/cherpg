"""CheRPG v0.0.7: reshape ring-like ears and soften empty eye slits.
No eyeballs, irises, pupils. The existing mouth is deliberately untouched.
"""
import bpy,math,sys,json
from pathlib import Path
from mathutils import Vector
argv=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
if len(argv)!=2:raise RuntimeError("Usage: -- input.blend output")
src,out=Path(argv[0]).resolve(),Path(argv[1]).resolve()
if not src.is_file():raise FileNotFoundError(src)
out.mkdir(parents=True,exist_ok=True)
if Path(bpy.data.filepath).resolve()!=src:bpy.ops.wm.open_mainfile(filepath=str(src))
head=bpy.data.objects.get("Pawn_Head_FaceBlockout")
if head is None or head.type!="MESH" or head.get("facial_shape_version")!="0.0.6":raise RuntimeError("Expected v0.0.6")
assert len(head.data.vertices)==12076
if any(o.name.startswith(("Eyeball_","Iris_","Pupil_")) for o in bpy.data.objects):raise RuntimeError("Forbidden eye objects")
def g(v,c,s):return math.exp(-((v-c)/s)**2)
def clamp(v):return max(0.,min(1.,v))
def smooth(v):v=clamp(v);return v*v*(3-2*v)
old=[v.co.copy() for v in head.data.vertices]
counts=dict(ear=0,eye=0,nose=0)
eye_start=10869;eye_patch=393
for v in head.data.vertices:
    p=v.co
    x,y,z=p.x,p.y,p.z
    if eye_start<=v.index<eye_start+2*eye_patch:
        n=(v.index-eye_start)//eye_patch
        cx=(-.034,.034)[n]
        ring=(v.index-eye_start)%eye_patch
        # Flatten exaggerated open-looking middle of the outlined shape,
        # preserving shallow upper/lower lid topology instead of carving an opening.
        if ring<392:
            layer=ring//56
            weight=(0.0,.06,.16,.33,.56,.64,.62)[layer]
        else:weight=.68
        dz=z-1.433
        p.z=1.433+dz*(1-.24*weight)
        p.y+=.00125*weight*g(x,cx,.026)
        counts["eye"]+=1
        continue
    # Preserve original nose but smooth out sharp forward point, giving
    # a continuous bridge to tip transition.
    front=smooth((-y-.034)/.044)
    w=front*g(x,0,.013)*g(z,1.383,.009)
    delta=.00065*w
    if delta>1e-7:p.y+=delta;counts["nose"]+=1
    # Disc-like auricle relief becomes an asymmetric, tilted ear.
    # Carve concha more deeply at rear-central position; break concentric helix.
    side=smooth((abs(x)-.065)/.020)
    yc,zc=.014,1.414
    yy=(y-yc)/.025;zz=(z-zc)/.031
    r=math.sqrt(yy*yy+zz*zz)
    theta=math.atan2(zz,yy)
    fade=smooth((1.23-r)/.30)
    if side>.002 and fade>.001:
        upper=g(zz,.56,.37)
        back=g(yy,.36,.34)
        inner=g(yy,-.07,.35)*g(zz,.02,.45)
        # less protrusion on front rim; stronger fold on posterior-superior edge
        dx=side*fade*(.0022*upper*back-.00185*g(r,.83,.13)*g(yy,-.40,.45)
                      -.00145*inner+.0011*g(zz,-.62,.20)*g(yy,.10,.40))
        p.x+=(1 if x>=0 else -1)*dx
        # angular pull yields a leaning nonconcentric upper ear silhouette
        p.z+=side*fade*(.0025*upper*back-.0010*g(zz,-.65,.26))
        p.y+=side*fade*(.0015*upper-.0009*inner)
        counts["ear"]+=1
head.data.update()
max_shift=max((v.co-o).length for v,o in zip(head.data.vertices,old))
if max_shift>.008:raise RuntimeError("Exceeded safe vertex movement: "+str(max_shift))
if counts["ear"]<100 or counts["eye"]<100 or counts["nose"]<20:raise RuntimeError(str(counts))
if any(not all(math.isfinite(float(q)) for q in v.co) for v in head.data.vertices):raise RuntimeError("Non-finite geometry")
head["facial_shape_version"]="0.0.7"
head["eye_policy"]="shallow surface outline only; no eyeballs, iris, pupils"
scene=bpy.context.scene
scene["build_version"]="pawn-head-shapes-v0.0.7"
scene["approval"]="UNAPPROVED until reference overlay and art review"
scene.render.engine="CYCLES";scene.cycles.samples=48
scene.render.resolution_x=900;scene.render.resolution_y=900
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
    if cam is None:bpy.ops.object.camera_add(location=loc);cam=bpy.context.object;cam.name="Camera_"+name
    cam.location=loc;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat("-Z","Y").to_euler()
    cam.data.type="ORTHO";cam.data.ortho_scale=scale
scene.camera=bpy.data.objects["Camera_front"]
dst=out/"pawn-head-shapes-v0.0.7.blend"
bpy.ops.wm.save_as_mainfile(filepath=str(dst))
for name in views:
    scene.camera=bpy.data.objects["Camera_"+name]
    scene.render.filepath=str(out/("pawn-head-shapes-v0.0.7-"+name+".png"))
    bpy.ops.render.render(write_still=True)
report={"version":"0.0.7","source":src.name,"blend":dst.name,
"modified_vertices":counts,"max_displacement_m":round(max_shift,7),
"eye_objects":[],"eye_policy":"only outline, no eyeballs","approved":False,"views":list(views)}
(out/"report.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
print("CHERPG_V0007_SUCCESS",json.dumps(report))
