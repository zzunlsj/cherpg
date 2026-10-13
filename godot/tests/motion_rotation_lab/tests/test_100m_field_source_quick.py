"""Static structural checks only. Runs in <1s, never simulates gameplay."""
from pathlib import Path
root=Path(__file__).resolve().parents[1]
terrain=(root/"scripts/test_lane.gd").read_text(encoding="utf-8")
lab=(root/"scripts/motion_lab.gd").read_text(encoding="utf-8")
pawn=(root/"scripts/pawn_controller.gd").read_text(encoding="utf-8")
device=(root/"scripts/direction_device.gd").read_text(encoding="utf-8")
board=(root/"scripts/board_rules.gd").read_text(encoding="utf-8")
assert "const WIDTH_M := 100.0" in terrain and "const DEPTH_M := 100.0" in terrain
assert "const TILE_M := 2.0" in terrain and "TILE_SIZE_M := 2.0" in board
assert 'var floor_shape := BoxShape3D.new()' in terrain
assert 'const RAMP_ANGLES := [8.0, 15.0, 30.0, 45.0, 60.0, 75.0, 90.0]' in terrain
assert 'VerticalWallCollision' in terrain and 'UnevenPatchCollision' in terrain
assert "shader_type spatial" in terrain and "dark_tile" in terrain
assert "func spawn_position(" in terrain and "func spawn_count()" in terrain
assert "KEY_F:" in lab and 'request_toggle' in lab
assert "KEY_A:" in lab and "KEY_D:" in lab and "request_turn" in lab
assert "KEY_R" in lab and 'set_preview_held' in lab
assert "KEY_O:" in lab and "KEY_SHIFT:" in lab and 'pawn.queue_dash()' in lab
assert "func queue_dash()" in pawn and "DASH_COOLDOWN_SECONDS" in pawn
assert "MAX_ASCENT_ANGLE_DEG := 90.0" in pawn
assert "func _wall_contact(" in pawn
assert "func request_turn(step: int = 1)" in device
assert "func request_toggle()" in device
assert "func _build_hologram()" in device
assert "func set_preview_held(held: bool)" in device
assert 'BoardTile2x2m_Hologram' not in device or 'WorldAligned2mTileBorder' in device
assert "INPUT_SMOOTHING_PER_SEC := 10.0" in pawn
assert "WALK_MPS := 4.0" in pawn
print("CHERPG_100M_MAP_INPUT_AND_HOLOGRAM_STATIC_OK")
