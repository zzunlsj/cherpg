import bpy
import math
import sys
from pathlib import Path
from mathutils import Vector

def parse_args():
    args = sys.argv
    if "--" not in args:
        raise RuntimeError("Expected: input_blend output_png")
    args = args[args.index("--")+1:]
    if len(args) < 2:
        raise RuntimeError("Usage: blender --background file.blend --python render_v054.py -- file.blend out.png")
    return Path(args[0]).resolve(), Path(args[1]).resolve()

def look_at(obj, target):
    direction = Vector(target) - obj.location
    obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()

def add_area(name, loc, energy, size, color=(1.0,1.0,1.0)):
    data = bpy.data.lights.new(name=name, type="AREA")
    data.energy = energy
    data.shape = "DISK"
    data.size = size
    data.color = color
    obj = bpy.data.objects.new(name, data)
    bpy.context.scene.collection.objects.link(obj)
    obj.location = loc
    look_at(obj, (0,0,0.9))
    return obj

def main():
    input_blend, output_png = parse_args()
    output_png.parent.mkdir(parents=True, exist_ok=True)
    if Path(bpy.data.filepath).resolve() != input_blend:
        bpy.ops.wm.open_mainfile(filepath=str(input_blend))

    scene = bpy.context.scene
    scene.frame_set(1)

    # Neutral portrait render of the actual v0.5.4 model.
    for o in list(scene.objects):
        if o.type in {"CAMERA","LIGHT"}:
            bpy.data.objects.remove(o, do_unlink=True)

    # Ground plane.
    bpy.ops.mesh.primitive_plane_add(size=8.0, location=(0,0,0.0))
    ground = bpy.context.object
    ground.name = "RenderGround"
    mat = bpy.data.materials.new("RenderGroundMat")
    mat.diffuse_color = (0.055,0.06,0.065,1.0)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (0.055,0.06,0.065,1.0)
    bsdf.inputs["Roughness"].default_value = 0.78
    ground.data.materials.append(mat)

    # Camera: front 3/4 view, approximately eye-level.
    cam_data = bpy.data.cameras.new("RenderCamera")
    cam = bpy.data.objects.new("RenderCamera", cam_data)
    scene.collection.objects.link(cam)
    cam.location = (2.35, -3.55, 1.72)
    cam.data.lens = 62
    look_at(cam, (0.0, 0.0, 0.91))
    scene.camera = cam

    # Three point lighting plus soft top.
    add_area("Key", (-2.2,-2.6,3.1), 1150, 2.4, (1.0,0.82,0.66))
    add_area("Fill", (2.4,-1.5,2.0), 620, 2.2, (0.68,0.80,1.0))
    add_area("Rim", (0.4,2.6,2.6), 980, 1.7, (0.75,0.84,1.0))
    add_area("Top", (0.0,0.1,4.4), 500, 2.8, (1.0,0.93,0.82))

    world = scene.world or bpy.data.worlds.new("World")
    scene.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes.get("Background")
    bg.inputs["Color"].default_value = (0.012,0.014,0.018,1.0)
    bg.inputs["Strength"].default_value = 0.32

    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 900
    scene.render.resolution_y = 1100
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.filepath = str(output_png)
    scene.render.film_transparent = False

    # High enough quality while staying CI-friendly.
    scene.render.image_settings.color_depth = "8"
    scene.render.resolution_percentage = 100

    # Filmic/AgX defaults give reliable PBR response.
    try:
        scene.view_settings.look = "AgX - Medium High Contrast"
    except Exception:
        pass

    bpy.ops.render.render(write_still=True)
    print(f"RENDER_PNG={output_png}")

if __name__ == "__main__":
    main()
