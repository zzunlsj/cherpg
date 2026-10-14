"""Fast contract: every visual part is rigid through all animation states."""
from pathlib import Path
import re

root=Path(__file__).resolve().parents[1]
pawn=(root/"scripts/pawn_controller.gd").read_text(encoding="utf-8")
device=(root/"scripts/direction_device.gd").read_text(encoding="utf-8")

# A mesh may have initial authoring dimensions, but no runtime animation
# function may change MeshInstance3D.scale or a Mesh primitive's size.
def functions(text):
    sections=re.split(r"(?=^func )",text,flags=re.M)
    for part in sections:
        if part.startswith("func "):
            yield part.split("(",1)[0].split()[1],part

for name,fn in list(functions(pawn))+list(functions(device)):
    if name not in ("_box","_ball","_rod","_make_box","_make_torus","_make_cylinder"):
        assert not re.search(r"\b(?:avatar|upper_body_pivot|opening_ring|heading_pivot|rail|upper|lower|tip|collar|shoe)\.scale\s*=",fn),name
        assert not re.search(r"\b(?:avatar|opening_ring|rail|upper|lower|tip|collar|shoe)\.scale\.[xyz]\s*=",fn),name

assert "avatar.scale.y = lerpf(" not in pawn
assert "upper_body_pivot = Node3D.new()" in pawn
assert "func _install_upper_body_pivot()" in pawn
assert 'child.name.ends_with("_ShoulderPivot")' in pawn
assert "upper_body_pivot.rotation.x = lerpf(" in pawn
assert "avatar.position.y = lerpf(avatar.position.y,-0.22*crouch_blend,blend)" in pawn
assert "joints.append(upper_body_pivot)" in pawn
assert "upper_body_pivot.rotation.x = clampf(" in pawn
assert "func _sync_device_to_rigid_waist(" in pawn
for entry in ("_update_gait","_update_air_pose","_update_crouch_pose",
              "_update_climb_pose","_update_mantle_pose","_apply_attack_pose"):
    assert f"func {entry}(" in pawn
assert "var stowed_ring: MeshInstance3D" in device
assert "var opening_ring: MeshInstance3D" in device
assert "CollapsedRigidWaistRing" in device
assert "DeployedRigidWaistRing" in device
assert "ANCHOR_SLIDING_TIP_" in device
assert "upper.visible = anchor_frac >" in device
assert "tip.position = Vector3(" in device
assert "shoe.quaternion = Quaternion.IDENTITY.slerp" in device
print("CHERPG_RIGID_ANIMATION_NO_RUNTIME_SCALE_SOURCE_OK")
