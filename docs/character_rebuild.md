# CheRPG Pawn Hero — fresh modeling criteria

**State:** No current Blender scene, GLB export, rig, render, or active modeling workflow. Previous attempts were removed from the active branch on 2026-10-11.

## Illustration is the source of truth
The character is a stylized stone Pawn Hero from the approved user illustration, **not a human**. Keep the natural three-part design hierarchy, proportions and neutral expression. See `docs/pawn_hero_modular_head_contract_v0012.md` for the specific geometry constraints. The contract was written during the older iteration but its **design requirements** remain valid independently of deleted model files.

## Future work — only on explicit request
1. Add the approved reference images to `production/pawn_protagonist/references/`, keeping original file dimensions.
2. Prepare scale-matched front/side/8-direction plus top and bottom artwork.
3. Build the helmet, hair and face as three detachable top-level Blender groups; face shape and ears remain independent and can be rendered alone.
4. Match the illustration's face proportions, layered hair and hollow symmetric helmet; no gold cracks or unrequested ornaments.
5. Check the precise reassembly of original-size parts, then verify render views, mesh quality, GLB export and Godot integration.

No previous model should be reused or presented as approved.
