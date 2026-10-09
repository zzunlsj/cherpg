"""CheRPG Pawn head v0.0.5 — sculpt EARS, NOSE and EYE SHAPES only.
NO eyeballs, irises, pupils or floating ocular objects.
Input is real Blender v0.0.4 retopology checkpoint.
Camera and material review rendered by Blender, NOT generated images.
"""
import bpy,math,sys,json
from pathlib import Path
from mathutils import Vector
argv=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
if len(argv)!=2:raise RuntimeError("Usage: -- v0.0.4.blend output_directory")
src,out=Path(argv[0]).resolve(),Path(argv[1]).resolve()
if not src.is_file():raise RuntimeError("Missing checkpoint: "+str(src))
out.mkdir(parents=True,exist_ok=True)
if Path(bpy.data.filepath).resolve()!=src:
    bpy.ops.wm.open_mainfile(filepath=str(src))
head=bpy.data.objects.get("Pawn_Head_FaceBlockout")
if head is None or head.type!="MESH" or head.get("loop_retopology_version")!="0.0.4":
    raise RuntimeError("Expected v0.0.4 real head mesh")
if head.get("facial_shape_version"):raise RuntimeError("Pass already applied")
removed=[]
for name in ("Eyeball_L","Eyeball_R","Iris_L","Iris_R","Pupil_L","Pupil_R"):
    obj=bpy.data.objects.get(name)
    if obj is None:raise RuntimeError("Expected eye object not found: "+name)
    bpy.data.objects.remove(obj,do_unlink=True)
    removed.append(name)
# Precisely index v0.0.4's registered quad-ring topology:
# 11,392 original vertices; 523 removed inner UV vertices => 10,869 kept.
# Eye patches: 7 rings x 56 vertices + one center; mouth: 7x60+center.
EYE_OFFSET=10869
EYE_RING_VERTS=56
EYE_RING_COUNT=7
EYE_PATCH_VERTS=EYE_RING_COUNT*EYE_RING_VERTS+1
if len(head.data.vertices)!=12076:raise RuntimeError("Unexpected retopo count")
eye_vertex_sets=[]
for n in range(2):
    start=EYE_OFFSET+n*EYE_PATCH_VERTS
    eye_vertex_sets.append(set(range(start,start+EYE_PATCH_VERTS)))
eye_ids=set.union(*eye_vertex_sets)
def g(v,c,s):return math.exp(-((v-c)/s)**2)
def smooth(v):
    v=max(0.0,min(1.0,v))
    return v*v*(3-2*v)
def face_front_y(x,z):
    # Continuous positive-z upper half and sculpted lower head envelope.
    zz=(z-1.422)/.126
    jaw=max(0.,(-zz-.12)/.85)
    width=.093*(.91+.11*g(zz,.42,.55)+.06*g(zz,-.12,.32)-.24*jaw**1.2)
    depth=.089*(1-.07*jaw)
    return -depth*math.sqrt(max(.035,1-zz*zz-(x/width)**2))
# Preserve all original geometry and track change extent.
original=[v.co.copy() for v in head.data.vertices]
# First smooth carved eye cavities into CLOSED, shallow eyelid-shaped stone.
# No void, no dark sockets, no globe. Original topological eye loops are retained.
for n,cx in enumerate((-.034,.034)):
    start=EYE_OFFSET+n*EYE_PATCH_VERTS
    for layer in range(EYE_RING_COUNT):
        for j in range(EYE_RING_VERTS):
            idx=start+layer*EYE_RING_VERTS+j
            p=head.data.vertices[idx].co
            x,z=p.x,p.z
            # Shallower eyelid structure with an elegant almond seam;
            # the center remains stone, not an eye opening.
            # Layer 0 transitions to surrounding cheek & brow; 4/5 = eyelid rim.
            profile=(0.0,.00015,.00025,.00055,-.00025,.00035,.00075)[layer]
            base=face_front_y(x,z)
            upper= -.00095*g(z,1.439,.0036)*g(x,cx,.021)
            p.y=base+profile+upper
            if layer>=4:
                # Reduce vertical aperture: eyes should be sculpt outlines only.
                p.z=1.433+(p.z-1.433)*(.90 if layer==4 else .76)
    p=head.data.vertices[start+EYE_RING_VERTS*EYE_RING_COUNT].co
    p.y=face_front_y(p.x,p.z)+.0008
# Only replace the old dark socket material ON EYE POLYGONS.
# Leave the mouth and its original topology/material unchanged.
eye_face_changes=0
for face in head.data.polygons:
    if face.material_index!=1:continue
    if all(any(v in s for s in eye_vertex_sets) for v in face.vertices):
        face.material_index=0
        eye_face_changes+=1
# In addition, blend anterior cheek/brow near existing eye border.
for v in head.data.vertices:
    if v.index in eye_ids:continue
    p=v.co
    x,y,z=p.x,p.y,p.z
    front=smooth((-y-.02)/.045)
    around=0
    for ex in (-.034,.034):
        dist=math.sqrt(((x-ex)/.021)**2+((z-1.433)/.009)**2)
        around=max(around,g(dist,1.45,.60))
    if front>0 and around>0.01:
        desired=face_front_y(x,z)
        p.y+=.48*front*around*(desired-p.y)
# Next carve the nose IN the head mesh; it must read as a shallow sculpted
# bridge + small tip, not as a separate wedge primitive.
nose_count=0
ear_count=0
for v in head.data.vertices:
    if v.index in eye_ids:continue
    p=v.co
    x,y,z=p.x,p.y,p.z
    # Front only for nose: continuous bridge / rounded tip / subtle alar forms.
    front=smooth((-y-.018)/.054)
    bridge=g(x,0,.0118)*g(z,1.416,.025)
    tip=g(x,0,.0120)*g(z,1.383,.010)
    alae=(g(x,-.011,.007)+g(x,.011,.007))*g(z,1.381,.009)
    # Extremely restrained nose, avoid adult-size forward beak.
    delta=front*(.0029*bridge+.0068*tip+.0019*alae)
    if delta>0.00001:
        p.y-=delta
        nose_count+=1
    # Ears: integral auricle relief from same head topology; no ear primitives.
    # Ear is behind the cheek in Y and beside eye-to-nose height in Z.
    side=smooth((abs(x)-.061)/.025)
    cy=.014
    cz=1.414
    dy=(y-cy)/.025
    dz=(z-cz)/.031
    r=math.sqrt(dy*dy+dz*dz)
    body=.0112*g(r,0,.83)
    helix=.0054*g(r,.84,.19)
    concha=-.0050*g(r,.42,.26)
    lobe=.0032*g(y,cy,.015)*g(z,1.389,.011)
    # Ear entrance should taper against temple and jaw.
    ear_offset=side*(body+helix+concha+lobe)
    if abs(ear_offset)>0.000015:
        p.x+=(-1 if x<0 else 1)*ear_offset
        ear_count+=1
head.data.update()
moved=max((v.co-o).length for v,o in zip(head.data.vertices,original))
if moved>.021:raise RuntimeError("Unsafe maximum vertex displacement: "+str(moved))
if ear_count<100 or nose_count<40 or eye_face_changes<40:
    raise RuntimeError("Geometry coverage insufficient: "+str((ear_count,nose_count,eye_face_changes)))
if any(not all(math.isfinite(q) for q in v.co) for v in head.data.vertices):
    raise RuntimeError("Non-finite mesh vertex")
# Existing modifier relaxes coarse eyebrow/mouth transitions; maintain it.
head["facial_shape_version"]="0.0.5"
head["eye_policy"]="shape only: NO eye globes/iris/pupil"
head["ear_construction"]="continuously sculpted from original side head mesh"
head["nose_construction"]="continuously sculpted from head mesh"
scene=bpy.context.scene
scene["build_version"]="Pawn-head-ear-nose-eye-shapes-v0.0.5"
scene["approval"]="pending visual comparison to approved original artwork"
scene.render.engine="CYCLES"
scene.cycles.samples=40
scene.render.resolution_x=900
scene.render.resolution_y=900
scene.render.resolution_percentage=100
scene.render.image_settings.file_format="PNG"
scene.view_settings.view_transform="Standard"
for obj in bpy.data.objects:
    if obj.type=="LIGHT":
        obj.data.energy=130 if "key" in obj.name.lower() else 68
def look(o,target):
    o.rotation_euler=(Vector(target)-o.location).to_track_quat("-Z","Y").to_euler()
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
    cam.location=loc;look(cam,target)
    cam.data.type="ORTHO";cam.data.ortho_scale=scale
scene.camera=bpy.data.objects["Camera_front"]
model=out/"pawn-head-shapes-v0.0.5.blend"
bpy.ops.wm.save_as_mainfile(filepath=str(model))
for name in views:
    scene.camera=bpy.data.objects["Camera_"+name]
    scene.render.filepath=str(out/("pawn-head-shapes-v0.0.5-"+name+".png"))
    bpy.ops.render.render(write_still=True)
remaining=[o.name for o in bpy.data.objects if o.name.startswith(("Eyeball_","Iris_","Pupil_"))]
if remaining:raise RuntimeError("Eye objects survived: "+str(remaining))
report={"version":"0.0.5","source":src.name,"blend":model.name,
"removed_eye_objects":removed,"remaining_eye_objects":remaining,
"eyelid_patches_retargeted":2,"eye_faces_recolored_to_stone":eye_face_changes,
"nose_modified_vertices":nose_count,"ear_modified_vertices":ear_count,
"head_vertices":len(head.data.vertices),
"max_vertex_movement_m":round(moved,6),
"single_continuous_head_for_eye_nose_ear_forms":True,"views":list(views),
"note":"No actual eyeballs. Existing mouth intentionally untouched (aside from modifier). Quality pending comparison."}
(out/"report.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
print("CHERPG_V0005_SUCCESS",json.dumps(report))
