# Unity 2D → Godot 3D movement analysis

Source: uploaded `pawn_player.cs`, `pawn_player : MonoBehaviour` using `Rigidbody2D` and Unity InputSystem.

| Unity C# behavior | Godot 0.0.6v mapping |
|---|---|
| A/D & W/S, 2-axis input | W/S along Pawn logical heading only; no lateral freedom |
| `Mathf.MoveTowards(inputVec, raw, delta * 10)` | `smoothed_input = move_toward(...,10*delta)` |
| `maxSpeed=4.0` | `WALK_MPS=4.0` |
| `sprintSpeedScaile=1.5` | `RUN_MPS=6.0` |
| `maxForce=20000` | recorded as original source constant; acceleration recalibrated |
| `sprintForceScaile=2` | multiply movement acceleration by 2 when sprinting |
| `maxStopFriction=0.5`, `moveFriction=0.3` | mimic static/friction direction effects (not original force units) |
| `minSpeed=0.1`, `minForce=0.1` | adapted dead zone / stop threshold |
| `force -= velocity.normalized * maxForce` when idle | strong release brake |
| Animator speed from linear velocity | stride cycle uses Godot `get_real_velocity` |
| No vertical jump implementation | new Space jump (separate from input/force) |
| Left mouse attack trigger | excluded from movement-only test |

**Why force units differ:** Unity's `AddForce(force * Time.fixedDeltaTime)` is called under a 2D RigidBody solver. Simply copying its numeric 20,000 into Godot CharacterBody3D acceleration ignores mass, timestep, scale and floor contact. Match the responsive ramp / speed caps / braking shape before artistic tuning.

The original Unity script's W/S/A/D behavior is unconstrained; the Godot test preserves the user's Pawn chess-direction rule instead of imposing unrestricted third-person strafe movement.
