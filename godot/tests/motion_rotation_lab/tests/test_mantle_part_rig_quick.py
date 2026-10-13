"""Static-only regression (<1 second). Gameplay QA remains with user."""
from pathlib import Path
root=Path(__file__).resolve().parents[1]
pawn=(root/'scripts/pawn_controller.gd').read_text(encoding='utf-8')
lab=(root/'scripts/motion_lab.gd').read_text(encoding='utf-8')
terrain=(root/'scripts/test_lane.gd').read_text(encoding='utf-8')
expected=[
 'const MANTLE_TIME := 1.16',
 'func _begin_mantle(',
 'func _mantle_goal(',
 'func _update_mantle(',
 'func _update_mantle_pose(',
 'func _abort_mantle(',
 'move_and_collide(motion)',
 '_constrain_step(global_position,desired)',
 'func _create_part_collision_proxies(',
 'func _part_penetrates_world_or_self(',
 'func _prevent_part_penetration(',
 'func _apply_terrain_pose(',
 'func _apply_surface_tilt(',
 'func _parts_are_connected(',
 'var elbow: Array[Node3D] = []',
 'elbow.append(elbow_pivot)',
 'func _clamp_anatomical_joints()',
 'func _gait_joint_targets(',
 'func _update_climb_pose(',
 'func _update_crouch_pose(',
 'func _update_air_pose(',
]
for token in expected:
    assert token in pawn, token
assert "var mantle_active := false" in pawn
assert "if mantle_active:" in pawn
assert 'CollisionEnvelope' in pawn
assert 'collision_mask = 1 | 4' in pawn
assert 'query.collide_with_areas = true' in pawn
assert 'capsule_shape.height = STANDING_HEIGHT_M' in pawn
assert 'MAX_KNEE_FLEX_RAD' in pawn
assert 'MANTLE: %s' in lab and 'PART COLLIDERS: %d' in lab
assert 'board_grid_visible = true' in terrain
assert 'const TILE_M := 4.0' in terrain
print('CHERPG_MANTLE_ARTICULATED_RIG_SOURCE_OK (NOT A PLAYTEST)')
