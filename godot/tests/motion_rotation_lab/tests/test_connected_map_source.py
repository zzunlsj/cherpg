"""Fast offline structural regression only; not a playtest."""
from pathlib import Path
p=Path(__file__).resolve().parents[1]
land=(p/"scripts/test_lane.gd").read_text()
lab=(p/"scripts/motion_lab.gd").read_text()
pawn=(p/"scripts/pawn_controller.gd").read_text()
assert "ContinuousGroundCollision" in land
assert "const START_Z := 14.0" in land and "const END_Z := -56.0" in land
assert "func _smooth_hinge(" in land and "func height_at(" in land
assert "shader_type spatial;" in land and "cull_disabled" in land
assert "dark_line" in land and "alternate" in land and "2.0" in land
assert 'name = "ConnectedTerrain_FiveZones_OneCollision"' in land
assert lab.count("terrain = TERRAIN_SCRIPT.new()") == 1
assert "for i in range(5):" not in lab.split("func _ready() -> void:")[1].split("func _build_lighting")[0]
assert "func _teleport_to_zone(" in lab and "terrain.call(\"spawn_z\", index)" in lab
assert "MOUSE_BUTTON_LEFT" in lab and "pawn.trigger_attack()" in lab
assert "KEY_1, KEY_2, KEY_3, KEY_4, KEY_5" in lab
assert "Input.is_key_pressed(KEY_W)" in pawn and "Input.is_key_pressed(KEY_UP)" in pawn
assert "Input.is_key_pressed(KEY_SHIFT)" in pawn
assert "INPUT_SMOOTHING_PER_SEC := 10.0" in pawn
assert "WALK_MPS := 4.0" in pawn and "RUN_MPS := 6.0" in pawn
assert "func trigger_attack() -> void:" in pawn
assert "func _update_air_pose(" in pawn and "func _update_gait(" in pawn
assert "func _apply_attack_pose(" in pawn and "run_blend" in pawn
print("CHERPG_CONNECTED_BOARD_INPUT_SOURCE_OK (NOT A PLAYTEST)")
