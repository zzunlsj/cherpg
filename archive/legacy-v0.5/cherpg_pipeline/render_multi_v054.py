import bpy
import sys
from pathlib import Path
from mathutils import Vector

VIEWS = [
    ("front",       (0.0, -4.20, 1.36)),
    ("front_3q",    (2.65, -3.55, 1.52)),
    ("right",       (4.20, 0.0, 1.36)),
    ("back",        (0.0, 4.20, 1.36)),
    ("back_3q",     (-2.65, 3.55, 1.52)),
    ("left",        (-4.20, 0.0, 1.36)),
]

def parse_args():
    a=sys.argv
    if "--" not in a:
        raise RuntimeError("Expected input blend and output directory")
    a=a[a.index("--")+1:]
    return Path(a[0]).resolve(), Path(a[1]).resolve()

def look_at(obj, target):
    obj.rotation_euler=(Vector(target)-obj.location).to_track_quat("-Z","Y").to_euler()

def add_area(name, loc, energy, size, color):
    d=bpy.data.lights.new(name=name,type="AREA")
    d.energy=energy
    d.shape="DISK"
    d.size=size
    d.color=color
    o=bpy.data.objects.new(name,d)
    bpy.context.scene.collection.objects.link(o)
    o.location=loc
    look_at(o,(0,0,0.92))
    return o

def setup_scene():
    s=bpy.context.scene
    s.frame_set(1)

    for o in list(s.objects):
        if o.type in {"CAMERA","LIGHT"} or o.name=="RenderGround":
            bpy.data.objects.remove(o,do_unlink=True)

    bpy.ops.mesh.primitive_plane_add(size=8.0,location=(0,0,0))
    g=bpy.context.object
    g.name="RenderGround"
    m=bpy.data.materials.new("RenderGroundMat")
    m.diffuse_color=(0.055,0.06,0.065,1)
    m.use_nodes=True
    bsdf=m.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value=(0.055,0.06,0.065,1)
    bsdf.inputs["Roughness"].default_value=0.78
    g.data.materials.append(m)

    cd=bpy.data.cameras.new("RenderCamera")
    cam=bpy.data.objects.new("RenderCamera",cd)
    s.collection.objects.link(cam)
    cam.data.lens=68
    s.camera=cam

    add_area("Key",(-2.2,-2.6,3.1),1150,2.4,(1.0,0.82,0.66))
    add_area("Fill",(2.4,-1.5,2.0),620,2.2,(0.68,0.80,1.0))
    add_area("Rim",(0.4,2.6,2.6),980,1.7,(0.75,0.84,1.0))
    add_area("Top",(0.0,0.1,4.4),500,2.8,(1.0,0.93,0.82))

    w=s.world or bpy.data.worlds.new("World")
    s.world=w
    w.use_nodes=True
    bg=w.node_tree.nodes.get("Background")
    bg.inputs["Color"].default_value=(0.012,0.014,0.018,1)
    bg.inputs["Strength"].default_value=0.32

    s.render.engine="BLENDER_EEVEE"
    s.render.resolution_x=640
    s.render.resolution_y=800
    s.render.resolution_percentage=100
    s.render.image_settings.file_format="PNG"
    s.render.image_settings.color_mode="RGBA"
    s.render.film_transparent=False
    try:
        s.view_settings.look="AgX - Medium High Contrast"
    except Exception:
        pass
    return s,cam

def main():
    input_blend,outdir=parse_args()
    outdir.mkdir(parents=True,exist_ok=True)
    if Path(bpy.data.filepath).resolve()!=input_blend:
        bpy.ops.wm.open_mainfile(filepath=str(input_blend))
    s,cam=setup_scene()
    target=(0.0,0.0,0.92)

    for name,pos in VIEWS:
        cam.location=pos
        look_at(cam,target)
        s.render.filepath=str(outdir/f"cherpg-pawn-v0.5.4-{name}.png")
        bpy.ops.render.render(write_still=True)
        print("RENDERED",name,s.render.filepath)

if __name__=="__main__":
    main()
