"""CheRPG Pawn Hero — upper-head anatomy refinement v0.0.2 (Blender).
Changes existing v0.0.1 mesh, never creates pasted-on face features.
The concept art hides the cranium under a pawn cap; inferred anatomy is provisional.
Front=-Y; up=Z; units=m.
"""
import bpy,sys,json,math
from pathlib import Path
from mathutils import Vector
args=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
if len(args)!=2: raise RuntimeError("Usage: -- input-v0.0.1.blend output-dir")
source=Path(args[0]).resolve();out=Path(args[1]).resolve()
if not source.is_file(): raise RuntimeError("Input .blend not found: "+str(source))
out.mkdir(parents=True,exist_ok=True)
if Path(bpy.data.filepath).resolve()!=source:
    bpy.ops.wm.open_mainfile(filepath=str(source))
head=bpy.data.objects.get("Pawn_Head_FaceBlockout")
if head is None or head.type!="MESH" or len(head.data.vertices)<1000:
    raise RuntimeError("Expected v0.0.1 continuous head mesh")
if head.get("upper_refinement_version"):
    raise RuntimeError("Upper head pass already applied; use original v0.0.1 .blend")
def g(x,c,s):return math.exp(-((x-c)/s)**2)
def smoothstep(v):
    q=max(0.,min(1.,v))
    return q*q*(3.-2.*q)
prior=[v.co.copy() for v in head.data.vertices]
for v in head.data.vertices:
    p=v.co.copy()
    x,y,z=p.x,p.y,(p.z-1.422)/0.126
    az=abs(x)
    front=smoothstep((-y/0.092-0.12)/0.63)
    rear=smoothstep((y/0.092-0.10)/0.60)
    side=smoothstep((az-0.025)/0.065)
    # Rounded cranium beneath the pawn hat: broaden upper lateral vault.
    cranial=g(z,0.66,0.32)
    width_gain=1.0+0.079*cranial-0.018*g(z,0.19,0.17)
    p.x=x*width_gain
    # Youthful forehead: flatter center-front plane, rather than bulging egg.
    forehead=g(z,0.48,0.37)
    center=g(x,0.0,0.068)
    p.y=y+0.0062*front*forehead*center
    # A very subtle, connected brow ridge and integrated temple-to-cheek falloff.
    brow=g(z,0.11,0.12)*g(az,0.034,0.030)
    p.y-=0.00165*front*brow
    temple=g(z,0.34,0.22)*side
    p.y+=0.0012*front*temple
    # Back crown needs real volume under the rear hat rim.
    p.y+=0.0044*rear*g(z,0.57,0.35)
    # Avoid tall egg-shaped apex; top flattens slightly beneath pawn finial.
    p.z-=0.0043*g(z,0.98,0.12)
    v.co=p
head.data.update()
move=max((v.co-p).length for v,p in zip(head.data.vertices,prior))
if move>0.012: raise RuntimeError("Unsafe sculpt displacement: "+str(move))
head["upper_refinement_version"]="0.0.2"
head["reference_inference"]="forehead, temples, upper cranial vault obscured by pawn cap"
# Neutral studio clay. The previous v0.0.1 renders were visually blown out.
material=head.active_material
if material:
    material.diffuse_color=(0.40,0.38,0.35,1)
    if material.use_nodes and material.node_tree:
        node=material.node_tree.nodes.get("Principled BSDF")
        if node:
            node.inputs["Base Color"].default_value=(0.40,0.38,0.35,1)
            node.inputs["Roughness"].default_value=0.87
scene=bpy.context.scene
for obj in bpy.data.objects:
    if obj.type=="LIGHT":
        if "key" in obj.name.lower(): obj.data.energy=38
        else: obj.data.energy=24
scene.render.engine="CYCLES"
scene.cycles.samples=36
scene.render.resolution_x=800;scene.render.resolution_y=800;scene.render.resolution_percentage=100
scene.render.image_settings.file_format="PNG"
scene.view_settings.view_transform="Standard"
scene.render.film_transparent=False
def orient(obj,target):obj.rotation_euler=(Vector(target)-obj.location).to_track_quat("-Z","Y").to_euler()
views={"front":((0,-2.0,1.44),(0,0,1.425),0.335),
       "profile":((2.0,0,1.44),(0,0,1.425),0.335),
       "threequarter":((1.4,-1.6,1.47),(0,0,1.425),0.335),
       "forehead-detail":((0.68,-1.2,1.69),(0,0,1.475),0.19)}
for label,(position,target,scale) in views.items():
    name="Camera_"+label
    cam=bpy.data.objects.get(name)
    if cam is None:
        bpy.ops.object.camera_add(location=position);cam=bpy.context.object;cam.name=name
    cam.location=position
    orient(cam,target);cam.data.type="ORTHO";cam.data.ortho_scale=scale
scene["build_version"]="face-upper-refine-v0.0.2"
scene["status"]="provisional cranial anatomy; concept comparison pending"
scene.camera=bpy.data.objects["Camera_threequarter"]
result=out/"pawn-face-upper-v0.0.2.blend"
bpy.ops.wm.save_as_mainfile(filepath=str(result))
for label in views:
    scene.camera=bpy.data.objects["Camera_"+label]
    scene.render.filepath=str(out/("pawn-face-upper-v0.0.2-"+label+".png"))
    bpy.ops.render.render(write_still=True)
report={"version":"0.0.2","status":"upper-skull-pass-awaiting-review",
"source":source.name,"result":result.name,"vertices":len(head.data.vertices),
"max_vertex_shift_m":move,"adjustments":["rounder upper cranium","flatter forehead","temple/brow transition","smoother rear vault","shorter apex"],"views":list(views),
"notes":"Actual Blender mesh edit. No image generation, no eyes/mouth added."}
(out/"report.json").write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding="utf-8")
print("CHERPG_FACE_UPPER_SUCCESS",json.dumps(report))
