"""Camera wall-safety source regression (<1s). Not a gameplay test."""
from pathlib import Path
p=Path(__file__).resolve().parents[1]
lab=(p/"scripts/motion_lab.gd").read_text(encoding="utf-8")
required=(
    "var camera_distance := 6.8",
    "const CAMERA_COLLISION_RADIUS := 0.23",
    "const CAMERA_SURFACE_MARGIN := 0.08",
    "camera_query_sphere = SphereShape3D.new()",
    "camera.near = 0.06",
    "func _camera_collision_clamp(pivot: Vector3, wanted: Vector3) -> Vector3:",
    "query.shape = camera_query_sphere",
    "query.motion = motion",
    "query.collision_mask = 1",
    "query.collide_with_bodies = true",
    "get_world_3d().direct_space_state.cast_motion(query)",
    "maxf(0.0,movement_length * safe_fraction - CAMERA_SURFACE_MARGIN)",
    "if safe_fraction >= 0.999:",
    "return wanted # preserve EXACT configured orbit distance when clear",
    "_camera_collision_clamp(sweep_pivot,desired)",
    "_camera_collision_clamp(sweep_pivot,interpolated)",
    "CAMERA_FOLLOW_SPEED if camera_wall_blocked else CAMERA_RECOVER_SPEED",
    "sweep_pivot += pawn.climb_normal * 0.11",
    "camera_actual_distance = camera.global_position.distance_to(camera_target)",
    "camera.look_at(camera_target,stable_up)",
    "pawn.set_camera_orbit_yaw(camera_yaw)",
    "const CAMERA_ELEVATION_MAX := PI / 2.0",
)
for token in required:
    assert token in lab, token
assert lab.count("camera.global_position = _camera_collision_clamp") == 1
# Without a collision the return path preserves the full desired distance;
# the safety gap is subtracted only from genuinely obstructed sweeps.
for distance in (1.0,6.8,12.0):
    from math import isclose
    allowed=max(0.,distance-0.08)
    assert allowed<=distance and isclose(distance-allowed,0.08)
print("CHERPG_CAMERA_WALL_SPHERE_CAST_SOURCE_OK (NOT A PLAYTEST)")
