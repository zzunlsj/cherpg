import bpy, json, sys
from pathlib import Path
from mathutils import Vector

args=sys.argv[sys.argv.index("--")+1:]
blend=Path(args[0]).resolve()

if Path(bpy.data.filepath).resolve()!=blend:
    bpy.ops.wm.open_mainfile(filepath=str(blend))

KEYWORDS=[
    "HEAD","FACE","HELM","HAIR","CHEST","TORSO","RIB","STERNUM",
    "BACKPACK","BEDROLL","BOOT","FOOT","ANKLE","SHIN","DEVICE_",
    "SCARF","CAPE","BELT","TABARD","TASSET"
]

rows=[]
for o in bpy.context.scene.objects:
    if o.type!="MESH":
        continue
    u=o.name.upper()
    if not any(k in u for k in KEYWORDS):
        continue
    corners=[o.matrix_world@Vector(c) for c in o.bound_box]
    mn=[min(p[i] for p in corners) for i in range(3)]
    mx=[max(p[i] for p in corners) for i in range(3)]
    center=[(mn[i]+mx[i])*0.5 for i in range(3)]
    size=[mx[i]-mn[i] for i in range(3)]
    rows.append({
        "name":o.name,
        "group":str(o.get("cherpg_group","")),
        "parent":o.parent.name if o.parent else None,
        "center":[round(v,5) for v in center],
        "size":[round(v,5) for v in size],
        "scale":[round(v,5) for v in o.scale],
    })

rows.sort(key=lambda r:r["name"])
print("SILHOUETTE_DIAGNOSTIC_JSON")
print(json.dumps(rows,indent=2))
