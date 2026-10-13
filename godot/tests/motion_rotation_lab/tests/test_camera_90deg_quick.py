"""Fast source regression (<1s), no 3D gameplay simulation."""
from pathlib import Path
root=Path(__file__).resolve().parents[1]
lab=(root/"scripts/motion_lab.gd").read_text(encoding="utf-8")
pawn=(root/"scripts/pawn_controller.gd").read_text(encoding="utf-8")
assert "const CAMERA_ELEVATION_MAX := PI / 2.0" in lab
assert "var camera_elevation := deg_to_rad(24.0)" in lab
assert "camera_elevation-event.relative.y*.003" in lab
assert "camera_distance * cos(camera_elevation)" in lab
assert "camera_distance * sin(camera_elevation)" in lab
assert "camera_elevation >= deg_to_rad(89.0)" in lab
assert "camera.look_at(camera_target,stable_up)" in lab
assert "pawn.set_camera_orbit_yaw(camera_yaw)" in lab
assert "CAMERA: %.0f°/90°" in lab
assert "func set_camera_orbit_yaw(yaw: float) -> void:" in pawn
assert "camera_orbit_forward = Vector3(-sin(yaw),0.0,-cos(yaw))" in pawn
assert "return camera_orbit_forward" in pawn
assert "heading_index = 0" in pawn  # world chess-heading kept separate
assert "var camera_pitch" not in lab
print("CHERPG_CAMERA_90_DEGREES_STATIC_OK (NO PLAYTEST)")
