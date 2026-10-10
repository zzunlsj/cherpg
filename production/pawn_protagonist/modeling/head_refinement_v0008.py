"""CheRPG Pawn head v0.0.8 — rebuild anatomical auricle relief from baseline.
Input: approved-as-technical-checkpoint v0.0.7, plus untouched v0.0.4
vertex-matched mesh. No eyeballs/irises/pupils; eye region is closed stone.
Five real Blender renders; visual approval is intentionally NOT automatic.
"""
import bpy, math, json, sys
from pathlib import Path
from mathutils import Vector
args=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
if len(args)!=3:
    raise RuntimeError("Usage: -- head-v0.0.7.blend base-v0.0.4.blend outdir")
src,base_file,out=(Path(a).resolve() for a in args)
if not src.is_file() or not base_file.is_file():raise FileNotFoundError((src,base_file))
out.mkdir(parents=True,exist_ok=True)
if Path(bpy.data.filepath).resolve()!=src:
    bpy.ops.wm.open_mainfile(filepath=str(src))
head=bpy.data.objects.get("Pawn_Head_FaceBlockout")
if head is None or head.type!="MESH" or head.get("facial_shape_version")!="0.0.7":
    raise RuntimeError("Expected v0.0.7 Pawn head")
bad=[o.name for o in bpy.data.objects
     if o.name.startswith(("Eyeball_","Iris_","Pupil_"))]
if bad:raise RuntimeError("Disallowed ocular objects: "+str(bad))
# Read original mesh into data only, not the scene. Matching indexed topology
# lets us undo the circular v0.0.5-v0.0.7 ear deformation cleanly.
with bpy.data.libraries.load(str(base_file),link=False) as (available,loaded):
    if "Pawn_Head_FaceBlockout" not in available.objects:
        raise RuntimeError("Missing baseline mesh")
    loaded.objects=["Pawn_Head_FaceBlockout"]
base_obj=loaded.objects[0]
if base_obj is None or base_obj.type!="MESH":raise RuntimeError("Unable to load baseline mesh")
base_coords=[v.co.copy() for v in base_obj.data.vertices]
if len(base_coords)!=len(head.data.vertices) or len(base_coords)!=12076:
    raise RuntimeError("Vertex topology mismatch")
bpy.data.objects.remove(base_obj,do_unlink=True)
def gaussian(v,c,s):return math.exp(-((v-c)/s)**2)
def smooth(v):
    v=max(0.0,min(1.0,v))
    return v*v*(3.0-2.0*v)
before=[v.co.copy() for v in head.data.vertices]
counts={"ear_reset_and_sculpt":0,"eye_contour":0,"nose_transition":0}
EYE_START,EYE_PATCH=10869,393
for v in head.data.vertices:
    p=v.co; x,y,z=p.x,p.y,p.z
    # Eye region: close the stylized lid impression further, retaining a
    # soft upper-fold contour without any artificial eyeball or dark socket.
    if EYE_START<=v.index<EYE_START+2*EYE_PATCH:
        n=(v.index-EYE_START)//EYE_PATCH
        local=(v.index-EYE_START)%EYE_PATCH
        cx=(-.034,.034)[n]
        if local<392:
            layer=local//56
            t=(0.0,.10,.23,.42,.66,.76,.77)[layer]
        else:t=.78
        p.z=1.433+(p.z-1.433)*(1-.24*t)
        p.y+=.00085*t*gaussian(x,cx,.026)
        counts["eye_contour"]+=1
        continue
    # Nose only: soften tip-to-bridge kink, preserve nose size and identity.
    front=smooth((-y-.027)/.045)
    delta=.00048*front*gaussian(x,0.0,.012)*gaussian(z,1.385,.011)
    if delta>1e-7:
        p.y+=delta;counts["nose_transition"]+=1
    # Auricle geometry: restore the original unmodified side-head envelope
    # in the region previously given a concentric ear, then add asymmetrical
    # superior helix, antihelix, concha, tragus and lobe as contiguous relief.
    b=base_coords[v.index]
    by,bz=b.y,b.z
    yy=(by-.014)/.025
    zz=(bz-1.414)/.031
    r=math.sqrt(yy*yy+zz*zz)
    # fully removes old ring within auricle; blends to existing head outside.
    side=smooth((abs(b.x)-.057)/.020)
    falloff=smooth((1.47-r)/.26)
    w=side*falloff
    if w<.002:continue
    # Helix upper/posterior dominance; weakened anterior/lower sector.
    rz=zz+.11*yy
    ry=yy-.08*zz
    elliptical_r=math.sqrt((ry/.92)**2+(rz/1.03)**2)
    helix=(.0051*gaussian(elliptical_r,.83,.15)
           *(.55+.45*smooth((zz+.28)/.62))
           *(.62+.38*smooth((yy+.5)/.8)))
    body=.0066*gaussian(elliptical_r,0.0,.80)
    antihelix=(.0031*gaussian(yy,.19+.16*zz,.21)
               *gaussian(zz,.08,.69))
    superior_crus=(.0024*gaussian(yy,-.04+.43*(zz-.35),.19)
                   *gaussian(zz,.55,.29))
    inferior_crus=(.0017*gaussian(yy,.17-.38*(zz-.12),.18)
                   *gaussian(zz,.31,.25))
    concha=(-.0045*gaussian(yy,-.11,.35)*gaussian(zz,-.16,.36))
    tragus=(.0025*gaussian(yy,-.65,.18)*gaussian(zz,-.39,.19))
    lobe=(.0034*gaussian(yy,.02,.32)*gaussian(zz,-.86,.21))
    protrusion=body+helix+antihelix+superior_crus+inferior_crus+concha+tragus+lobe
    side_sign=1 if b.x>=0 else -1
    target_x=b.x+side_sign*side*falloff*protrusion
    target_y=b.y+side*falloff*(.0011*gaussian(zz,.61,.34)-.0007*gaussian(zz,-.4,.33))
    target_z=b.z+side*falloff*(.0022*gaussian(zz,.72,.31)*gaussian(yy,.15,.68)
                              -.0012*gaussian(zz,-.82,.24))
    p.x=(1-w)*p.x+w*target_x
    p.y=(1-w)*p.y+w*target_y
    p.z=(1-w)*p.z+w*target_z
    counts["ear_reset_and_sculpt"]+=1
head.data.update()
moved=max((v.co-old).length for v,old in zip(head.data.vertices,before))
if moved>.030:raise RuntimeError("Unexpected large displacement: "+str(moved))
if counts["ear_reset_and_sculpt"]<100 or counts["eye_contour"]!=786 or counts["nose_transition"]<30:
    raise RuntimeError("Insufficient change coverage: "+repr(counts))
if any(not all(math.isfinite(float(q)) for q in v.co) for v in head.data.vertices):
    raise RuntimeError("Nonfinite geometry")
if any(o.name.startswith(("Eyeball_","Iris_","Pupil_")) for o in bpy.data.objects):
    raise RuntimeError("An eye object was unexpectedly created")
head["facial_shape_version"]="0.0.8"
head["eye_policy"]="stone eyelid contour only; NO globe, iris or pupil"
head["ear_construction"]="reconstructed from registered v0.0.4 continuous mesh"
scene=bpy.context.scene
scene["build_version"]="pawn-head-shapes-v0.0.8"
scene["approval"]="technical checkpoint; visual likeness unapproved"
scene.render.engine="CYCLES"
scene.cycles.samples=48
scene.render.resolution_x=900;scene.render.resolution_y=900
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
for name,(loc,target,scale) in views.items():
    cam=bpy.data.objects.get("Camera_"+name)
    if cam is None:
        bpy.ops.object.camera_add(location=loc)
        cam=bpy.context.object;cam.name="Camera_"+name
    cam.location=loc
    cam.rotation_euler=(Vector(target)-cam.location).to_track_quat("-Z","Y").to_euler()
    cam.data.type="ORTHO";cam.data.ortho_scale=scale
scene.camera=bpy.data.objects["Camera_front"]
dst=out/"pawn-head-shapes-v0.0.8.blend"
bpy.ops.wm.save_as_mainfile(filepath=str(dst))
for view in views:
    scene.camera=bpy.data.objects["Camera_"+view]
    scene.render.filepath=str(out/("pawn-head-shapes-v0.0.8-"+view+".png"))
    bpy.ops.render.render(write_still=True)
report={"version":"0.0.8","source":src.name,"baseline":base_file.name,"blend":dst.name,
        "modified_vertices":counts,"max_displacement_m":round(moved,7),
        "eye_objects":[],"eye_policy":"stone outline only, no eyeballs",
        "head_vertices":len(head.data.vertices),
        "views":list(views),"approved":False}
(out/"report.json").write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding="utf-8")
print("CHERPG_V0008_SUCCESS",json.dumps(report))
