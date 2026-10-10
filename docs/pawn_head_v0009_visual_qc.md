# CheRPG Pawn Protagonist | v0.0.9 Actual Render QC (2026-10-10)

Status: **FAIL artistic acceptance**, **PASS technical scene generation**.

Five Blender-rendered images exist under `production/pawn_protagonist/renders/`:
- [Front](../production/pawn_protagonist/renders/pawn-head-shapes-v0.0.9-front.png)
- [Profile](../production/pawn_protagonist/renders/pawn-head-shapes-v0.0.9-profile.png)
- [Three-quarter](../production/pawn_protagonist/renders/pawn-head-shapes-v0.0.9-threequarter.png)
- [Face detail](../production/pawn_protagonist/renders/pawn-head-shapes-v0.0.9-face-detail.png)
- [Ear detail](../production/pawn_protagonist/renders/pawn-head-shapes-v0.0.9-ear-detail.png)

Actual geometric report: 192,368 vertices, 6,044 ear-sculpt vertices, 786 eye-region vertices, 5,094 nose-transition vertices, zero eyeballs, pupils or irises. Max sculpt displacement 12.17 mm.

## Visual findings
1. Ear: Helix and inner branches are no longer concentric, but their relief is excessive, giving visibly angular, pointed upper and lower edges especially in front/profile.
2. Nose: Anterior nose silhouette and tip still look flat/boxlike. Need smoother continuous bridge-to-tip-to-cheek blending.
3. Eyes: Strictly no eyes/globes per the user's request. The eyelid-only markings are so shallow that they nearly vanish in face detail. Raise/lower stone surface very subtly, without apertures.
4. The early mouth slit is unchanged by scope. Do not silently add mouth changes to ear/nose/eye-only tasks.
5. Still lack artwork registration/landmark comparison. Never mark full-model similarity approved purely from a successful GitHub Action.

## Planned v0.0.10 response
- Invert v0.0.9's ear displacement on the actual high-density mesh and reconstruct at lower, broader amplitudes.
- Apply local, vertex-group-restricted smoothing, preserving the surrounding head surface.
- Add slight continuous nose tip and alar adjustment, no detached shapes.
- Adjust lid relief only (zero ocular objects).
- Generate five actual Blender render views; manually review before approval.

Only production checkpoints can be promoted to Godot after reference comparison, manifold/normal review and retopology.
