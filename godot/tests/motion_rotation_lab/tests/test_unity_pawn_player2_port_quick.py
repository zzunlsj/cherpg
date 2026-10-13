"""Sub-second C# pawn_player(2).cs -> GDScript contract checks. NO playtest."""
from pathlib import Path
from math import hypot, isclose
root=Path(__file__).resolve().parents[1]
pawn=(root/"scripts/pawn_controller.gd").read_text(encoding="utf-8")
lab=(root/"scripts/motion_lab.gd").read_text(encoding="utf-8")
tokens=(
    "func _process(delta: float) -> void:",
    "INPUT_SMOOTHING_PER_SEC := 10.0",
    "smoothed_input = move_toward(smoothed_input,target_y,delta * INPUT_SMOOTHING_PER_SEC)",
    "smoothed_strafe = move_toward(smoothed_strafe,target_x,delta * INPUT_SMOOTHING_PER_SEC)",
    "func _source_feel_horizontal(current: Vector3, input_vector: Vector2, is_sprint: bool, delta: float)",
    "SOURCE_MAX_FORCE := 20000.0",
    "SOURCE_SPRINT_FORCE_MULT := 2.0",
    "SOURCE_STOP_FRICTION := 0.5",
    "SOURCE_MOVE_FRICTION := 0.3",
    "SOURCE_MIN_SPEED := 0.1",
    "SOURCE_MIN_FORCE := 0.1",
    "source_rigidbody_mass := 1.0",
    "source_rigidbody_gravity_scale := 1.0",
    "static_push: float = maxf(input_magnitude * SOURCE_MAX_FORCE - mass * gravity_scale * SOURCE_STOP_FRICTION,0.0)",
    "force = source_fixed_input_vec * SOURCE_MAX_FORCE",
    "force -= planar_velocity.normalized() * SOURCE_MAX_FORCE",
    "if force.length() < SOURCE_MIN_FORCE:",
    "planar_velocity = Vector2.ZERO",
    "force *= SOURCE_SPRINT_FORCE_MULT",
    "planar_velocity += force * (delta * delta / mass)",
    "var cap: float = WALK_MPS * (1.5 if is_sprint else 1.0)",
    "return Vector3(planar_velocity.x,0.0,planar_velocity.y)",
    "source_anim_speed = horizontal_speed",
    "attack_timer = ATTACK_POSE_SECONDS",
    "Input.is_key_pressed(KEY_CTRL)",
    "Input.is_key_pressed(KEY_SHIFT)",
    "next_horizontal := _source_feel_horizontal(current_horizontal, input_vector, running, delta)",
)
for t in tokens: assert t in pawn, t
assert '"is_busy"' in pawn
assert "pawn.trigger_attack()" in lab and "MOUSE_BUTTON_LEFT" in lab
assert '"if force.length()" not in pawn'  # avoid quoted / dead-code force branch
# Pure-Python reference for exactly the source's planar force update.
def reference_step(v, inp, sprint=False, dt=1/60, mass=1., gravity_scale=1., crouch=False):
    inp_mag = hypot(*inp)
    if inp_mag > 1:
        inp=(inp[0]/inp_mag,inp[1]/inp_mag)
        inp_mag=1.
    speed=hypot(*v)
    unit=lambda a: (a[0]/hypot(*a),a[1]/hypot(*a)) if hypot(*a) else (0.,0.)
    if speed<=0.1:
        static=max(inp_mag*20000-mass*gravity_scale*0.5,0.)
        force=tuple(d*static for d in unit(inp))
        if inp_mag<0.1: force=(0.,0.)
    else:
        u=unit(v)
        force=tuple(inp[i]*20000-u[i]*mass*gravity_scale*.3 for i in (0,1))
        if inp_mag<0.1:
            force=tuple(force[i]-u[i]*20000 for i in (0,1))
    if hypot(*force)<.1:
        force=(0.,0.);v=(0.,0.)
    elif sprint:
        force=tuple(f*2 for f in force)
    if hypot(*force)>=.1:
        v=tuple(v[i]+force[i]*dt*dt/mass for i in (0,1))
    cap=min((6. if sprint else 4.),1.8) if crouch else (6. if sprint else 4.)
    size=hypot(*v)
    if size>cap: v=tuple(n*cap/size for n in v)
    return v
assert reference_step((0.,0.),(0.,0.))==(0.,0.)
assert reference_step((0.,0.),(0.,1.))==(0.,4.)
assert reference_step((0.,0.),(0.,1.),sprint=True)==(0.,6.)
assert isclose(hypot(*reference_step((0.,0.),(1.,1.))),4.)
assert hypot(*reference_step((0.,0.),(0.,1.),crouch=True))<=1.8
assert reference_step((0.,0.),(0.,1.),sprint=True,crouch=True)==(0.,1.8)
assert reference_step((0.06,0.),(0.,0.))==(0.,0.)
print("CHERPG_UNITY_PAWN_PLAYER2_FORCE_PORT_STATIC_OK (NOT A PLAYTEST)")
