import bpy, sys
from pathlib import Path
from mathutils import Vector

def look_at(o,t):
    o.rotation_euler=(Vector(t)-o.location).to_track_quat("-Z","Y").to_euler()

args=sys.argv[sys.argv.index("--")+1:]
blend=Path(args[0]).resolve(); out=Path(args[1]).resolve()
out.parent.mkdir(parents=True,exist_ok=True)
if Path(bpy.data.filepath).resolve()!=blend:
    bpy.ops.wm.open_mainfile(filepath=str(blend))
s=bpy.context.scene; s.frame_set(1)
for o in list(s.objects):
    if o.type in {"CAMERA","LIGHT"} or o.name=="RenderGround":
        bpy.data.objects.remove(o,do_unlink=True)
bpy.ops.mesh.primitive_plane_add(size=8,location=(0,0,0))
g=bpy.context.object; g.name="RenderGround"
m=bpy.data.materials.new("RenderGroundMat"); m.use_nodes=True
b=m.node_tree.nodes.get("Principled BSDF")
b.inputs["Base Color"].default_value=(0.055,0.06,0.07,1); b.inputs["Roughness"].default_value=0.72
g.data.materials.append(m)
cd=bpy.data.cameras.new("RenderCamera"); cam=bpy.data.objects.new("RenderCamera",cd); s.collection.objects.link(cam)
cam.location=(2.45,3.25,1.55); cam.data.lens=62; look_at(cam,(0,0,0.92)); s.camera=cam
def light(name,loc,energy,size,color):
    d=bpy.data.lights.new(name=name,type="AREA"); d.energy=energy; d.shape="DISK"; d.size=size; d.color=color
    o=bpy.data.objects.new(name,d); s.collection.objects.link(o); o.location=loc; look_at(o,(0,0,0.95))
light("Key",(-2.1,2.8,3.0),1150,2.5,(1.0,0.84,0.70))
light("Fill",(2.6,1.3,2.1),650,2.3,(0.72,0.82,1.0))
light("Rim",(0,-2.7,2.7),1050,1.8,(0.72,0.82,1.0))
light("Top",(0,0.2,4.2),450,2.8,(1.0,0.94,0.84))
w=s.world or bpy.data.worlds.new("World"); s.world=w; w.use_nodes=True
bg=w.node_tree.nodes.get("Background"); bg.inputs["Color"].default_value=(0.012,0.014,0.02,1); bg.inputs["Strength"].default_value=0.28
s.render.engine="BLENDER_EEVEE"; s.render.resolution_x=720; s.render.resolution_y=900; s.render.resolution_percentage=100
s.render.image_settings.file_format="PNG"; s.render.image_settings.color_mode="RGBA"; s.render.filepath=str(out)
try: s.view_settings.look="AgX - Medium High Contrast"
except: pass
bpy.ops.render.render(write_still=True)
