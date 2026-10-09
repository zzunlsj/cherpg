import bpy, sys
from pathlib import Path
from mathutils import Vector

def look_at(o,t):
    o.rotation_euler=(Vector(t)-o.location).to_track_quat("-Z","Y").to_euler()

a=sys.argv[sys.argv.index("--")+1:]
blend=Path(a[0]).resolve(); out=Path(a[1]).resolve(); out.parent.mkdir(parents=True,exist_ok=True)
if Path(bpy.data.filepath).resolve()!=blend: bpy.ops.wm.open_mainfile(filepath=str(blend))
s=bpy.context.scene; s.frame_set(1)
for o in list(s.objects):
    if o.type in {"CAMERA","LIGHT"}: bpy.data.objects.remove(o,do_unlink=True)

cd=bpy.data.cameras.new("ArmCam"); cam=bpy.data.objects.new("ArmCam",cd); s.collection.objects.link(cam)
cam.location=(1.05,1.85,1.20); cam.data.lens=78; look_at(cam,(0,0.02,0.98)); s.camera=cam

def light(name,loc,e,size,color):
    d=bpy.data.lights.new(name=name,type="AREA"); d.energy=e; d.size=size; d.color=color
    o=bpy.data.objects.new(name,d); s.collection.objects.link(o); o.location=loc; look_at(o,(0,0.02,1.0))
light("Key",(-1.1,1.6,2.2),900,1.2,(1.0,0.84,0.72))
light("Fill",(1.3,0.8,1.6),460,1.4,(0.72,0.82,1.0))
light("Rim",(0,-1.0,1.8),650,1.0,(0.72,0.82,1.0))
w=s.world or bpy.data.worlds.new("World"); s.world=w; w.use_nodes=True
bg=w.node_tree.nodes.get("Background"); bg.inputs["Color"].default_value=(0.015,0.018,0.025,1); bg.inputs["Strength"].default_value=0.34
s.render.engine="BLENDER_EEVEE"; s.render.resolution_x=720; s.render.resolution_y=720; s.render.resolution_percentage=100
s.render.image_settings.file_format="PNG"; s.render.filepath=str(out)
try: s.view_settings.look="AgX - Medium High Contrast"
except: pass
bpy.ops.render.render(write_still=True)
