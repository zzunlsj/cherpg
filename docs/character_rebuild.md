# Pawn protagonist — rebuild plan

**Status:** Fresh-start character modeling. Legacy v0.5.x results are reference/history only.

## Directories
- `references/` — approved concept illustrations (front, side, 3/4) and scale references
- `modeling/` — fresh Blender scene, head and body mesh
- `renders/` — comparison previews and review sheets
- `rigging/` — animation-ready rig once model approved
- `exports/` — approved GLB intended for Godot

## Quality gates
1. **Reference lock:** artwork, scale (Pawn ~1.5–1.6 m), coordinate axes and silhouette agreed.
2. **Head blockout:** front/side/3/4 silhouette and proportion overlay accepted.
3. **Face:** design integrated eyes, eyelids, nose, mouth and cheeks from one coherent surface. Avoid floating primitive-like parts.
4. **Material:** stone-based living mineral body materials as required by world canon; no cosmetic attempt to hide geometry defects.
5. **Production:** topology, normals, vertex weights, intersection checks, GLB export and Godot import.

No old v0.5.x workflow runs automatically from this new production directory.


## Head work status (v0.0.4 — technical checkpoint, not approved)
- Original reference: the two user-approved Pawn Hero concept/turnaround sheets in the conversation.
- Blender 5.2.2 build: successful; saved at `production/pawn_protagonist/modeling/checkpoints/pawn-face-retopo-v0.0.4.blend`.
- Technical changes: eye/mouth integrated quad-loop patches, eyeball spheres behind integral lids, softened chin and transition surfaces.
- QC: **FAIL visual likeness**. Giant bare cranial vault is temporary (helmet/hair not yet modeled); eyes remain stare-like, nose and upper/lower lip shape are too indistinct, and the face has not passed illustration comparison.
- Next gate: build a registered front+profile guide from the approved reference; tune facial planes and lids with the helmet/hair silhouette visible. Validate shading and topology before rigging.
- Never infer production approval merely from a green GitHub Actions run.

## Head work status (v0.0.5 — geometric features only)
- **User direction:** do **not** add eyeballs, iris or pupils. Sculpt only ears, nose and the **shape of the eye region**. Do not add visual images through image generation.
- Source: `modeling/checkpoints/pawn-face-retopo-v0.0.4.blend`.
- Actual Blender checkpoint: `modeling/checkpoints/pawn-head-shapes-v0.0.5.blend`; render images: `renders/pawn-head-shapes-v0.0.5-*.png`.
- Six eye-related objects deleted (both eyeballs, both irises, both pupils). Eyelid/eye shape is only a shallow stone surface with two integrated retopology regions.
- Nose bridge/tip and both ear forms were sculpted directly into the same head mesh; no detached geometric ear objects.
- This is a **technical checkpoint, not a visual approval**. Ears currently read as simplified concentric relief; the old mouth is still present and was not part of this user's requested feature pass. Do not add finished eyeballs unless explicitly authorized by the user.
