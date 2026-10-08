import bpy, json, sys
from pathlib import Path
from mathutils import Vector

args=sys.argv[sys.argv.index("--")+1:]
src=Path(args[0]).resolve()
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.gltf(filepath=str(src))

rows=[]
for o in bpy.context.scene.objects:
    if o.type!="MESH":
        continue
    if o.name.startswith("DEVICE_") or "ElbowRing" in o.name:
        corners=[o.matrix_world@Vector(c) for c in o.bound_box]
        mn=[min(p[i] for p in corners) for i in range(3)]
        mx=[max(p[i] for p in corners) for i in range(3)]
        center=[(mn[i]+mx[i])*0.5 for i in range(3)]
        size=[mx[i]-mn[i] for i in range(3)]
        rows.append({
            "name":o.name,
            "parent":o.parent.name if o.parent else None,
            "location_world":[round(v,6) for v in center],
            "size_world":[round(v,6) for v in size],
            "location_local":[round(v,6) for v in o.location],
            "rotation_euler":[round(v,6) for v in o.rotation_euler],
            "scale":[round(v,6) for v in o.scale]
        })
print("DEVICE_DIAGNOSTIC_JSON")
print(json.dumps(rows,indent=2))
