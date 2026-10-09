"""CheRPG Pawn Hero — fresh facial blockout v0.0.1.
No geometry/assets from archived v0.5.x are reused.
Axis: front -Y, up Z; meters. Blender 5.2 LTS.
"""
import bpy, math, sys, json
from pathlib import Path
from mathutils import Vector
a=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
if len(a)!=1: raise SystemExit("Usage: -- output_directory")
out=Path(a[0]).resolve();out.mkdir(parents=True,exist_ok=True)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
# UV parametric continuous skin/stone surface, no separate eye/mouth primitives.
# Head center about 1.405 m, height 0.250 m (young stylized proportions).
LAT=88;LON=128
verts=[];faces=[]
def gaussian(x,c,s):return math.exp(-((x-c)/s)**2)
for i in range(LAT+1):
    t=math.pi*i/LAT
    z=math.cos(t)
    radial=math.sin(t)
    for j in range(LON):
        u=2*math.pi*j/LON
        x=math.cos(u)*radial
        y=math.sin(u)*radial
        # broaden upper face, soften and narrow jaw, round chin
        forehead=gaussian(z,0.42,0.55)
        jaw=max(0.0,(-z-0.12)/0.85)
        cheek=gaussian(z,-0.12,0.32)
        width=0.093*(0.91+0.11*forehead+0.06*cheek-0.24*jaw**1.2)
        depth=0.089*(1-0.07*jaw)
        xx=x*width;yy=y*depth;zz=z*0.126
        # anterior is -Y, front-only weight avoids reshaping rear cranium
        fw=max(0.0,min(1.0,(-y-0.28)/0.56))
        # gentle face-plane without detached accessories
        yy+=0.005*fw*gaussian(z,0.02,0.54)
        # symmetrical shallow eye sockets; place after silhouette established
        left=gaussian(xx,-0.036,0.023);right=gaussian(xx,0.036,0.023)
        eyez=gaussian(zz,0.014,0.018)
        yy+=0.0060*fw*(left+right)*eyez
        # bridge/nose base is integral to the head surface; very subtle placeholder
        bridge=gaussian(xx,0,0.016)*gaussian(zz,-0.013,0.045)
        yy-=0.004*fw*bridge
        # quiet smile/neutral mouth plane, deliberately no drawn-on lips yet
        verts.append((xx,yy,1.422+zz))
for i in range(LAT):
    for j in range(LON):
        n=i*LON+j;n2=i*LON+(j+1)%LON
        faces.append((n,n2,n2+LON,n+LON))
mesh=bpy.data.meshes.new("Pawn_Face_Continuous_Quad_Surface")
mesh.from_pydata(verts,[],faces);mesh.update()
ob=bpy.data.objects.new("Pawn_Head_FaceBlockout",mesh);bpy.context.collection.objects.link(ob)
for p in mesh.polygons:p.use_smooth=True
# No destructive modifiers or overcomplicated separate facial components.
sub=ob.modifiers.new("Face_Subdivision_Preview","SUBSURF");sub.levels=1;sub.render_levels=1
mat=bpy.data.materials.new("Stone_clay_neutral");mat.diffuse_color=(0.72,0.69,0.63,1)
mat.use_nodes=True;mat.node_tree.nodes.get("Principled BSDF").inputs["Base Color"].default_value=(0.72,0.69,0.63,1)
mat.node_tree.nodes.get("Principled BSDF").inputs["Roughness"].default_value=0.87
mesh.materials.append(mat)
world=bpy.data.worlds.new("Review_World");bpy.context.scene.world=world;world.use_nodes=True
world.node_tree.nodes.get("Background").inputs["Color"].default_value=(0.22,0.22,0.22,1)
world.node_tree.nodes.get("Background").inputs["Strength"].default_value=0.7
def track(o,pt):o.rotation_euler=(Vector(pt)-o.location).to_track_quat("-Z","Y").to_euler()
for name,xyz,energy,size in [("Softbox_key",(-1.5,-2.4,3.1),360,2.0),("Softbox_fill",(1.6,-1.7,1.8),210,2.0)]:
    bpy.ops.object.light_add(type="AREA",location=xyz);light=bpy.context.object;light.name=name;light.data.energy=energy;light.data.shape="DISK";light.data.size=size;track(light,(0,0,1.42))
sc=bpy.context.scene;sc.render.engine="CYCLES";sc.cycles.samples=24
sc.render.resolution_x=800;sc.render.resolution_y=800;sc.render.resolution_percentage=100
sc.render.image_settings.file_format="PNG"
sc.view_settings.view_transform="Standard"
cameras={"front":(0,-2.0,1.43),"profile":(2.0,0,1.43),"threequarter":(1.4,-1.6,1.45)}
for view,location in cameras.items():
    bpy.ops.object.camera_add(location=location);cam=bpy.context.object;cam.name="Camera_"+view;track(cam,(0,0,1.42))
    cam.data.type="ORTHO";cam.data.ortho_scale=0.33;sc.camera=cam
    sc.render.filepath=str(out/("pawn-face-blockout-v0.0.1-"+view+".png"))
    bpy.ops.render.render(write_still=True)
sc["reference_status"]="approved user concept sheets; proportional overlay pending"
sc["build_version"]="face-blockout-v0.0.1"
bpy.ops.wm.save_as_mainfile(filepath=str(out/"pawn-face-blockout-v0.0.1.blend"))
report={"version":"0.0.1","status":"blockout-needs-review","mesh":ob.name,"vertices":len(mesh.vertices),"quads":len(mesh.polygons),"separate_eyes":False,"separate_mouth":False,"views":list(cameras),"approval":"not yet matched pixel-for-pixel to approved illustration"}
(out/"report.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
print("CHERPG_BLOCKOUT_SUCCESS",json.dumps(report))
