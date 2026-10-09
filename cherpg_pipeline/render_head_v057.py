import bpy, sys, math
from pathlib import Path
from mathutils import Vector

VIEWS=[
("front",(0.0,1.72,1.47)),
("threequarter",(0.72,1.52,1.50)),
("side",(1.72,0.0,1.47)),
]

def look_at(o,t):
    o.rotation_euler=(Vector(t)-o.location).to_track_quat("-Z","Y").to_euler()

a=sys.argv[sys.argv.index("--")+1:]
blend=Path(a[0]).resolve(); outdir=Path(a[1]).resolve()
outdir.mkdir(parents=True,exist_ok=True)
if Path(bpy.data.filepath).resolve()!=blend:
    bpy.ops.wm.open_mainfile(filepath=str(blend))
s=bpy.context.scene; s.frame_set(1)

for o in list(s.objects):
    if o.type in {"CAMERA","LIGHT"}: bpy.data.objects.remove(o,do_unlink=True)

cd=bpy.data.cameras.new("HeadReviewCam")
cam=bpy.data.objects.new("HeadReviewCam",cd); s.collection.objects.link(cam)
cam.data.lens=92; s.camera=cam

def light(name,loc,e,size,color):
    d=bpy.data.lights.new(name=name,type="AREA"); d.energy=e; d.size=size; d.color=color
    o=bpy.data.objects.new(name,d); s.collection.objects.link(o); o.location=loc; look_at(o,(0,0.04,1.44))

light("Key",(-0.85,1.25,2.15),820,1.0,(1.0,0.84,0.72))
light("Fill",(0.95,0.75,1.75),440,1.15,(0.72,0.82,1.0))
light("Rim",(0,-0.95,2.0),680,0.85,(0.72,0.82,1.0))

w=s.world or bpy.data.worlds.new("World"); s.world=w; w.use_nodes=True
bg=w.node_tree.nodes.get("Background"); bg.inputs["Color"].default_value=(0.014,0.017,0.024,1); bg.inputs["Strength"].default_value=0.32

s.render.engine="BLENDER_EEVEE"
s.render.resolution_x=720; s.render.resolution_y=720; s.render.resolution_percentage=100
s.render.image_settings.file_format="PNG"
try: s.view_settings.look="AgX - Medium High Contrast"
except: pass

for name,pos in VIEWS:
    cam.location=pos; look_at(cam,(0,0.04,1.44))
    s.render.filepath=str(outdir/f"cherpg-pawn-v0.5.7-head-{name}.png")
    bpy.ops.render.render(write_still=True)
    print("RENDERED",name)
