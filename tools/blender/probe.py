"""Check CheRPG's Blender runtime; never create a character model."""
import bpy
import json
import sys
from pathlib import Path
from datetime import datetime, timezone

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
if len(argv) != 1:
    raise RuntimeError("Usage: blender --background --python probe.py -- OUTPUT_DIR")

out = Path(argv[0]).resolve()
out.mkdir(parents=True, exist_ok=True)
if tuple(bpy.app.version) < (5, 2, 2):
    raise RuntimeError("Blender 5.2.2+ is required")
engines = [
    item.identifier
    for item in bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items
]
has_glb_export = hasattr(bpy.ops.export_scene, "gltf")
if not has_glb_export:
    raise RuntimeError("GLB exporter unavailable")
report = {
    "status": "ok",
    "utc": datetime.now(timezone.utc).isoformat(),
    "version": bpy.app.version_string,
    "render_engines": engines,
    "glb_export_available": has_glb_export,
    "note": "Infrastructure check only; no character models created.",
}
(out / "blender-tool-health.json").write_text(
    json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
)
print("CHERPG_BLENDER_TOOL_READY", json.dumps(report))
