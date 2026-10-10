"""CheRPG PAWN HERO, illustration-led MODULAR head v0.0.11.
Three TOP LEVEL parts (helmet, hair, face), with detachable facial subparts.
Coordinates in metres, one common origin for every GLB. This is a stylized
stone automaton, not a human scan; no anatomical ear canal or eye spheres.
"""
import bpy, math, json, sys
from pathlib import Path
from mathutils import Vector

args=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
if len(args)!=1: raise RuntimeError("Usage: -- OUTPUT_DIR")
out=Path(args[0]).resolve();out.mkdir(parents=True,exist_ok=True)
bpy.ops.object.select_all(action="SELECT");bpy.ops.object.delete(use_global=False)
for data in list(bpy.data.collections):
    if data.name!="Collection" and data.users==0:bpy.data.collections.remove(data)

sc=bpy.context.scene
sc.unit_settings.system="METRIC"
sc.render.engine="CYCLES";sc.cycles.samples=10
sc.render.resolution_x=640;sc.render.resolution_y=640
sc.render.resolution_percentage=100
sc.render.image_settings.file_format="PNG"
sc.render.film_transparent=False
sc.view_settings.view_transform="Standard"
sc.world.color=(.76,.76,.76)
sc["character"]="CheRPG PAWN HERO"
sc["style_reference"]="User-approved pawn hero 3-part and 10-angle turnarounds"
sc["part_structure"]="3 top-level groups: helmet, hair, face; facial features independently detachable"
sc["status"]="geometry draft — illustration likeness must be visually approved"
sc["version"]="0.0.11"

def mat(name, color, rough=0.81):
    m=bpy.data.materials.new(name);m.diffuse_color=(*color,1)
    m.use_nodes=True
    p=m.node_tree.nodes.get("Principled BSDF")
    p.inputs["Base Color"].default_value=(*color,1)
    p.inputs["Roughness"].default_value=rough
    return m
stone=mat("STONE_ivory_no_gold",(.79,.73,.67))
stone_l=mat("STONE_highlight",(.89,.83,.76))
stone_inner=mat("STONE_helmet_inner",(.34,.32,.31))
hairmat=mat("HAIR_carved_ivory",(.89,.81,.70))
hairshade=mat("HAIR_inner_shadow",(.65,.58,.51))
browmat=mat("BROWS_warm_taupe",(.45,.35,.29))
eyeedge=mat("EYE_almond_outline",(.19,.14,.13))
white=mat("EYE_ivory_insert",(.91,.86,.79))
amber=mat("EYE_amber_illustration",(.55,.29,.12),.48)
dark=mat("EYE_pupil_ink",(.15,.09,.07))
mouthmat=mat("MOUTH_soft_neutral",(.39,.30,.28))

parts={}
def group(name,parent=None):
    o=bpy.data.objects.new(name,None);sc.collection.objects.link(o)
    o.empty_display_type="PLAIN_AXES";o.empty_display_size=.013
    if parent:o.parent=parent
    return o
root=group("PAWN_HERO_MODULAR_ORIGIN")
helmet=group("PART_01_HELMET",root)
hair=group("PART_02_HAIR",root)
face=group("PART_03_FACE",root)
parts.update(helmet=helmet,hair=hair,face=face)
sub={}
for key,label in (
    ("face_shape","SUB_03_01_FACE_SHAPE"),("ears","SUB_03_02_EARS_L_R"),
    ("eyes","SUB_03_03_EYES_FLAT_INLAYS"),("brows","SUB_03_04_EYEBROWS"),
    ("nose","SUB_03_05_NOSE"),("mouth","SUB_03_06_MOUTH")):
    sub[key]=group(label,face)

def mesh_obj(name,vs,fs,ma,parent,smooth=False):
    mesh=bpy.data.meshes.new(name+"_mesh")
    mesh.from_pydata(vs,[],fs);mesh.update()
    obj=bpy.data.objects.new(name,mesh)
    sc.collection.objects.link(obj);obj.parent=parent
    obj.data.materials.append(ma)
    for poly in mesh.polygons:poly.use_smooth=smooth
    return obj

def lathe(name, profile, parent, ma, segments=64, oval_y=1):
    verts=[(r*math.cos(j*math.tau/segments),
            oval_y*r*math.sin(j*math.tau/segments),z)
           for r,z in profile for j in range(segments)]
    faces=[]
    for i in range(len(profile)-1):
        for j in range(segments):
            k=(j+1)%segments
            faces.append((i*segments+j,i*segments+k,
                          (i+1)*segments+k,(i+1)*segments+j))
    return mesh_obj(name,verts,faces,ma,parent,True)

# 1. Symmetric pawn hat: hollow underside without hanging tabs/decorations.
# A continuous thick open-ended shell: outer top -> inner roof -> inner brim.
profile=[
 (.109,.214),(.113,.225),(.109,.240),(.104,.257),
 (.097,.277),(.084,.295),(.065,.310),(.043,.320),(.019,.326),
 (.007,.327),(.007,.309),(.020,.307),(.043,.301),
 (.066,.286),(.082,.267),(.091,.245),(.095,.223),(.095,.214)]
hat=lathe("Helmet_hollow_open_shell",profile,helmet,stone,96,.91)
hat["hollow_open_base"]=True;hat["symmetry"]="bilateral X about local origin"
# Enforced matching stone globe centered directly above hat crown.
def sphere(name,origin,radii,parent,ma,segments=40,rings=22):
    vs=[];fs=[]
    for i in range(rings+1):
        a=math.pi*i/rings
        for j in range(segments):
            b=math.tau*j/segments
            vs.append((origin[0]+radii[0]*math.sin(a)*math.cos(b),
                       origin[1]+radii[1]*math.sin(a)*math.sin(b),
                       origin[2]+radii[2]*math.cos(a)))
    for i in range(rings):
        for j in range(segments):
            k=(j+1)%segments
            fs.append((i*segments+j,i*segments+k,(i+1)*segments+k,(i+1)*segments+j))
    return mesh_obj(name,vs,fs,ma,parent,True)
sphere("Helmet_Pawn_crown_sphere",(0,0,.368),(.046,.043,.047),helmet,stone)
# Tonal ring is not a decorative ornament, it is an integral silhouette band.
# It is geometrically symmetric and shares same scale as the cap.
lathe("Helmet_arch_band",[(.106,.244),(.111,.251),(.111,.256),(.107,.260)],
      helmet,stone_l,96,.91)

# 2. Hair. The cap and swept, blade-shaped overlapping locks are ONE logical
# hair part, without face, ears or helmet fragments.
sphere("Hair_crown_under_helmet",(0,.002,.236),(.091,.077,.072),hair,hairshade,48,24)
def lock(name,p0,p1,p2,width,angle,ma=hairmat):
    side=Vector((-math.sin(angle),math.cos(angle),0))
    points=(Vector(p0),Vector(p1),Vector(p2))
    ws=(width*.69,width,width*.015)
    vertices=[]
    for i,p in enumerate(points):
        w=ws[i]
        front=Vector((0,-.005,0))
        back=Vector((0,.005,0))
        for offset in (side*w/2,-side*w/2):
            vertices.append(tuple(p+offset+front))
        for offset in (side*w*.41,-side*w*.41):
            vertices.append(tuple(p+offset+back))
    faces=[]
    for i in range(2):
        a=4*i;b=a+4
        faces.extend([(a,a+1,b+1,b),(a+2,b+2,b+3,a+3),
                      (a,b,a+2,b+2),(a+1,a+3,b+3,b+1)])
    faces.extend([(0,2,3,1),(8,9,11,10)])
    return mesh_obj(name,vertices,faces,ma,hair,False)
# front / side / rear stylized angular hair tufts
for i in range(22):
    theta=-math.pi/2+math.tau*i/22
    front_side=math.sin(theta)<-.45
    root_r=.033
    rm=.073
    rend=.095
    ztip=.143 if front_side else (.143 if abs(math.cos(theta))>.78 else .158)
    # distinct sweeping bangs at the front, side tufts further down
    skew=(-.012 if i%2 else .012) if front_side else 0.
    p0=(root_r*math.cos(theta),root_r*math.sin(theta),.289)
    p1=(rm*math.cos(theta)+skew,rm*math.sin(theta),.236 if front_side else .207)
    p2=(rend*math.cos(theta)+skew*1.25,
        rend*math.sin(theta),ztip)
    lock("Hair_carved_lock_%02d"%i,p0,p1,p2,.026 if front_side else .022,theta)
# front signature asymmetrical curved central bangs from user reference
lock("Hair_signature_front_bang",
     (-.021,-.037,.283),(.006,-.091,.218),(.030,-.092,.152),.034,-math.pi/2)

# 3-1. FACE SHAPE: full original-size bald cranial envelope AND broad neck,
# with absolutely no baked ears, eyes, eyebrow, nose or mouth.
headprofile=[(.002,.017),(.028,.026),(.052,.053),(.068,.086),
             (.077,.122),(.085,.165),(.091,.200),(.091,.236),
             (.082,.265),(.063,.285),(.036,.298),(.002,.302)]
facebase=lathe("Face_shape_whole_cranium_and_jaw",headprofile,sub["face_shape"],stone,96,.86)
# Short broad neck specified by the user (roughly twice initial narrow version)
lathe("Face_neck_integral_broad",[(.036,-.020),(.037,.015),(.034,.044)],
      sub["face_shape"],stone,64,.92)

# 3-2. EARS: low-relief, simple stylized stone pair with slight hollow.
# Independent meshes, mirror signs exactly and use a common origin.
for sign,label in ((-1,"L"),(1,"R")):
    rows=7;segments=32;vv=[];ff=[]
    for k in range(rows):
        q=k/(rows-1)
        for j in range(segments):
            a=math.tau*j/segments
            z=.177+.032*q*math.sin(a)
            y= .002+.017*q*math.cos(a)
            # cup-shaped center inset and outer rim, no intricate human folds
            x=sign*(.082+.008*q+.003*math.exp(-((q-.83)/.18)**2)-.002*(1-q))
            vv.append((x,y,z))
    for k in range(rows-1):
        for j in range(segments):
            n=(j+1)%segments
            ff.append((k*segments+j,k*segments+n,(k+1)*segments+n,(k+1)*segments+j))
    ear=mesh_obj("Ear_simple_%s"%label,vv,ff,stone_l,sub["ears"],True)
    ear["mirrored_from_common_dimensions"]=True

# Thin ceramic surface inlays rather than separate anatomical eyeballs.
# Preserve 2D anime eyes of the final illustration, no spherical eyes.
def thin_polygon(name,polygon,depth,parent,ma):
    # polygon is pairs of (x,z), front facing -Y
    return mesh_obj(name,[(x,depth,z) for x,z in polygon],
                    [tuple(range(len(polygon)))],ma,parent,False)
for sign,label in ((-1,"L"),(1,"R")):
    cx=sign*.038
    eyey=-.078
    pts=[(cx-.025,.159),(cx-.012,.171),(cx+.013,.171),
         (cx+.024,.163),(cx+.015,.151),(cx-.014,.151)]
    thin_polygon("Eye_almond_outline_%s"%label,pts,eyey,sub["eyes"],eyeedge)
    scl=[(cx-.019,.159),(cx-.008,.166),(cx+.010,.166),
         (cx+.017,.159),(cx+.008,.154),(cx-.009,.154)]
    thin_polygon("Eye_ivory_insert_%s"%label,scl,eyey-.001,sub["eyes"],white)
    # Amber center oval is a near-planar insert, NOT an eyeball.
    vv=[(cx+.006*math.cos(t*math.tau/28),eyey-.002,
         .159+.008*math.sin(t*math.tau/28)) for t in range(28)]
    mesh_obj("Eye_amber_flat_%s"%label,vv,[tuple(range(28))],amber,sub["eyes"])
    vv=[(cx+.0026*math.cos(t*math.tau/20),eyey-.0028,
         .159+.005*math.sin(t*math.tau/20)) for t in range(20)]
    mesh_obj("Eye_pupil_flat_%s"%label,vv,[tuple(range(20))],dark,sub["eyes"])
    brow=[(cx-.021,.192),(cx-.006,.195),(cx+.018,.191),(cx+.020,.188),
          (cx-.006,.190),(cx-.019,.189)]
    thin_polygon("Brow_neutral_%s"%label,brow,-.078,sub["brows"],browmat)

# 3-5: tiny faceted nose (explicitly no realistic nostrils).
nosev=[(-.009,-.077,.120),(.009,-.077,.120),(0,-.094,.115),
       (-.003,-.080,.103),(.003,-.080,.103)]
mesh_obj("Nose_stone_lowpoly",nosev,[(0,1,2),(0,2,3),(1,4,2),(3,2,4)],
         stone_l,sub["nose"])
# 3-6: closed neutral mouth, neither grin nor dark mouth aperture.
thin_polygon("Mouth_neutral_small",
             [(-.015,.085),(0,.085),(.015,.085),(.006,.083),
              (-.006,.083)],-.075,sub["mouth"],mouthmat)

def descendants(parent):
    children=[]
    for obj in bpy.data.objects:
        p=obj.parent
        while p is not None:
            if p is parent:
                children.append(obj);break
            p=p.parent
    return children

meshparts=[o for o in bpy.data.objects if o.type=="MESH"]
assert len({id(x) for x in meshparts})==len(meshparts)
assert len(meshparts)>=40, len(meshparts)
assert all(descendants(q) for q in (helmet,hair,face,*sub.values()))
assert not any(o.name.startswith(("Eyeball_","Iris_","Pupil_")) for o in meshparts)
assert len([o for o in descendants(sub["ears"]) if o.type=="MESH"])==2

def save_glb(filename,items):
    bpy.ops.object.select_all(action="DESELECT")
    for ob in items:ob.select_set(True)
    if not items:raise ValueError(filename)
    bpy.context.view_layer.objects.active=items[0]
    opts={"filepath":str(out/filename),"export_format":"GLB"}
    properties=set(p.identifier for p in bpy.ops.export_scene.gltf.get_rna_type().properties)
    if "use_selection" in properties:opts["use_selection"]=True
    elif "export_selected" in properties:opts["export_selected"]=True
    else:raise RuntimeError("GLTF exporter does not support selection")
    bpy.ops.export_scene.gltf(**opts)
    if (out/filename).stat().st_size<1000:raise RuntimeError("Empty GLB: "+filename)

def render(name,visible,camera_pos,target=(0,0,.200),ortho=.51):
    for o in meshparts:o.hide_render=(o not in visible)
    camera.location=camera_pos
    camera.rotation_euler=(Vector(target)-camera.location).to_track_quat("-Z","Y").to_euler()
    camera.data.ortho_scale=ortho
    sc.render.filepath=str(out/(name+".png"))
    bpy.ops.render.render(write_still=True)
    if (out/(name+".png")).stat().st_size<1000:raise RuntimeError("Empty PNG: "+name)

bpy.ops.object.camera_add(location=(0,-2,.20))
camera=bpy.context.object;camera.name="CAM_ORTHO";camera.data.type="ORTHO"
sc.camera=camera
def area(name,xyz,power,size):
    bpy.ops.object.light_add(type="AREA",location=xyz)
    o=bpy.context.object;o.name=name;o.data.energy=power;o.data.shape="DISK"
    o.data.size=size
    o.rotation_euler=(Vector((0,0,.20))-o.location).to_track_quat("-Z","Y").to_euler()
area("Key_light",(-1.4,-1.8,2.2),220,3.0)
area("Fill_light",(1.7,1.1,1.8),120,2.0)
allparts=[o for o in meshparts]
sc["passes_expected"]="4 component GLBs, assembled GLB, 18 true renders"

# Save editable master with each subgroup kept in ORIGINAL assembly coordinates.
bpy.ops.wm.save_as_mainfile(filepath=str(out/"pawn-head-parts-v0.0.11.blend"))
exports={
 "01_helmet":descendants(helmet),
 "02_hair":descendants(hair),
 "03_01_face_shape":descendants(sub["face_shape"]),
 "03_02_ears":descendants(sub["ears"]),
 "03_face_complete":descendants(face),
 "assembled":descendants(root)
}
for tag,objs in exports.items():
    save_glb("pawn-head-"+tag+"-v0.0.11.glb",objs)
views=[("front",(0,-1.75,.23)),("front_right_45",(1.24,-1.24,.23)),
 ("right",(1.75,0,.23)),("back_right_135",(1.24,1.24,.23)),
 ("back",(0,1.75,.23)),("back_left_225",(-1.24,1.24,.23)),
 ("left",(-1.75,0,.23)),("front_left_315",(-1.24,-1.24,.23)),
 ("top",(0,0,1.9)),("bottom",(0,0,-1.45))]
for name,pos in views:
    render("pawn-head-assembled-"+name+"-v0.0.11",allparts,pos)
for name,objs in exports.items():
    if name not in ("assembled","03_face_complete"):
        oset={o for o in objs if o.type=="MESH"}
        render("pawn-head-"+name+"-front-v0.0.11",oset,(0,-1.75,.23))
        render("pawn-head-"+name+"-right-v0.0.11",oset,(1.75,0,.23))
# one full face view, with eyes and brows etc
render("pawn-head-03_face_complete-front-v0.0.11",
       {o for o in exports["03_face_complete"] if o.type=="MESH"},(0,-1.75,.23))
for o in meshparts:o.hide_render=False

png=list(out.glob("pawn-head-*.png"));glb=list(out.glob("pawn-head-*.glb"))
report={"version":"0.0.11","primary_parts":["helmet","hair","face"],
 "subparts":["face_shape","ears","eyes","eyebrows","nose","mouth"],
 "helmet_hollow":True,"hat_bilateral_symmetry":True,
 "ear_object_count":2,"eye_globes":0,"assembled_common_coordinates":True,
 "mesh_count":len(meshparts),"glb_count":len(glb),"render_count":len(png),
 "exports":[p.name for p in glb],"renders":[p.name for p in png],
 "art_reference":"CheRPG pawn hero locked 3-part and 8+2 turnaround concept",
 "visual_approval":"PENDING user review; procedural blockout, not final production model"}
(out/"pawn-head-parts-v0.0.11-report.json").write_text(
    json.dumps(report,indent=2,ensure_ascii=False),encoding="utf-8")
print("CHERPG_MODULAR_HEAD_V0011_SUCCESS",json.dumps(report))
