import bpy,sys
from pathlib import Path
from mathutils import Vector
def look(o,t):o.rotation_euler=(Vector(t)-o.location).to_track_quat("-Z","Y").to_euler()
a=sys.argv[sys.argv.index("--")+1:];blend=Path(a[0]).resolve();out=Path(a[1]).resolve();out.parent.mkdir(parents=True,exist_ok=True)
if Path(bpy.data.filepath).resolve()!=blend:bpy.ops.wm.open_mainfile(filepath=str(blend))
s=bpy.context.scene;s.frame_set(1)
for o in list(s.objects):
    if o.type in {"CAMERA","LIGHT"}:bpy.data.objects.remove(o,do_unlink=True)
cd=bpy.data.cameras.new("PBR");cam=bpy.data.objects.new("PBR",cd);s.collection.objects.link(cam);cam.location=(0.72,1.52,1.50);cam.data.lens=92;look(cam,(0,0.045,1.445));s.camera=cam
def light(n,l,e,size,col):
    d=bpy.data.lights.new(n,"AREA");d.energy=e;d.size=size;d.color=col;o=bpy.data.objects.new(n,d);s.collection.objects.link(o);o.location=l;look(o,(0,0.045,1.445))
light("Key",(-0.75,1.25,2.15),800,1.0,(1,0.84,0.72));light("Fill",(0.9,0.7,1.75),420,1.15,(0.72,0.82,1));light("Rim",(0,-0.9,2.0),650,0.85,(0.72,0.82,1))
w=s.world or bpy.data.worlds.new("World");s.world=w;w.use_nodes=True;bg=w.node_tree.nodes.get("Background");bg.inputs["Color"].default_value=(0.014,0.017,0.024,1);bg.inputs["Strength"].default_value=0.32
s.render.engine="BLENDER_EEVEE";s.render.resolution_x=640;s.render.resolution_y=640;s.render.resolution_percentage=100;s.render.image_settings.file_format="PNG";s.render.filepath=str(out)
try:s.view_settings.look="AgX - Medium High Contrast"
except:pass
bpy.ops.render.render(write_still=True)
