import bpy,sys,json
from pathlib import Path
from mathutils import Vector

a=sys.argv[sys.argv.index("--")+1:]
blend=Path(a[0]).resolve()
if Path(bpy.data.filepath).resolve()!=blend:bpy.ops.wm.open_mainfile(filepath=str(blend))

rows=[]
for o in bpy.context.scene.objects:
    if o.type!="MESH":continue
    pts=[o.matrix_world@Vector(c) for c in o.bound_box]
    mn=[min(p[i] for p in pts) for i in range(3)]
    mx=[max(p[i] for p in pts) for i in range(3)]
    size=[mx[i]-mn[i] for i in range(3)]
    center=[(mn[i]+mx[i])*0.5 for i in range(3)]
    # Focus on suspicious long/thin objects crossing neck/head region.
    if mx[2] >= 1.33 and mn[2] <= 1.48:
        thin=sorted(size)[0]
        long=max(size)
        if thin < 0.012 and long > 0.055:
            rows.append({
                "name":o.name,
                "group":str(o.get("cherpg_group","")),
                "parent":o.parent.name if o.parent else None,
                "center":[round(v,5) for v in center],
                "size":[round(v,5) for v in size],
            })
print("HEAD_ARTIFACT_DIAGNOSTIC")
print(json.dumps(rows,indent=2))
