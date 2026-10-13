"""CheRPG 0.0.3v primitive-only waist direction mechanism.
Run via CheRPG Blender Tool (Blender 5.2.2+):
  blender --background --python pawn_direction_device_0_0_3v.py -- OUTPUT_DIR
Character is NOT modified. Only the rule-based heading marker rotates.
"""
import bpy
import json
import math
import sys
from pathlib import Path
from mathutils import Vector

sys.path.insert(0,str(Path(__file__).resolve().parent))
from direction_contact_solver import PRESETS,solve,FOOT_THICKNESS,SPLIT_Z
from merge_device_actions import merge_actions
terrain_preset="micro_terrain"
contact=solve(PRESETS[terrain_preset])
if not contact["safe"]:
    raise RuntimeError("Grounding failed: anchor stroke/collision limit exceeded")
if solve(PRESETS["too_steep_30deg"])["safe"]:
    raise AssertionError("Steep terrain must be rejected")

VER="0.0.3v"
Z=.748
R_OPEN=.68
R_CLOSED=.232
FRAMES=(1,30,50,80,100)
argv=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
if len(argv)!=1: raise RuntimeError("Expected a single output-directory argument after --")
output=Path(argv[0]).resolve()
output.mkdir(parents=True,exist_ok=True)
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)
scene=bpy.context.scene
scene.unit_settings.system="METRIC"
scene.unit_settings.scale_length=1.
scene.frame_start,scene.frame_end=1,100
scene.render.resolution_x=960
scene.render.resolution_y=960
scene.render.resolution_percentage=100
scene.render.image_settings.file_format="PNG"

def material(name,rgb,metal=0):
    m=bpy.data.materials.new(name)
    m.diffuse_color=(*rgb,1)
    m.use_nodes=True
    bsdf=m.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value=(*rgb,1)
        bsdf.inputs["Metallic"].default_value=metal
        bsdf.inputs["Roughness"].default_value=.75
    return m

dark=material("DEVICE_DarkIron",(.21,.28,.33),.6)
steel=material("DEVICE_SlideSteel",(.44,.50,.52),.45)
joint=material("DEVICE_Joints",(.29,.35,.39),.55)
blue=material("DEVICE_Heading",(.11,.53,.62),.2)
stone=material("PREVIEW_Stone",(.68,.66,.61))
device=bpy.data.collections.new("DEVICE_PAWN_DIRECTION_RING")
scene.collection.children.link(device)
dummy=bpy.data.collections.new("PREVIEW_ONLY_NOT_EXPORTED")
scene.collection.children.link(dummy)

def place(obj,target,mat):
    for c in list(obj.users_collection): c.objects.unlink(obj)
    target.objects.link(obj)
    obj.data.materials.append(mat)
    return obj

def cube(name,at,dim,mat,target=device):
    bpy.ops.mesh.primitive_cube_add(size=1,location=at)
    o=bpy.context.object
    o.name=name
    o.dimensions=dim
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    return place(o,target,mat)

def cylinder(name,at,r,depth,mat,vertices=10):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices,radius=r,depth=depth,location=at)
    o=bpy.context.object
    o.name=name
    return place(o,device,mat)

def torus(name,r,wire,mat,xs=1,ys=1):
    bpy.ops.mesh.primitive_torus_add(major_segments=24,minor_segments=6,
        major_radius=r,minor_radius=wire,location=(0,0,Z))
    o=bpy.context.object
    o.name=name
    o.scale=(xs,ys,1)
    return place(o,device,mat)

def animate(obj,f,at=None,scale=None,rotation=None):
    if at is not None:
        obj.location=at
        obj.keyframe_insert(data_path="location",frame=f)
    if scale is not None:
        obj.scale=scale
        obj.keyframe_insert(data_path="scale",frame=f)
    if rotation is not None:
        obj.rotation_euler=rotation
        obj.keyframe_insert(data_path="rotation_euler",frame=f)

# Belt stays fixed. The actor itself never turns in this model.
torus("DEVICE_00_WaistMount",.206,.025,dark,1.18,.86)
cube("DEVICE_01_FrontLatch",(0,-.195,Z),(.087,.036,.055),joint)
outer=torus("DEVICE_02_ExpandableRing",R_OPEN,.024,dark)
for f in FRAMES:
    ratio=(R_CLOSED/R_OPEN) if f==1 else 1.
    animate(outer,f,scale=(ratio*(1.12 if f==1 else 1),
                             ratio*(.87 if f==1 else 1),1))

for i,angle in enumerate((45,135,225,315),1):
    a=math.radians(angle)
    u=(math.cos(a),math.sin(a))
    spoke=cube("ACTUATOR_%02d_SlidingRail"%i,(0,0,Z),(.455,.046,.046),steel)
    spoke.rotation_euler.z=a
    hinge=cylinder("ACTUATOR_%02d_RingJoint"%i,(0,0,Z),.042,.06,joint)
    high=cylinder("ANCHOR_%02d_Upper"%i,(0,0,Z),.025,1,steel,8)
    collar=cylinder("ANCHOR_%02d_Collar"%i,(0,0,Z),.037,.069,joint)
    low=cylinder("ANCHOR_%02d_Lower"%i,(0,0,Z),.018,1,steel,8)
    foot=cylinder("ANCHOR_%02d_GroundFoot"%i,(0,0,Z),.075,.052,joint)
    foot_target=contact["feet"][i-1]
    for f in FRAMES:
        opened=f>=30
        down=f>=50
        radius=.68 if opened else .225
        mid=.45 if opened else .213
        length=.455 if opened else .045
        x,y=radius*u[0],radius*u[1]
        animate(spoke,f,at=(mid*u[0],mid*u[1],Z),scale=(length/.455,1,1))
        animate(hinge,f,at=(x,y,Z))
        # Upper tube ends at a fixed collar; lower tube telescopes independently.
        top_end=Z-.012
        upper_mid=(top_end+SPLIT_Z)/2
        animate(high,f,at=(x,y,upper_mid if down else Z-.02),
                scale=(1,1,(top_end-SPLIT_Z) if down else .045))
        animate(collar,f,at=(x,y,SPLIT_Z if down else Z-.055),
                scale=(1,1,1 if down else .35))
        shoe_top=foot_target["upper"]
        low_mid=((x+shoe_top[0])/2,(y+shoe_top[1])/2,
                 (SPLIT_Z+shoe_top[2])/2)
        animate(low,f,at=low_mid if down else (x,y,Z-.07),
                scale=(1,1,(SPLIT_Z-shoe_top[2]) if down else .045))
        if down:
            n=Vector(foot_target["normal"])
            center=Vector(foot_target["base"])+n*(FOOT_THICKNESS/2)
            tilt=n.to_track_quat("Z","Y").to_euler()
            foot.rotation_euler=tilt
            foot.keyframe_insert(data_path="rotation_euler",frame=f)
            animate(foot,f,at=tuple(center),scale=(1,1,1))
        else:
            foot.rotation_euler=(0,0,0)
            foot.keyframe_insert(data_path="rotation_euler",frame=f)
            animate(foot,f,at=(x,y,Z-.1),scale=(1,1,.05))

# Only this visual reference direction rotates, not the Pawn.
bpy.ops.object.empty_add(type="PLAIN_AXES",location=(0,0,Z))
marker=bpy.context.object
marker.name="DEVICE_CTRL_HeadingOnly"
for c in list(marker.users_collection): c.objects.unlink(marker)
device.objects.link(marker)
shaft=cube("DIRECTION_00_Shaft",(.51,0,Z+.052),(.12,.034,.030),blue)
bpy.ops.mesh.primitive_cone_add(vertices=8,radius1=.048,radius2=0,
    depth=.085,location=(.607,0,Z+.052))
tip=bpy.context.object
tip.name="DIRECTION_01_Arrowhead"
tip.rotation_euler.y=math.pi/2
place(tip,device,blue)
for obj in (shaft,tip):
    obj.parent=marker
    obj.location.z-=Z
for f in FRAMES:
    ratio=R_CLOSED/R_OPEN if f==1 else 1
    heading=0 if f>=80 else -math.pi/2
    animate(marker,f,scale=(ratio,ratio,1),rotation=(0,0,heading))

scene["version"]=VER
scene["behavior"]="Changes only pawn heading, not body orientation"
scene["ring_radius_deployed_m"]=R_OPEN
scene["terrain_preset"]=terrain_preset
scene["anchor_contact_success"]=contact["safe"]
scene["ring_radius_stowed_m"]=R_CLOSED
scene["waist_height_m"]=Z
scene["tile_size_m"]=2
objs=list(device.objects)
meshes=[o for o in objs if o.type=="MESH"]
if len(meshes)!=29:
    raise RuntimeError("Unexpected device mesh count: %s"%len(meshes))
# Plain preview blocks are NOT exported.
cube("PREVIEW_Torso",(0,0,.903),(.462,.282,.349),stone,dummy)
cube("PREVIEW_Pelvis",(0,0,.675),(.395,.258,.19),stone,dummy)
cube("PREVIEW_Head",(0,0,1.30),(.29,.27,.33),stone,dummy)
for label,sgn in (("L",-1),("R",1)):
    cube("PREVIEW_Leg_"+label,(sgn*.12,0,.35),(.17,.19,.67),stone,dummy)
    cube("PREVIEW_Arm_"+label,(sgn*.36,0,.82),(.13,.16,.40),stone,dummy)

def select_device():
    bpy.ops.object.select_all(action="DESELECT")
    for obj in objs: obj.select_set(True)
    bpy.context.view_layer.objects.active=meshes[0]

scene.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=str(output/"pawn-direction-device-0.0.3v.blend"))
select_device()
bpy.ops.export_scene.gltf(filepath=str(output/"pawn-direction-device-animated-0.0.3v.glb"),
    export_format="GLB",use_selection=True,export_animations=True,export_extras=True)
merged_clip_report=merge_actions(
    output/"pawn-direction-device-animated-0.0.3v.glb",
    output/"pawn-direction-device-unified-animation-0.0.3v.glb")
print("CHERPG_GLTF_UNIFIED_CLIP_READY",json.dumps(merged_clip_report))
states=(("stowed",1),("deployed_front",50),("deployed_east",80))
for label,f in states:
    scene.frame_set(f)
    select_device()
    bpy.ops.export_scene.gltf(filepath=str(output/("direction-device-only-%s-0.0.3v.glb"%label)),
        export_format="GLB",use_selection=True,export_animations=False,export_extras=True)

scene.render.engine="BLENDER_WORKBENCH"
scene.display.shading.light="STUDIO"
scene.display.shading.color_type="MATERIAL"
scene.display.shading.show_shadows=True
scene.display.shading.show_cavity=True
bpy.ops.object.camera_add(location=(2.6,-3.7,2.15))
cam=bpy.context.object
cam.data.type="ORTHO"
cam.data.ortho_scale=2.55
cam.rotation_euler=(Vector((0,0,.77))-cam.location).to_track_quat("-Z","Y").to_euler()
scene.camera=cam
for label,f in states:
    scene.frame_set(f)
    scene.render.filepath=str(output/("pawn-direction-device-%s-0.0.3v.png"%label))
    bpy.ops.render.render(write_still=True)

report={"status":"generated_not_art_approved","version":VER,
    "mesh_count":len(meshes),"tile_size_m":2,"pawn_height_m":1.55,
    "ring_diameter_closed_m":2*R_CLOSED,"ring_diameter_deployed_m":2*R_OPEN,
    "anchor_count":4,"body_rotates":False,
    "frames":{"closed":1,"expanded":30,"grounded":50,"heading_east":80},
    "character_geometry_exported":False}
(output/"pawn-direction-device-report-0.0.3v.json").write_text(
    json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
print("CHERPG_DIRECTION_DEVICE_READY",json.dumps(report))


# The contact report remains separately testable from rendered geometry.
report_grounding={
    "version":"0.0.3v",
    "terrain":terrain_preset,
    "pawn_body_rotates":False,
    "all_anchors_supported":contact["safe"],
    "steep_terrain_rejected":not solve(PRESETS["too_steep_30deg"])["safe"],
    "foot_contacts":contact["feet"],
}
(output/"direction-grounding-0.0.3v.json").write_text(
    json.dumps(report_grounding,ensure_ascii=False,indent=2),encoding="utf-8")
print("CHERPG_GROUND_CONTACT_CHECK_OK",report_grounding["all_anchors_supported"])
