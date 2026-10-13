# CheRPG — Pawn Hero primitive blockout 0.0.1v

## Status
First **provisional** low-poly model, built from boxes, faceted spheres, tapered cylinders, a hollow helmet mesh and torus rings. **Not art-approved.** The previously rejected models are not reused.

- Height including top pawn sphere: **1.55 m** (Z 0.00–1.55).
- Orientation: +Z up; character faces -Y; 1 unit = 1 meter.
- Separate head: `PART_01_HELMET`, `PART_02_HAIR`, `PART_03_FACE` with `SUB_03_01_FACE_SHAPE`.
- Other parts: `PART_04_STONE_BODY` and `PART_05_DIRECTION_BELT_PLACEHOLDER`.
- Neutral stylized stone / iron silhouette; no realistic eyes, lips, gold cracks or decorations.
- Direction-device belt is **stowed**; no body-turning animation is implied.
- Artist references 22, 26 and 27 are not in the current GitHub reference folder; no exact likeness is claimed.

## GitHub's retained Blender tool

Script path: `production/pawn_protagonist/modeling/pawn_hero_blockout_0_0_1v.py`

1. Open `Actions` > `CheRPG Blender Tool` > `Run workflow`.
2. Select branch containing the new script, set **action** to `run_script`.
3. Set **script_path** to `production/pawn_protagonist/modeling/pawn_hero_blockout_0_0_1v.py`.
4. When finished, download artifact `cherpg-blender-tool-result` (`.blend`, `.glb`, front/side/threequarter `.png` and JSON manifest).

The workflow only creates an artifact; it does not commit generated models into `main`.

## Model inspection and next pass

- A separate temporary preview GLB can be generated from these same primitive measurements offline; only the Blender script is committed to this branch.
- Python syntax and offline GLB geometry have been checked; **actual Blender execution remains to be confirmed** through the GitHub action.
- Obtain the approved reference images in `production/pawn_protagonist/references` without resizing.
- Review proportions in front / side / three-quarter views (head size, helmet shape, torso width, arms, legs).
- Only after silhouette approval, sculpt detachable face details and study 10-angle likeness.
- Confirm Blender output and Godot import / collisions before calling this game-ready.
