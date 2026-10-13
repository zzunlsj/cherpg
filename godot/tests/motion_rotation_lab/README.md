# CheRPG — Terrain Motion + Direction Device Test Map (0.0.6v)

**Standalone Godot 4.5.2 project** — independent from the main game map, village and checkpoint. This branch changes no production scenes.

Open `godot/tests/motion_rotation_lab/project.godot` in Godot 4.5.2 and run the project (F5).

## Keyboard
- W/S or Up/Down: move forward/back along the Pawn's current chess-rule heading. No A/D strafing.
- Left Shift: sprint.
- Space: jump; release early for a shorter jump.
- 1–5: flat, 8° incline, 15° incline, uneven, 30° incline test lanes.
- R: expand waist ring and drop four terrain-contact anchors, **only when standing and stopped**.
- E: while grounded device is deployed, rotate only the logical heading 90°, never the body.
- Q: retract anchors and ring. T: reset position. Mouse: orbit camera. Esc: mouse capture toggle.

## Based on uploaded Unity pawn_player.cs
The user-provided 2D source uses input easing at 10/sec, 4.0 max walk speed, 1.5× sprint speed cap (6.0), sprint force multiplier 2, speed/force thresholds 0.1, friction and powerful release braking. This prototype preserves those movement **characteristics**, but recalibrates horizontal force into Godot CharacterBody3D acceleration rather than assuming Rigidbody2D mass and ForceMode units match. `SOURCE_*` constants document the original parameters.

The source has no jump. Godot's jump is separate: takeoff, in-air movement control, early-release lower jump, coyote time, input buffer, landing recovery and visual poses.

## Terrain and device
All parts are simple boxes, spheres, cylinders or torus meshes. Height and grid: Pawn 1.55m; one tile 2m × 2m. Dynamic walk/run joint swing, upper-body pitch and knee lift vary with slope. The four anchor shoes raycast the actual scene collision terrain (plus edge samples) and reject unsupported contacts or telescopic strokes outside 0.18–0.54m. Test lane colliders are two-sided after actual Godot validation.

## Test and limitations
`Godot --headless --path godot/tests/motion_rotation_lab -- --smoke-test` creates and checks five lanes, two leg pivots, four anchors, a grounded deployment, then jump and landing. GitHub Actions additionally checks the parser. CI validates code and geometrical contacts, **not subjective control feel**, original Unity physics equivalence, production map integration, or final sculpted/rigged art. The PR is intentionally a draft.
