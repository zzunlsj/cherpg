"""Under-one-second source checks. Actual Godot gameplay is user-tested."""
from pathlib import Path
import math
root=Path(__file__).resolve().parents[1]
pawn=(root/'scripts/pawn_controller.gd').read_text()
lab=(root/'scripts/motion_lab.gd').read_text()
assert 'var movement_camera: Camera3D' in pawn
assert 'func set_movement_camera(' in pawn
assert '-movement_camera.global_transform.basis.z' in pawn
assert 'horizontal.y = 0.0' in pawn
assert pawn.count('var forward: Vector3 = _camera_flat_forward()') == 2
assert 'var right: Vector3 = forward.cross(Vector3.UP)' in pawn
assert 'collider.position.y = capsule.height * 0.5' in pawn
assert 'Vector3(0, -0.038, -0.05), Vector3(0.19, 0.12, 0.25)' in pawn
assert 'global_position = Vector3(world_x, base_y + SPAWN_CLEARANCE_M, world_z)' in pawn
assert 'SPAWN_CLEARANCE_M := 0.20' in pawn
assert 'pawn.set_movement_camera(camera)' in lab
assert '_teleport_to_lane(0)' in lab
assert 'pawn.call("reset_at",float(0-2)*8.5,0.0,9.3,0)' not in lab
for deg in (0,45,90,180,270):
    rad=math.radians(deg)
    forward=(-math.sin(rad),-math.cos(rad))
    right=(math.cos(rad),-math.sin(rad))
    assert abs(forward[0]*right[0]+forward[1]*right[1])<1e-8
    assert abs(math.hypot(*forward)-1)<1e-8
    assert abs(math.hypot(*right)-1)<1e-8
print("CHERPG_CAMERA_SPAWN_STATIC_OK (NOT A PLAYTEST)")
