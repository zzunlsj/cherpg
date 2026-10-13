"""Static structural checks only. Runs in <1s, never simulates gameplay."""
from pathlib import Path
root=Path(__file__).resolve().parents[1]
terrain=(root/"scripts/test_lane.gd").read_text(encoding="utf-8")
lab=(root/"scripts/motion_lab.gd").read_text(encoding="utf-8")
pawn=(root/"scripts/pawn_controller.gd").read_text(encoding="utf-8")
device=(root/"scripts/direction_device.gd").read_text(encoding="utf-8")
board=(root/"scripts/board_rules.gd").read_text(encoding="utf-8")
assert "const WIDTH_M := 100.0" in terrain and "const DEPTH_M := 100.0" in terrain
assert "const TILE_M := 4.0" in terrain and "TILE_SIZE_M := 4.0" in board
assert 'var floor_shape := BoxShape3D.new()' in terrain
assert 'const RAMP_ANGLES := [8.0, 15.0, 30.0, 45.0, 60.0, 75.0, 90.0]' in terrain
assert 'VerticalWallCollision' in terrain and 'UnevenPatchCollision' in terrain
assert "shader_type spatial" in terrain and "dark_tile" in terrain
assert "func spawn_position(" in terrain and "func spawn_count()" in terrain
assert "event.physical_keycode == KEY_F" in lab and 'request_toggle' in lab
assert "KEY_A:" in lab and "KEY_D:" in lab and "request_turn" in lab
assert "Input.is_key_pressed(KEY_F)" in lab and 'set_preview_held' in lab
assert "KEY_R" not in lab
assert "KEY_I:" in lab and "board_rules_enabled" in lab
assert "func _constrain_step(" in pawn and "if board_rules_enabled:" in pawn
assert 'board_grid_visible = true' in terrain and '"board_visible", 1.0' in terrain
assert "KEY_O:" in lab and "KEY_SHIFT:" not in lab and "KEY_CTRL:" not in lab
assert "Input.is_key_pressed(KEY_CTRL)" in pawn
assert "Input.is_key_pressed(KEY_SHIFT)" in pawn
assert "func _update_crouch_collider(" in pawn and "func _can_stand()" in pawn
assert "func _update_crouch_pose(" in pawn and "func _clamp_anatomical_joints()" in pawn
assert "MAX_ASCENT_ANGLE_DEG := 90.0" in pawn
assert "func _wall_contact(" in pawn
assert "cherpg_grabbable" in pawn and "cherpg_grabbable" in terrain
assert "CLIMB_MIN_ANGLE_DEG := 30.0" in pawn
assert "func _gait_joint_targets(" in pawn and "phase < 0.60" in pawn
assert "func request_turn(step: int = 1)" in device
assert "func request_toggle()" in device
assert "func _build_hologram()" in device
assert "func set_preview_held(held: bool)" in device
assert "WorldAligned4mTileBorder" in device
assert "INPUT_SMOOTHING_PER_SEC := 10.0" in pawn
assert "WALK_MPS := 4.0" in pawn
print("CHERPG_100M_MAP_INPUT_AND_HOLOGRAM_STATIC_OK")
