import bpy, sys
from pathlib import Path
from mathutils import Vector

VIEWS=[
("front",(0,-4.0,1.35)),
("front_3q",(2.5,-3.35,1.50)),
("right",(4.0,0,1.35)),
("back",(0,4.0,1.35)),
("back_3q",(-2.5,3.35,1.50)),
("left",(-4.0,0,1.35)),
]

def look_at(o,t):
    o.rotation_euler=(Vector(t)-o.location).to_track_quat("-Z","Y").to_euler()

args=sys.argv[sys.argv.index("--")+1:]
blend=Path(args[0]).resolve()
out=Path(args[1]).resolve()
out.mkdir(parents=True,exist_ok=True)
if Path(bpy.data.filepath).resolve()!=blend:
    bpy.ops.wm.open_mainfile(filepath=str(blend))
s=bpy.context.scene
s.frame_set(1)

for o in list(s.objects):
    if o.type in {"CAMERA","LIGHT"} or o.name=="PreviewGround":
        bpy.data.objects.remove(o,do_unlink=True)

bpy.ops.mesh.primitive_plane_add(size=7,location=(0,0,0))
g=bpy.context.object
g.name="PreviewGround"

cd=bpy.data.cameras.new("PreviewCamera")
cam=bpy.data.objects.new("PreviewCamera",cd)
s.collection.objects.link(cam)
cam.data.lens=72
s.camera=cam

s.render.engine="BLENDER_WORKBENCH"
s.render.resolution_x=480
s.render.resolution_y=600
s.render.resolution_percentage=100
s.render.image_settings.file_format="PNG"
s.render.film_transparent=False

sh=s.display.shading
sh.light="STUDIO"
sh.color_type="MATERIAL"
sh.show_shadows=True
sh.show_cavity=True
sh.cavity_type="WORLD"
sh.curvature_ridge_factor=1.5
sh.curvature_valley_factor=1.2
sh.show_specular_highlight=True

for name,pos in VIEWS:
    cam.location=pos
    look_at(cam,(0,0,0.92))
    s.render.filepath=str(out/f"cherpg-pawn-v0.5.4-preview-{name}.png")
    bpy.ops.render.render(write_still=True)
    print("RENDERED",name)
