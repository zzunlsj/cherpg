"""CheRPG Pawn head v0.0.9 — anatomy-led surface sculpt with subdivided ear relief.
Research: NIH ear landmarks, Blender Studio facial edge flow and sculpting.
Input: production v0.0.8 + index-matched v0.0.4 neutral ear baseline.
STRICT: no eyeballs/iris/pupils; eye REGION is a continuous stone lid plane.
No detached ear, nose or eye objects. Mouth is out of scope.
"""
import bpy, math, json, sys
from pathlib import Path
from mathutils import Vector

argv=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
if len(argv)!=3: raise RuntimeError("Usage: -- head-v0.0.8.blend head-v0.0.4.blend output-dir")
source,baseline,output=(Path(s).resolve() for s in argv)
if not source.is_file() or not baseline.is_file(): raise FileNotFoundError((source,baseline))
output.mkdir(parents=True,exist_ok=True)
if Path(bpy.data.filepath).resolve()!=source:
    bpy.ops.wm.open_mainfile(filepath=str(source))
head=bpy.data.objects.get("Pawn_Head_FaceBlockout")
if head is None or head.type!="MESH" or head.get("facial_shape_version")!="0.0.8":
    raise RuntimeError("Expected v0.0.8 input head")
badprefix=("Eyeball_","Iris_","Pupil_")
if any(o.name.startswith(badprefix) for o in bpy.data.objects):
    raise RuntimeError("Eye globes/irises/pupils are forbidden")
with bpy.data.libraries.load(str(baseline),link=False) as (a,b):
    if "Pawn_Head_FaceBlockout" not in a.objects:raise RuntimeError("Missing baseline head")
    b.objects=["Pawn_Head_FaceBlockout"]
ref=b.objects[0]
original=[v.co.copy() for v in ref.data.vertices]
if len(original)!=12076 or len(head.data.vertices)!=len(original):
    raise RuntimeError("Input topology is not vertex-aligned")
bpy.data.objects.remove(ref,do_unlink=True)

def g(a,c,w):return math.exp(-((a-c)/w)**2)
def smooth(v):v=max(0.,min(1.,v));return v*v*(3.-2.*v)
def lerp(a,b,t):return a*(1-t)+b*t
def baseline_y(x,z):
    zz=(z-1.422)/.126
    jaw=max(0.,(-zz-.12)/.85)
    w=.093*(.91+.11*g(zz,.42,.55)+.06*g(zz,-.12,.32)-.24*jaw**1.2)
    depth=.089*(1-.07*jaw)
    return -depth*math.sqrt(max(.035,1-zz*zz-(x/w)**2))
def polyline_distance(u,v,points):
    best=1e9
    for (ax,ay),(bx,by) in zip(points,points[1:]):
        dx=bx-ax;dy=by-ay
        t=max(0.,min(1.,((u-ax)*dx+(v-ay)*dy)/(dx*dx+dy*dy+1e-10)))
        best=min(best,math.hypot(u-ax-t*dx,v-ay-t*dy))
    return best

# Freeze the pre-existing softening modifier, before targeted eye and ear correction.
bpy.ops.object.select_all(action="DESELECT")
head.select_set(True);bpy.context.view_layer.objects.active=head
bpy.ops.object.mode_set(mode="OBJECT")
for mod in list(head.modifiers):
    if mod.type=="SMOOTH":
        bpy.ops.object.modifier_apply(modifier=mod.name)

# Return the radial ear rings to the neutral source head while retaining the
# modified nose and mouth everywhere outside the registered auricle mask.
ear_recovered=0
for vert,b in zip(head.data.vertices,original):
    p=vert.co
    u=(b.y-.014)/.025;v=(b.z-1.414)/.031
    r=math.hypot(u,v)
    mask=smooth((abs(b.x)-.058)/.015)*smooth((1.47-r)/.26)
    if mask>.0005:
        t=.995*mask
        p.x=lerp(p.x,b.x,t)
        p.y=lerp(p.y,b.y,t)
        p.z=lerp(p.z,b.z,t)
        ear_recovered+=1

# An eye-shape relief WITHOUT socket, globe or any aperture. Flatten the
# dark-looking slit to its analytic face envelope and use only gentle upper
# eyelid crease shading and lower lid relief. All surface faces are stone.
eye_start=10869;eye_patch=393
eye_fixed=0
for vert in head.data.vertices:
    if not eye_start<=vert.index<eye_start+2*eye_patch:continue
    p=vert.co
    k=(vert.index-eye_start)%eye_patch
    layer=k//56 if k<392 else 7
    t=(0.,.34,.58,.82,1.,1.,1.,1.)[layer]
    cx=(-.034,.034)[(vert.index-eye_start)//eye_patch]
    p.z=1.433+(p.z-1.433)*(1-.30*t)
    x,z=p.x,p.z
    brow=-.00040*g(x,cx,.023)*g(z,1.438,.004)
    lower= .00015*g(x,cx,.023)*g(z,1.429,.003)
    target=baseline_y(x,z)+brow+lower
    p.y=lerp(p.y,target,t)
    eye_fixed+=1
for face in head.data.polygons:
    if any(eye_start<=index<eye_start+2*eye_patch for index in face.vertices):
        face.material_index=0
head.data.update()

# Raise actual local sculpting resolution, rather than stacking detail
# fields onto a few coarse side-head vertices.
sub=head.modifiers.new("SculptResolution_v0009","SUBSURF")
sub.subdivision_type="SIMPLE"
sub.levels=2;sub.render_levels=2
bpy.ops.object.modifier_apply(modifier=sub.name)
if len(head.data.vertices)<60000: raise RuntimeError("Subdivision did not apply")
high_res_count=len(head.data.vertices)
before=[v.co.copy() for v in head.data.vertices]

# Anatomical curves in the side (Y/Z) plane, rather than concentric circles.
# u<0 is toward the face; v>0 is toward the crown.
helix=[(-.58,.51),(-.53,.78),(-.29,.97),(.11,1.03),(.47,.94),
       (.73,.67),(.79,.22),(.74,-.26),(.54,-.66),(.19,-.85)]
antihelix=[(.22,-.56),(.32,-.35),(.39,-.08),(.35,.23),(.24,.42)]
upper_crus=[(.24,.42),(.23,.62),(.43,.78)]
lower_crus=[(.24,.42),(-.03,.60),(-.24,.63)]
reworked=0;nose_reworked=0;peak=0.
for vert in head.data.vertices:
    p=vert.co
    x,y,z=p.x,p.y,p.z
    # Restrict nose changes to anterior portion to retain scale and nostril policy.
    face=smooth((-y-.035)/.050)
    tip=g(x,0.,.011)*g(z,1.385,.010)
    alae=(g(x,-.011,.006)+g(x,.011,.006))*g(z,1.383,.008)
    nose_delta=face*(.00070*tip-.00105*alae)
    if abs(nose_delta)>1e-7:
        p.y+=nose_delta
        nose_reworked+=1
    # Ear field on both sides of the existing single mesh.
    side=smooth((abs(x)-.066)/.016)
    if side<.0001:continue
    u=(y-.014)/.025
    v=(z-1.414)/.031
    e=math.sqrt(((u-.035-.065*v)/.96)**2+((v+.010)/1.08)**2)
    support=side*smooth((1.18-e)/.28)
    if support<.0005:continue
    # Helix = broken C, antihelix = branched Y, concha = asymmetric bowl.
    h=.0072*g(polyline_distance(u,v,helix),0.,.112)
    a=.0048*g(polyline_distance(u,v,antihelix),0.,.125)
    y1=.0035*g(polyline_distance(u,v,upper_crus),0.,.115)
    y2=.0033*g(polyline_distance(u,v,lower_crus),0.,.110)
    bowl=-.0042*g(u,-.26,.34)*g(v,-.09,.38)
    tragus=.0034*g(u,-.57,.17)*g(v,-.29,.20)
    lobe=.0030*g(u,.13,.29)*g(v,-.83,.20)
    root=.0012*g(u,-.51,.19)*g(v,.54,.20)
    base=.0010*g(e,.35,.60)
    delta=support*(h+a+y1+y2+bowl+tragus+lobe+root+base)
    p.x+=(1 if x>=0 else -1)*delta
    reworked+=1
    peak=max(peak,abs(delta))

head.data.update()
max_displacement=max((vert.co-old).length for vert,old in zip(head.data.vertices,before))
if not (ear_recovered>120 and eye_fixed==786 and reworked>400 and nose_reworked>100):
    raise RuntimeError("Coverage check failed: "+str((ear_recovered,eye_fixed,reworked,nose_reworked)))
if peak<.004 or peak>.020:raise RuntimeError("Unexpected ear relief magnitude: "+str(peak))
if any(not all(math.isfinite(float(t)) for t in v.co) for v in head.data.vertices):
    raise RuntimeError("Nonfinite mesh coordinates")
if any(o.name.startswith(badprefix) for o in bpy.data.objects):
    raise RuntimeError("Ocular object appeared during sculpt")

head["facial_shape_version"]="0.0.9"
head["eye_policy"]="CONTINUOUS STONE SHAPE ONLY; zero ocular objects"
head["ear_construction"]="non-radial C-shaped helix, branched antihelix, concha, tragus, lobule"
head["sculpt_status"]="high-resolution sculpt checkpoint; RETOPOLOGY REQUIRED for rigging"
scene=bpy.context.scene
scene["build_version"]="pawn-head-shapes-v0.0.9"
scene["approval"]="visual comparison REQUIRED; not approved for Godot"
scene.render.engine="CYCLES";scene.cycles.samples=20
scene.render.resolution_x=768;scene.render.resolution_y=768
scene.render.resolution_percentage=100
scene.render.image_settings.file_format="PNG"
scene.view_settings.view_transform="Standard"
views={
"front":((0,-2,1.45),(0,0,1.422),.335),
"profile":((2,0,1.45),(0,0,1.422),.335),
"threequarter":((1.25,-1.7,1.48),(0,0,1.422),.335),
"face-detail":((.32,-1.8,1.45),(0,0,1.418),.205),
"ear-detail":((1.65,-.54,1.46),(0,.015,1.411),.172)
}
for name,(pos,target,scale) in views.items():
    cam=bpy.data.objects.get("Camera_"+name)
    if cam is None:
        bpy.ops.object.camera_add(location=pos)
        cam=bpy.context.object;cam.name="Camera_"+name
    cam.location=pos
    cam.rotation_euler=(Vector(target)-cam.location).to_track_quat("-Z","Y").to_euler()
    cam.data.type="ORTHO";cam.data.ortho_scale=scale
scene.camera=bpy.data.objects["Camera_front"]
dst=output/"pawn-head-shapes-v0.0.9.blend"
bpy.ops.wm.save_as_mainfile(filepath=str(dst))
for name in views:
    scene.camera=bpy.data.objects["Camera_"+name]
    scene.render.filepath=str(output/("pawn-head-shapes-v0.0.9-"+name+".png"))
    bpy.ops.render.render(write_still=True)
bad=[o.name for o in bpy.data.objects if o.name.startswith(badprefix)]
if bad:raise RuntimeError("Forbidden ocular objects: "+str(bad))
report={"version":"0.0.9","source":source.name,"baseline":baseline.name,
"blend":dst.name,"ear_reset_verts":ear_recovered,"eye_region_verts":eye_fixed,
"ear_sculpt_verts":reworked,"nose_transition_verts":nose_reworked,
"head_vertices":high_res_count,"max_sculpt_delta_m":round(max_displacement,7),
"peak_ear_relief_m":round(peak,7),"eye_objects":bad,
"eye_policy":"stone contour only","approval":"PENDING visual reference review",
"views":list(views),"research":["NIH external ear anatomy","Blender Studio facial topology"]}
(output/"report.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
print("CHERPG_V0009_SUCCESS",json.dumps(report))
