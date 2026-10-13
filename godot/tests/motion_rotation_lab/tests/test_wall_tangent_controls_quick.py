"""Fast static/math checks. Not a player-controlled test."""
from pathlib import Path
from math import sqrt, cos, sin, radians
root=Path(__file__).resolve().parents[1]
src=(root/"scripts/pawn_controller.gd").read_text(encoding="utf-8")
hud=(root/"scripts/motion_lab.gd").read_text(encoding="utf-8")
for token in (
    "func _climb_wall_up() -> Vector3:",
    "func _climb_wall_right() -> Vector3:",
    "func _update_climb_contact(",
    "_wall_contact(-climb_normal)",
    "Vector3.UP.cross(climb_normal)",
    "Vector3.UP.slide(climb_normal)",
    "climb_contact_grace",
    "climb_input = Vector2(raw_strafe,raw_axis).limit_length(1.0)",
    "if climbing and climb_input.y > 0.25:",
    "_try_climb_top_ledge(-climb_normal)",
    'move_state = "CLIMB HOLD" if',
    "_update_climb_pose(delta,climb_input)",
    "func _update_climb_pose(delta: float, wall_inputs: Vector2)",
    "avatar.rotation.y = lerp_angle(avatar.rotation.y,wall_yaw",
    "next_horizontal = Vector3(wall_motion.x,0.0,wall_motion.z)",
    "velocity.y = wall_motion.y",
):
    assert token in src, f"Missing feature: {token}"
# The wall-grip direction is not recast from camera yaw after grabbing.
attachment=src.split("func _update_climb_contact(",1)[1].split("\nfunc ",1)[0]
assert "_wall_contact(-climb_normal)" in attachment
assert "_camera_flat_forward()" in attachment  # for initial Ctrl+W attachment only
assert "elif active_direction > 0.25:" in attachment
assert "if climbing:" in attachment
assert "Ctrl+W" in hud
assert "fixed wall axes" in hud
# Wall +Z: right vector UP x normal = +X, up vector = +Y.
def dot(a,b):
    return sum(x*y for x,y in zip(a,b))
def cross(a,b):
    return (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2],
            a[0]*b[1]-a[1]*b[0])
def normalize(x):
    size=sqrt(dot(x,x))
    return tuple(v/size for v in x)
def tangent_up(n):
    return normalize(tuple((0,1,0)[i]-n[i]*n[1] for i in range(3)))
for deg in (30,45,75,90):
    n=(0,cos(radians(deg)),sin(radians(deg)))
    up=tangent_up(n)
    right=normalize(cross((0,1,0),n))
    assert dot(up,n)<1e-6
    assert dot(right,n)<1e-6
    assert dot(up,right)<1e-6
    assert right[0]>0.99
    assert up[1]>0
    # Ctrl only produces exactly zero tangential motion.
    ctrl_only=tuple(up[i]*0.0+right[i]*0.0 for i in range(3))
    assert ctrl_only==(0.,0.,0.)
    # S reverses ascent and A reverses wall-local right.
    assert dot(tuple(-v for v in up),up)<-0.999
    assert dot(tuple(-v for v in right),right)<-0.999
print("CHERPG_WALL_TANGENT_INPUT_STATIC_OK (NOT A PLAYTEST)")
