"""CheRPG Pawn head v0.0.6: refine integrated ear, nose and eyelid relief.
No ocular globes, irises, pupils, or separate facial primitive objects.
Starts from the published, real v0.0.5 Blender checkpoint.
"""
import bpy, math, json, sys
from pathlib import Path
from mathutils import Vector
args=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
if len(args)!=2: raise RuntimeError("Pass checkpoint .blend and output directory")
src,out=map(lambda a:Path(a).resolve(),args)
if not src.is_file(): raise FileNotFoundError(src)
out.mkdir(parents=True,exist_ok=True)
if Path(bpy.data.filepath).resolve()!=src:
    bpy.ops.wm.open_mainfile(filepath=str(src))
head=bpy.data.objects.get("Pawn_Head_FaceBlockout")
if head is None or head.type!="MESH" or head.get("facial_shape_version")!="0.0.5":
    raise RuntimeError("Requires integrated v0.0.5 head")
for obj in bpy.data.objects:
    if obj.name.startswith(("Eyeball_","Iris_","Pupil_")):
        raise RuntimeError("Disallowed eye object: "+obj.name)
if len(head.data.vertices)!=12076: raise RuntimeError("Unexpected vertex topology")
before=[v.co.copy() for v in head.data.vertices]
def gauss(v,c,s): return math.exp(-((v-c)/s)**2)
def smooth(v):
    v=max(0.0,min(1.0,v))
    return v*v*(3.0-2.0*v)
# Indices of the two integrated eye retopology regions, unchanged since v0.0.4.
EYE_OFFSET=10869
EYE_PATCH_VERTS=393
eye_ids=set(range(EYE_OFFSET,EYE_OFFSET+2*EYE_PATCH_VERTS))
counts={"eye":0,"nose":0,"ear":0}
for vert in head.data.vertices:
    p=vert.co
    x,y,z=p.x,p.y,p.z
    # Anterior eye region: restrained brow ridge and infraorbital transition,
    # shallow sculpt seam rather than socket or separate eyeball.
    if vert.index in eye_ids:
        cx=-.034 if vert.index<EYE_OFFSET+EYE_PATCH_VERTS else .034
        rim=gauss(abs(x-cx),.012,.009)
        upper=gauss(z,1.439,.005)
        lower=gauss(z,1.426,.005)
        delta=-.00085*rim*upper + .00030*rim*lower
        p.y+=delta
        if abs(delta)>1e-6: counts["eye"]+=1
        continue
    # Nose: taper the bridge smoothly into tip; soften nostril wings without
    # generating black nostril holes or disconnected spheres.
    front=smooth((-y-.030)/.043)
    bridge=gauss(x,0,.009)*gauss(z,1.407,.020)
    tip=gauss(x,0,.010)*gauss(z,1.384,.008)
    wing=(gauss(x,-.012,.005)+gauss(x,.012,.005))*gauss(z,1.382,.006)
    delta=front*(-.00135*bridge-.00120*tip-.00065*wing)
    if abs(delta)>1e-6:
        p.y+=delta
        counts["nose"]+=1
    # Auricles: asymmetrical radial structure in the original continuous
    # mesh, with a small superior helix, antihelix and inset concha.
    # Each is weighted around the side of head and disappears at the seam.
    side=smooth((abs(x)-.066)/.019)
    yc,zc=.014,1.414
    yy=(y-yc)/.025
    zz=(z-zc)/.030
    r=math.sqrt(yy*yy+zz*zz)
    theta=math.atan2(zz,yy)
    taper=smooth((1.15-r)/.30)
    helix=.0028*gauss(r,.84,.16)*(1+.13*math.sin(theta))
    antihelix=.00125*gauss(r,.55,.13)*gauss(zz,.10,.85)
    concha=-.00235*gauss(r,.30,.22)
    lobe=.00155*gauss(z,1.391,.009)*gauss(y,.014,.014)
    offset=side*taper*(helix+antihelix+concha+lobe)
    if abs(offset)>1e-6:
        p.x+=(1 if x>=0 else -1)*offset
        counts["ear"]+=1
head.data.update()
max_move=max((v.co-original).length for v,original in zip(head.data.vertices,before))
assert max_move<.006, max_move
assert counts["ear"]>100 and counts["nose"]>30 and counts["eye"]>15, counts
assert all(all(math.isfinite(float(q)) for q in v.co) for v in head.data.vertices)
head["facial_shape_version"]="0.0.6"
head["eye_policy"]="NO eyeballs/iris/pupils: surface shape only"
head["detail_pass"]="integrated helix/antihelix/concha, bridge/tip/alar and eyelid relief"
scene=bpy.context.scene
scene["build_version"]="pawn-head-shapes-v0.0.6"
scene["approval"]="PENDING artistic comparison; do not infer approval from build"
scene.render.engine="CYCLES"
scene.cycles.samples=48
scene.render.resolution_x=900
scene.render.resolution_y=900
scene.render.resolution_percentage=100
scene.render.image_settings.file_format="PNG"
scene.view_settings.view_transform="Standard"
def look(obj,target):
    obj.rotation_euler=(Vector(target)-obj.location).to_track_quat("-Z","Y").to_euler()
views={
 "front":((0,-2,1.45),(0,0,1.422),.335),
 "profile":((2,0,1.45),(0,0,1.422),.335),
 "threequarter":((1.25,-1.7,1.48),(0,0,1.422),.335),
 "face-detail":((.32,-1.8,1.45),(0,0,1.418),.205),
 "ear-detail":((1.65,-.54,1.46),(0,.015,1.411),.172)}
for name,(loc,target,scale) in views.items():
    cam=bpy.data.objects.get("Camera_"+name)
    if cam is None:
        bpy.ops.object.camera_add(location=loc)
        cam=bpy.context.object;cam.name="Camera_"+name
    cam.location=loc;look(cam,target)
    cam.data.type="ORTHO";cam.data.ortho_scale=scale
scene.camera=bpy.data.objects["Camera_front"]
model=out/"pawn-head-shapes-v0.0.6.blend"
bpy.ops.wm.save_as_mainfile(filepath=str(model))
for name in views:
    scene.camera=bpy.data.objects["Camera_"+name]
    scene.render.filepath=str(out/("pawn-head-shapes-v0.0.6-"+name+".png"))
    bpy.ops.render.render(write_still=True)
remaining=[o.name for o in bpy.data.objects if o.name.startswith(("Eyeball_","Iris_","Pupil_"))]
assert not remaining,remaining
report={"version":"0.0.6","source":src.name,"blend":model.name,
        "modified_vertices":counts,"max_displacement_m":round(max_move,7),
        "eye_objects":[],"eye_policy":"shape only",
        "continuous_head_mesh":True,"views":list(views),
        "approval":"technical checkpoint; visual similarity not yet accepted"}
(out/"report.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
print("CHERPG_V0006_SUCCESS",json.dumps(report))
