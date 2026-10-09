# CheRPG Blender pipeline

Canonical repository: `zzunlsj/cherpg` on `main`.
The earlier `claude-config/cherpg-blender-pipeline` branch is archived as Git history; it is **not** a build target.

## Current files
- Base model: `cherpg_pipeline/cherpg-pawn-protagonist-sculpt-refined-v0.5.2.glb`
- Core script chain: `cleanup_v053.py` → `silhouette_v055.py` → `rig_v055.py` → `head_pass_v056.py` → `head_rebuild_v058.py` → `head_detail_v059.py`
- Review renders: `cherpg_pipeline/renders_parts_v059/head/`
- Workflow: `.github/workflows/cherpg-head-v059.yml`

## Running
From the repository Actions tab, dispatch **CheRPG v0.5.9 Head Detail** on `main`; it reconstructs the head, renders front/side/three-quarter/PBR views and uploads a 30-day artifact containing the editable `.blend` file. Rendering requires Blender 5.2.2 and may be costly on Actions.

## Next milestones
1. Verify a clean rerun of v0.5.9 against the migrated `main` branch and inspect all images.
2. Head fidelity pass: silhouette, eye inset/lids, forehead/cheek/chin planes, helmet–hair intersection; compare with the original concept art.
3. Export and validate the updated rigged `.blend`/`.glb`, including bone parenting, materials and mesh intersections.
4. Only then update the version and integrate with Godot.

Do not assume a sculpt matches the concept illustration without a side-by-side concept-art comparison.
