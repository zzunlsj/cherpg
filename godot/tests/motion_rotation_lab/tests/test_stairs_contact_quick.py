"""Quick source contract for physical stairs and contact-aware IK."""
from pathlib import Path
p=Path(__file__).resolve().parents[1]
pawn=(p/'scripts/pawn_controller.gd').read_text()
terrain=(p/'scripts/test_lane.gd').read_text()
for token in (
    'const MAX_STEP_HEIGHT_M := 0.225',
    'func _try_step_up(',
    'test_move(raised,Vector3.UP*MAX_STEP_HEIGHT_M)',
    'test_move(raised,remaining)',
    'if hit["normal"].y < cos(floor_max_angle):',
    'apply_floor_snap()',
    '_try_step_up(starting_position,next_horizontal*delta,was_on_floor)',
    'func _solve_leg_foot(',
    'func _apply_terrain_pose(',
    'var supporting: bool',
    'foot_contact_valid[i] = true',
    'func _solve_arm_grip(',
    'func _apply_wall_contacts(',
    'hand_contact_valid[i] = true',
    'mantle_wall_normal = climb_normal',
    'var lowest: float = area.global_position.y',
):
    assert token in pawn,token
assert 'SPAWN_Z := [38.0' in terrain and '-13.6]' in terrain
assert 'StepCollision_%02d' in terrain
assert 'upper_leg[index].scale' not in pawn
assert 'knee[index].scale' not in pawn
print('CHERPG_STAIRS_FOOT_HAND_CONTACT_STATIC_OK')
