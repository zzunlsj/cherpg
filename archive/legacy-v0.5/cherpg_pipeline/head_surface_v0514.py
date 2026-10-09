import bpy,bmesh,math,json,sys
from pathlib import Path
from mathutils import Vector

VERSION="0.5.14-head-surface"

def parse_args():
    a=sys.argv
    if "--" not in a:raise RuntimeError("expected input output")
    a=a[a.index("--")+1:];return Path(a[0]).resolve(),Path(a[1]).resolve()

def mat_like(*hints):
    for h in hints:
        for m in bpy.data.materials:
            if h.lower() in m.name.lower():return m
    return bpy.data.materials[0] if bpy.data.materials else None

def arm():return bpy.data.objects.get("RIG_PawnHero")

def skin(o,group="HEAD"):
    a=arm();o["cherpg_group"]=group
    if not a:return
    for vg in list(o.vertex_groups):o.vertex_groups.remove(vg)
    vg=o.vertex_groups.new(name="Head")
    if len(o.data.vertices):vg.add(list(range(len(o.data.vertices))),1.0,"REPLACE")
    for m in list(o.modifiers):
        if m.type=="ARMATURE":o.modifiers.remove(m)
    md=o.modifiers.new("CheRPG_Armature","ARMATURE");md.object=a
    o["cherpg_primary_bone"]="Head";o["cherpg_skin_mode"]="rigid"

def segment(name,p0,p1,r,mat,group="HEAD"):
    p0,p1=Vector(p0),Vector(p1);d=p1-p0;L=d.length
    bpy.ops.mesh.primitive_cylinder_add(vertices=12,radius=r,depth=L,location=(p0+p1)*0.5)
    o=bpy.context.object;o.name=name;o.rotation_euler=d.to_track_quat("Z","Y").to_euler()
    if mat:o.data.materials.append(mat)
    skin(o,group)
    return o

def tiny_sphere(name,loc,r,mat,group="HELMET"):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=20,ring_count=10,radius=r,location=loc)
    o=bpy.context.object;o.name=name
    if mat:o.data.materials.append(mat)
    skin(o,group)
    return o

inp,out=parse_args()
if Path(bpy.data.filepath).resolve()!=inp:bpy.ops.wm.open_mainfile(filepath=str(inp))
stone=mat_like("marble","stone");iron=mat_like("iron","metal");brass=mat_like("brass","gold")
changes=[]

# Fine stone micro-displacement on large stone surfaces.
for name,strength,scale in [
    ("HEAD4_Face",0.00075,5.0),
    ("HELM4_Main",0.00085,4.0),
    ("HELM4_PawnSphere",0.00075,4.5),
    ("HELM6_StoneLip",0.00055,5.0),
]:
    o=bpy.data.objects.get(name)
    if not o:continue
    tex=bpy.data.textures.new(name+"_StoneNoise",type="CLOUDS")
    tex.noise_scale=0.055
    tex.noise_depth=2
    md=o.modifiers.new(name+"_MicroStone","DISPLACE");md.texture=tex;md.strength=strength;md.texture_coords="GLOBAL";md.mid_level=0.5
    bpy.context.view_layer.objects.active=o
    try:bpy.ops.object.modifier_apply(modifier=md.name)
    except:pass
    changes.append(name+" microstone")

# Small carved cracks; geometry is intentionally shallow and short.
cracks=[
("FaceCrackA",(-0.073,0.097,1.400),(-0.064,0.101,1.393)),
("FaceCrackB",(-0.064,0.101,1.393),(-0.069,0.100,1.384)),
("FaceCrackC",(0.082,0.085,1.458),(0.087,0.080,1.449)),
]
for n,a,b in cracks:segment("HEAD8_"+n,a,b,0.00055,iron,"HEAD")
changes.append("face micro cracks")

# Helmet seam accents: subtle front-visible plate separation.
seams=[
("HelmSeamL",(-0.092,0.116,1.572),(-0.074,0.126,1.611)),
("HelmSeamR",(0.092,0.116,1.572),(0.074,0.126,1.611)),
("HelmSeamC",(0.0,0.145,1.570),(0.0,0.132,1.620)),
]
for n,a,b in seams:segment("HELM8_"+n,a,b,0.00075,iron,"HELMET")
changes.append("helmet seams")

# Four tiny aged-brass rivets on lower helmet trim.
for i,(x,y) in enumerate([(-0.110,0.112),(0.110,0.112),(-0.145,0.045),(0.145,0.045)]):
    tiny_sphere(f"HELM8_Rivet_{i}",(x,y,1.553),0.0035,brass,"HELMET")
changes.append("helmet rivets")

# Small dark separation at hair roots to visually layer hair beneath helmet.
for x in [-0.075,-0.025,0.025,0.075]:
    segment(f"HEAD8_HairRoot_{x}",(x,0.102,1.526),(x,0.105,1.535),0.0007,iron,"HEAD")
changes.append("hair root separation")

bpy.context.scene["cherpg_version"]=VERSION;bpy.context.scene["part_pass"]="HEAD_SURFACE_DETAIL"
bpy.context.scene["part_pass_goal"]="illustration-like stone wear, helmet paneling, restrained metal details"
out.parent.mkdir(parents=True,exist_ok=True);bpy.ops.wm.save_as_mainfile(filepath=str(out))
out.with_suffix(".json").write_text(json.dumps({"version":VERSION,"changes":changes},ensure_ascii=False,indent=2),encoding="utf-8")
print(json.dumps({"version":VERSION,"changes":changes},ensure_ascii=False,indent=2))
