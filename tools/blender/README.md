# CheRPG Blender Tool

A reusable **Blender 5.2.2 headless runtime**, separate from all Pawn Hero models.

- [Blender workflow](../../.github/workflows/cherpg-blender-tool.yml) provides installation, validation, script execution, rendering support, GLB exporter, and Actions artifacts.
- **check** validates the runtime via `tools/blender/probe.py` without generating 3D models.
- **run_script** runs an explicitly selected Blender Python script from `production/pawn_protagonist/modeling/` or `tools/blender/scripts/`, passing an output directory after `--`. There are no active modeling scripts at present.
- The workflow does not commit character models back to GitHub; any future generated output is a downloadable workflow artifact.

To run: **Actions → CheRPG Blender Tool → Run workflow**.

Past .blend/.glb files, model-specific scripts, renders, and the legacy archive remain deleted from the current branch.
