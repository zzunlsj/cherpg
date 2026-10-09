# CheRPG

Godot-based Chess RPG project. This repository is being reorganized for a **new Pawn protagonist model built from scratch**.

## Active production
- `production/pawn_protagonist/`: new character modeling pipeline. No model is approved yet.
- `docs/character_rebuild.md`: modeling milestones and acceptance checks.

## Previous experimental pipeline
All historical v0.5.x source models, Blender scripts, images and rigging artifacts are kept unchanged (identical Git blobs) in `archive/legacy-v0.5/`.

Old Actions workflows were moved out of `.github/workflows/` to `archive/legacy-v0.5/workflows/` to prevent accidental reruns or stale commits. This is a deliberate reset, not loss of history. No legacy facial topology is to be reused as the new master.

## Next steps
1. Put the approved original illustration in `production/pawn_protagonist/references/`.
2. Block out head silhouette from front and side.
3. Approve front, profile and 3/4 views before designing eyes, mouth, or accessories.
4. Add rigging and Godot import only after facial proportions are accepted.
