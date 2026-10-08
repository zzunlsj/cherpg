# CheRPG Blender pipeline

This branch is isolated from main and is used only for the CheRPG Pawn protagonist 3D pipeline.

## Current stage: v0.5.3 Blender-ready cleanup

Put the source file at:

`cherpg_pipeline/input/cherpg-pawn-protagonist-sculpt-refined-v0.5.2.glb`

A push of that exact file to branch `cherpg-blender-pipeline` triggers GitHub Actions. The workflow downloads Blender 5.2.2, runs the cleanup pass, and uploads an Actions artifact containing:

- `cherpg-pawn-protagonist-blender-ready-v0.5.3.glb`
- `cherpg-pawn-protagonist-blender-ready-v0.5.3.blend`
- `cherpg-pawn-protagonist-v0.5.3-cleanup-report.json`

The cleanup keeps the 165-part rigid structure, preserves UVs/materials, recalculates normals, uses smooth shading only for face/cloth categories, creates logical Blender collections, gives the main cape real 5 mm thickness, and keeps the direction-device body orientation independent from movement heading.

No destructive merge-by-distance, decimation, or whole-character mesh joining is performed.
