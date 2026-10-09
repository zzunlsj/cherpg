import bpy,sys
from pathlib import Path
from mathutils import Vector
V=[("front",(0,1.72,1.47)),("threequarter",(0.72,1.52,1.50)),("side",(1.72,0,1.47))]
def look(o,t):o.rotation_euler=(Vector(t)-o.location).to_track_quat("-Z","Y").to_euler()
a=sys.argv[sys.argv.index("--")+1:];blend=Path(a[0]).resolve();out=Path(a[1]).resolve();out.mkdir(parents=True,exist_ok=True)
if Path(bpy.data.filepath).resolve()!=blend:bpy.ops.wm.open_mainfile(filepath=str(blend))
s=bpy.context.scene;s.frame_set(1)
for o in list(s.objects):
    if o.type in {"CAMERA","LIGHT"}:bpy.data.objects.remove(o,do_unlink=True)
cd=bpy.data.cameras.new("R");cam=bpy.data.objects.new("R",cd);s.collection.objects.link(cam);cam.data.lens=92;s.camera=cam
s.render.engine="BLENDER_WORKBENCH";s.render.resolution_x=560;s.render.resolution_y=560;s.render.resolution_percentage=100;s.render.image_settings.file_format="PNG"
sh=s.display.shading;sh.light="STUDIO";sh.color_type="MATERIAL";sh.show_shadows=True;sh.show_cavity=True;sh.cavity_type="WORLD";sh.curvature_ridge_factor=1.6
for n,p in V:
    cam.location=p;look(cam,(0,0.04,1.45));s.render.filepath=str(out/f"cherpg-pawn-v0.5.10-head-{n}.png");bpy.ops.render.render(write_still=True)
