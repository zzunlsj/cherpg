"""CheRPG Pawn: v0.0.3 sculpt the face IN the existing continuous head surface.
Input: actual v0.0.2 .blend; never reuse archived v0.5.x meshes.
Front = -Y, up = +Z. Dimensions in meters.
This is a facial *landmark sculpt*, not yet production eye/mouth retopology.
"""
import bpy,math,sys,json
from pathlib import Path
from mathutils import Vector

args=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
if len(args)!=2: raise RuntimeError("Usage: -- input-v0.0.2.blend output-dir")
source=Path(args[0]).resolve();out=Path(args[1]).resolve()
if not source.is_file(): raise RuntimeError("Missing input: "+str(source))
out.mkdir(parents=True,exist_ok=True)
if Path(bpy.data.filepath).resolve()!=source:
    bpy.ops.wm.open_mainfile(filepath=str(source))
head=bpy.data.objects.get("Pawn_Head_FaceBlockout")
if head is None or head.type!="MESH" or head.get("upper_refinement_version")!="0.0.2":
    raise RuntimeError("Requires continuous-face head from v0.0.2")
if head.get("facial_landmarks_version"): raise RuntimeError("Already sculpted")
if len(head.data.vertices)!=11392: raise RuntimeError("Unexpected head topology")
def g(v,center,sigma):
    return math.exp(-((v-center)/sigma)**2)
def clamp01(x): return max(0.,min(1.,x))
def smoothstep(x):
    t=clamp01(x)
    return t*t*(3-2*t)
before=[v.co.copy() for v in head.data.vertices]
deltas={"eye_sockets":0.0,"eyelid_relief":0.0,"nose":0.0,"mouth":0.0}
for v in head.data.vertices:
    p=v.co.copy()
    x,y,z=p.x,p.y,p.z-1.422
    ax=abs(x)
    front=smoothstep((-y/0.09-0.22)/0.54)
    # Spatially limited front facial relief: all elements are continuous quads.
    outer=max(g(x,-0.034,0.022),g(x,0.034,0.022))
    e_z=g(z,0.011,0.016)
    # Orbital sockets recess behind the eyelid rims.
    socket=0.0095*outer*e_z
    # Per-eye elliptical rim: subtle upper/lower lid volume, never a pasted-on primitive.
    eyelids=0.0
    upper_crease=0.0
    for cx in (-0.034,0.034):
        radius=math.sqrt(((x-cx)/0.0215)**2+((z-0.011)/0.0105)**2)
        eyelids+=0.0042*g(radius,1.0,0.26)
        upper_crease+=0.0016*g(x,cx,0.025)*g(z,0.028,0.005)
    # Smooth brow-to-temple anatomical transition.
    eyebrow=0.0024*outer*g(z,0.031,0.012)
    cheek=0.0042*max(g(x,-0.052,0.028),g(x,0.052,0.028))*g(z,-0.019,0.027)
    # Nose projects from face as one surface: bridge, tip and alae.
    bridge=0.0033*g(x,0,0.014)*g(z,-0.010,0.035)
    tip=0.0085*g(x,0,0.0125)*g(z,-0.036,0.013)
    alae=0.0023*(g(x,-0.011,0.006)+g(x,0.011,0.006))*g(z,-0.044,0.006)
    # The mouth is merely a sculpted seam with a natural subtle upper/lower lip.
    curve=-0.063+0.0024*smoothstep(ax/0.029)
    mouth_extent=g(x,0,0.025)
    mouth_groove=0.0023*mouth_extent*g(z,curve,0.0028)
    upper_lip=0.0014*g(x,0,0.020)*g(z,-0.056,0.005)
    lower_lip=0.0011*g(x,0,0.021)*g(z,-0.071,0.006)
    chin=0.0024*g(x,0,0.025)*g(z,-0.087,0.021)
    # Recesses are +Y; protrusions are -Y.
    p.y+=front*(socket-eyelids+upper_crease-eyebrow-cheek-bridge-tip-alae+mouth_groove-upper_lip-lower_lip-chin)
    # Control overly pointy original chin without upsetting head circumference.
    p.x*=1.0+0.14*g(z,-0.104,0.018)
    v.co=p
head.data.update()
# Preserve side silhouette, disallow any extreme displacement.
motions=[(v.co-old).length for v,old in zip(head.data.vertices,before)]
max_move=max(motions)
changed=sum(d>1e-5 for d in motions)
if max_move>0.022: raise RuntimeError("Excessive vertex shift: "+str(max_move))
if changed<250: raise RuntimeError("No meaningful facial geometry change")
if any(not math.isfinite(v.co.x+v.co.y+v.co.z) for v in head.data.vertices):
    raise RuntimeError("Non-finite geometry")
head["facial_landmarks_version"]="0.0.3"
head["face_workflow"]="base silhouette -> sculpted sockets/nose/mouth landmarks -> future retopo"
# Contrast-rich clay, no highlights concealing surface.
mat=head.active_material
if mat:
    mat.diffuse_color=(0.48,0.45,0.40,1)
    if mat.use_nodes:
        n=mat.node_tree.nodes.get("Principled BSDF")
        if n:
            n.inputs["Base Color"].default_value=(0.48,0.45,0.40,1)
            n.inputs["Roughness"].default_value=0.94
scene=bpy.context.scene
for ob in bpy.data.objects:
    if ob.type=="LIGHT":
        ob.data.energy=105 if "key" in ob.name.lower() else 46
scene.render.engine="CYCLES";scene.cycles.samples=48
scene.render.resolution_x=900;scene.render.resolution_y=900;scene.render.resolution_percentage=100
scene.render.image_settings.file_format="PNG"
scene.view_settings.view_transform="Standard"
# Directly compare to previously generated views; introduce close facial crop.
def aim(ob,target):
    ob.rotation_euler=(Vector(target)-ob.location).to_track_quat("-Z","Y").to_euler()
views={
 "front":((0,-2.0,1.44),(0,0,1.422),0.33),
 "profile":((2.,0,1.44),(0,0,1.422),0.33),
 "threequarter":((1.2,-1.8,1.46),(0,0,1.422),0.33),
 "face-detail":((0.43,-1.7,1.47),(0,0,1.410),0.205)}
for name,(position,target,scale) in views.items():
    cam=bpy.data.objects.get("Camera_"+name)
    if cam is None:
        bpy.ops.object.camera_add(location=position)
        cam=bpy.context.object
        cam.name="Camera_"+name
    cam.location=position;aim(cam,target)
    cam.data.type="ORTHO";cam.data.ortho_scale=scale
scene["build_version"]="face-landmarks-v0.0.3"
scene["status"]="sculpted landmarks; production facial edge loops not yet built"
scene.camera=bpy.data.objects["Camera_front"]
blend=out/"pawn-face-landmarks-v0.0.3.blend"
bpy.ops.wm.save_as_mainfile(filepath=str(blend))
for view in views:
    scene.camera=bpy.data.objects["Camera_"+view]
    scene.render.filepath=str(out/("pawn-face-landmarks-v0.0.3-"+view+".png"))
    bpy.ops.render.render(write_still=True)
report={
 "version":"0.0.3","mesh_name":head.name,"vertices":len(head.data.vertices),
 "changed_vertices":changed,"max_displacement_m":round(max_move,7),
 "actual_mesh_sculpt":True,"separate_eyes":False,"separate_mouth":False,
 "changes":["eye socket recesses","integrated eyelid rims and brow","bridge/tip/alar nose relief","small lip seam and chin softening"],
 "renders":list(views),"blend":blend.name,
 "limitations":["no ocular openings/animated eyelids yet","parametric existing UV quad mesh needs eye/mouth loop retopology","concept image alignment still pending"],
}
(out/"report.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
print("CHERPG_V0003_SUCCESS",json.dumps(report))
