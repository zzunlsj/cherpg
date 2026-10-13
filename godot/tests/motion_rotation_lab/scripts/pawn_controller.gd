extends CharacterBody3D
## A separate Godot implementation of the retained primitive-only 1.55 m Pawn.
## Deliberately uses no sculpted face, textures or reworked hero silhouette.
# Adapted from the user-provided Unity Rigidbody2D pawn_player.cs.
# Only the heading axis is kept: this is a chess Pawn, not free 4-way strafing.
# Source input smoothing: Mathf.MoveTowards(current, raw, delta * 10).
# Source speed caps: 4.0 walk; 4.0 * 1.5 = 6.0 sprint.
# Source force model: force=20000, sprint x2, strong release braking.
# Unity's AddForce(force * fixedDeltaTime) uses an EXTRA timestep; direct
# numeric port to CharacterBody3D would be mass/step dependent. Expose an
# intentionally calibrated acceleration instead, preserving the response shape.
const INPUT_SMOOTHING_PER_SEC := 10.0
const WALK_MPS := 4.0
const RUN_MPS := 6.0
const SOURCE_MAX_FORCE := 20000.0
const SOURCE_SPRINT_FORCE_MULT := 2.0
const SOURCE_STOP_FRICTION := 0.5
const SOURCE_MOVE_FRICTION := 0.3
const SOURCE_MIN_SPEED := 0.1
const SOURCE_MIN_FORCE := 0.1
const GROUND_PUSH_ACCEL := 38.0    # m/s² calibrated, not 1:1 Newton translation
const GROUND_RELEASE_BRAKE := 56.0 # replicates strong -velocity.normalized*maxForce
const AIR_PUSH_ACCEL := 7.0
const AIR_BRAKE := 3.5
const GRAVITY := 18.0
const COYOTE_SECONDS := 0.115    # jump just after losing the edge
const JUMP_BUFFER_SECONDS := 0.135 # retain jump pressed before touching ground
const JUMP_VELOCITY := 6.25      # calculated vertical impulse (separate from 2D locomotion)
const JUMP_RELEASE_GRAVITY_MULT := 2.35 # early release => shorter hop
const FALL_GRAVITY_MULT := 1.20
const MAX_UPWARD_SPEED := 7.0
const HEADING_NAMES := ["NORTH / -Z", "EAST / +X", "SOUTH / +Z", "WEST / -X"]
const HEADINGS := [Vector3.FORWARD, Vector3.RIGHT, Vector3.BACK, Vector3.LEFT]
var heading_index := 0
var lane_index := 0
var move_state := "IDLE"
var floor_deg := 0.0
var slope_sign := 0.0
var gait_clock := 0.0
var smoothed_input := 0.0
var latest_axis := 0.0
var latest_sprint := false
var jump_buffer_left := 0.0
var coyote_left := 0.0
var jump_key_down := false
var jump_count := 0
var airborne_time := 0.0
var landing_visual := 0.0
var takeoff_visual := 0.0
var jump_state := "GROUNDED"
var ground_normal := Vector3.UP
var device: Node3D
var avatar: Node3D
var upper_leg: Array[Node3D] = []
var knee: Array[Node3D] = []
var shoulder: Array[Node3D] = []
var feet: Array[Node3D] = []
var stone: StandardMaterial3D
var ivory: StandardMaterial3D
var iron: StandardMaterial3D
var dark: StandardMaterial3D

func _ready() -> void:
	name = "PawnCharacterBody"
	collision_layer = 2
	collision_mask = 1
	floor_snap_length = 0.24
	floor_max_angle = deg_to_rad(36.0)
	floor_stop_on_slope = true
	var capsule := CapsuleShape3D.new()
	capsule.radius = 0.235
	capsule.height = 1.43
	var collider := CollisionShape3D.new()
	collider.name = "PawnCollisionCapsule"
	collider.shape = capsule
	collider.position.y = 0.765
	add_child(collider)
	stone = _mat(Color("b5b4ab"), 0.0)
	ivory = _mat(Color("e2dac7"), 0.0)
	iron = _mat(Color("444c53"), 0.45)
	dark = _mat(Color("77736c"), 0.1)
	avatar = Node3D.new()
	avatar.name = "PrimitivePawnVisual"
	add_child(avatar)
	_build_primitive_body()
	device = preload("res://scripts/direction_device.gd").new()
	device.name = "FourAnchorWaistDevice"
	add_child(device)
	device.call("bind_pawn", self)

func _mat(color: Color, metal: float) -> StandardMaterial3D:
	var m := StandardMaterial3D.new()
	m.albedo_color = color
	m.metallic = metal
	m.roughness = 0.83
	return m

func _box(parent: Node3D, title: String, center: Vector3, size: Vector3, mat: Material) -> MeshInstance3D:
	var mi := MeshInstance3D.new()
	mi.name = title
	var mesh := BoxMesh.new()
	mesh.size = size
	mi.mesh = mesh
	mi.material_override = mat
	parent.add_child(mi)
	mi.position = center
	return mi

func _ball(parent: Node3D, title: String, center: Vector3, radius: Vector3, mat: Material) -> MeshInstance3D:
	var mi := MeshInstance3D.new()
	mi.name = title
	var mesh := SphereMesh.new()
	mesh.radius = 1.0
	mesh.height = 2.0
	mesh.radial_segments = 10
	mesh.rings = 5
	mi.mesh = mesh
	mi.material_override = mat
	parent.add_child(mi)
	mi.position = center
	mi.scale = radius
	return mi

func _rod(parent: Node3D, title: String, start: Vector3, finish: Vector3, radius: float, mat: Material) -> MeshInstance3D:
	var mi := MeshInstance3D.new()
	mi.name = title
	var mesh := CylinderMesh.new()
	mesh.top_radius = radius
	mesh.bottom_radius = radius
	mesh.height = 1.0
	mesh.radial_segments = 8
	mi.mesh = mesh
	mi.material_override = mat
	parent.add_child(mi)
	mi.position = (start + finish) * 0.5
	mi.scale.y = start.distance_to(finish)
	mi.quaternion = Quaternion(Vector3.UP, (finish - start).normalized())
	return mi

func _build_primitive_body() -> void:
	_box(avatar, "BODY_Pelvis", Vector3(0, 0.67, 0), Vector3(0.395, 0.194, 0.258), dark)
	_box(avatar, "BODY_Torso", Vector3(0, 0.902, 0), Vector3(0.462, 0.349, 0.282), stone)
	_box(avatar, "BODY_UpperChest", Vector3(0, 1.075, 0), Vector3(0.482, 0.105, 0.299), stone)
	_rod(avatar, "BODY_Neck", Vector3(0, 1.111, 0), Vector3(0, 1.184, 0), 0.065, iron)
	for sign in [-1.0, 1.0]:
		var side := "L" if sign < 0.0 else "R"
		var hip := Node3D.new()
		hip.name = "RIG_" + side + "_HipPivot"
		avatar.add_child(hip)
		hip.position = Vector3(sign * 0.103, 0.665, 0)
		upper_leg.append(hip)
		_rod(hip, "BODY_" + side + "_Thigh", Vector3(sign * 0.015, -0.018, 0), Vector3(sign * 0.015, -0.208, 0), 0.086, stone)
		var joint := Node3D.new()
		joint.name = "RIG_" + side + "_KneePivot"
		hip.add_child(joint)
		joint.position = Vector3(sign * 0.015, -0.242, 0)
		knee.append(joint)
		_ball(joint, "BODY_" + side + "_Knee", Vector3.ZERO, Vector3(0.085, 0.08, 0.09), dark)
		_rod(joint, "BODY_" + side + "_Shin", Vector3(0, -0.04, 0), Vector3(0, -0.285, 0), 0.07, iron)
		var foot := Node3D.new()
		foot.name = "RIG_" + side + "_FootPivot"
		joint.add_child(foot)
		foot.position = Vector3(0, -0.325, 0)
		feet.append(foot)
		_box(foot, "BODY_" + side + "_Foot", Vector3(0, -0.006, -0.05), Vector3(0.19, 0.12, 0.25), dark)
		var arm := Node3D.new()
		arm.name = "RIG_" + side + "_ShoulderPivot"
		avatar.add_child(arm)
		arm.position = Vector3(sign * 0.29, 1.055, 0)
		shoulder.append(arm)
		_ball(arm, "BODY_" + side + "_Shoulder", Vector3.ZERO, Vector3(.105,.095,.11), dark)
		_rod(arm, "BODY_" + side + "_UpperArm", Vector3(sign*.02,-.04,0), Vector3(sign*.065,-.22,0), .067, stone)
		_ball(arm, "BODY_" + side + "_Elbow", Vector3(sign*.066,-.245,0), Vector3(.058,.064,.064), iron)
		_rod(arm, "BODY_" + side + "_Forearm", Vector3(sign*.066,-.255,0), Vector3(sign*.105,-.47,0), .063, stone)
		_box(arm, "BODY_" + side + "_MalletHand", Vector3(sign*.108,-.52,0), Vector3(.108,.14,.103), dark)
	_ball(avatar,"HEAD_Face_Blank",Vector3(0,1.212,0),Vector3(.146,.14,.134),ivory)
	_ball(avatar,"HEAD_HairCap_Basic",Vector3(0,1.334,0),Vector3(.158,.05,.143),stone)
	# No eyes, nose, mouth or detailed sculpting at this blockout stage.
	var lower_band := _box(avatar,"HEAD_Helmet_Band",Vector3(0,1.392,0),Vector3(.37,.07,.33),ivory)
	lower_band.rotation.y = deg_to_rad(0.0)
	_box(avatar,"HEAD_Helmet_Crown",Vector3(0,1.439,0),Vector3(.235,.055,.22),ivory)
	_ball(avatar,"HEAD_PawnOrb",Vector3(0,1.515,0),Vector3(.035,.035,.035),ivory)

# Jump input is independent from the horizontal movement source/axis.
# It is called by MotionLab on KEY_SPACE down; release_jump on KEY_SPACE up.
func queue_jump() -> void:
	jump_key_down = true
	jump_buffer_left = JUMP_BUFFER_SECONDS

func release_jump() -> void:
	jump_key_down = false

func _horizontal_velocity() -> Vector3:
	return Vector3(velocity.x, 0.0, velocity.z)

## Independent testable planar physics adapter for the Unity movement feel.
## Godot move_and_slide() will handle final collider response after this update.
func _source_feel_horizontal(current: Vector3, axis: float, sprint: bool, delta: float, floor: bool, slope_multiplier: float) -> Vector3:
	var speed_cap: float = (RUN_MPS if sprint else WALK_MPS) * slope_multiplier
	var intended: Vector3 = HEADINGS[heading_index] * axis
	var magnitude: float = absf(axis)
	var push: float = GROUND_PUSH_ACCEL if floor else AIR_PUSH_ACCEL
	if sprint:
		push *= SOURCE_SPRINT_FORCE_MULT
	var braking: float = GROUND_RELEASE_BRAKE if floor else AIR_BRAKE
	var current_speed: float = current.length()
	var next: Vector3 = current
	if magnitude < SOURCE_MIN_FORCE:
		# Match the C# extra braking force on release (not linear drag only).
		next = current.move_toward(Vector3.ZERO, braking * delta)
	elif current_speed <= SOURCE_MIN_SPEED:
		# Source uses static friction before the movement threshold.
		var step: float = maxf(0.0, magnitude * push - SOURCE_STOP_FRICTION) * delta
		next = current + intended.normalized() * step
	else:
		# Driving force minus velocity-aligned kinetic drag.
		var acceleration: Vector3 = intended * push - current.normalized() * SOURCE_MOVE_FRICTION
		next = current + acceleration * delta
	# Velocity clipping corresponds to the C# Rigidbody2D speed-cap branches.
	if next.length() > speed_cap:
		next = next.normalized() * speed_cap
	if magnitude < SOURCE_MIN_FORCE and next.length() < SOURCE_MIN_SPEED:
		next = Vector3.ZERO
	return next

func _physics_process(delta: float) -> void:
	var was_on_floor: bool = is_on_floor()
	var fwd: float = float(Input.is_key_pressed(KEY_W) or Input.is_key_pressed(KEY_UP))
	var back: float = float(Input.is_key_pressed(KEY_S) or Input.is_key_pressed(KEY_DOWN))
	var raw_axis: float = fwd - back
	var device_busy: bool = bool(device.call("is_busy"))
	if device_busy:
		raw_axis = 0.0
	smoothed_input = move_toward(smoothed_input, raw_axis, INPUT_SMOOTHING_PER_SEC * delta)
	var axis: float = smoothed_input
	# Grounding operation must immobilize the pawn even while input decays.
	if device_busy:
		axis = 0.0
	var wants_run: bool = Input.is_key_pressed(KEY_SHIFT) and not is_zero_approx(raw_axis)
	latest_axis = axis
	latest_sprint = wants_run
	var direction: Vector3 = HEADINGS[heading_index] * signf(axis)

	if was_on_floor:
		ground_normal = get_floor_normal()
		floor_deg = rad_to_deg(get_floor_angle())
		coyote_left = COYOTE_SECONDS
		if jump_state != "GROUNDED":
			landing_visual = 1.0
		jump_state = "GROUNDED"
		airborne_time = 0.0
	else:
		coyote_left = maxf(0.0, coyote_left-delta)
		airborne_time += delta
		jump_state = "RISING" if velocity.y > 0.0 else "FALLING"

	jump_buffer_left = maxf(0.0, jump_buffer_left-delta)
	# Device and jump are mutually exclusive; jump is not a direction-change skill.
	if jump_buffer_left > 0.0 and coyote_left > 0.0 and not device_busy:
		velocity.y = JUMP_VELOCITY
		jump_buffer_left = 0.0
		coyote_left = 0.0
		jump_count += 1
		jump_state = "RISING"
		takeoff_visual = 1.0
		was_on_floor = false

	if not was_on_floor:
		var grav_mult: float = FALL_GRAVITY_MULT if velocity.y < 0.0 else (JUMP_RELEASE_GRAVITY_MULT if not jump_key_down else 1.0)
		velocity.y -= GRAVITY * grav_mult * delta
	elif velocity.y <= 0.0:
		velocity.y = -0.4

	var uphill: float = -ground_normal.dot(direction) if was_on_floor else 0.0
	slope_sign = uphill
	# Terrain changes only speed cap, not the original input ramp/brake shape.
	var slope_factor: float = 1.0-clampf(uphill*0.65,-0.10,0.26)
	var current_horizontal: Vector3 = _horizontal_velocity()
	var next_horizontal := _source_feel_horizontal(current_horizontal, axis, wants_run, delta, was_on_floor, slope_factor)
	# Release safely to a stop on a grounded, locked direction device.
	if device_busy:
		next_horizontal = Vector3.ZERO
	velocity.x = next_horizontal.x
	velocity.z = next_horizontal.z
	move_and_slide()
	# Resolve landing on the current physics tick, not only on the next tick.
	if is_on_floor() and jump_state != "GROUNDED":
		if airborne_time > 0.055:
			landing_visual = 1.0
		jump_state = "GROUNDED"
	if not is_on_floor():
		move_state = "JUMP" if velocity.y > 0.05 else "FALL"
	elif _horizontal_velocity().length() < 0.12 and absf(axis) < SOURCE_MIN_FORCE:
		move_state = "IDLE"
	elif wants_run:
		move_state = "RUN"
	else:
		move_state = "WALK"

	var horizontal_speed: float = Vector2(get_real_velocity().x,get_real_velocity().z).length()
	if is_on_floor():
		_update_gait(delta,horizontal_speed,wants_run,axis)
	else:
		_update_air_pose(delta)
	landing_visual = maxf(0.0,landing_visual-delta*6.0)
	takeoff_visual = maxf(0.0,takeoff_visual-delta*9.0)

func _update_air_pose(delta: float) -> void:
	# Separate primitive-joint animation: tucked ascent, extended descent.
	var rising: bool = velocity.y >= 0.0
	for i in range(2):
		var target_hip: float = (0.36 if i == 0 else -0.21) if rising else (-0.13 if i == 0 else 0.09)
		var target_knee: float = (0.37 if rising else 0.16)
		upper_leg[i].rotation.x = lerpf(upper_leg[i].rotation.x,target_hip,minf(1.0,delta*10.5))
		knee[i].rotation.x = lerpf(knee[i].rotation.x,target_knee,minf(1.0,delta*11.0))
		shoulder[i].rotation.x = lerpf(shoulder[i].rotation.x,(-0.26 if rising else 0.12),minf(1.0,delta*10.0))
		feet[i].rotation.x = lerpf(feet[i].rotation.x,(-0.20 if rising else 0.10),minf(1.0,delta*10.0))
	avatar.rotation.x = lerpf(avatar.rotation.x,(-0.045 if rising else 0.025),minf(1.0,delta*6.0))
	avatar.position.y = lerpf(avatar.position.y,0.0,minf(1.0,delta*9.0))

func _update_gait(delta: float, horizontal_speed: float, running: bool, axis: float) -> void:
	var moving := minf(horizontal_speed / WALK_MPS, 1.4)
	if absf(axis) > 0.1 and is_on_floor():
		gait_clock += horizontal_speed * delta * (2.4 if running else 2.1)
	var fade := clampf(moving, 0.0, 1.0) if absf(axis) > 0.01 else 0.0
	var amplitude := (0.57 if running else 0.35) * fade
	var swing := sin(gait_clock)
	var slope_ratio := clampf(floor_deg / 25.0, 0.0, 1.0)
	for i in range(2):
		var phase_swing := swing if i == 0 else -swing
		upper_leg[i].rotation.x = lerpf(upper_leg[i].rotation.x, phase_swing * amplitude, minf(1.0,delta * 13.0))
		var knee_lift := maxf(0.0, -phase_swing) * (0.38 if running else 0.20)
		knee_lift += maxf(0.0, slope_sign) * slope_ratio * 0.23
		knee[i].rotation.x = lerpf(knee[i].rotation.x, knee_lift * fade, minf(1.0,delta * 11.0))
		shoulder[i].rotation.x = lerpf(shoulder[i].rotation.x, -phase_swing * amplitude * .75, minf(1.0,delta * 10.0))
		feet[i].rotation.x = lerpf(feet[i].rotation.x, -knee[i].rotation.x * .3, minf(1.0,delta * 10.0))
	var climb_lean := clampf(slope_sign * 0.24, -0.09, 0.11)
	avatar.rotation.x = lerpf(avatar.rotation.x, climb_lean, minf(1.0,delta * 7.0))
	var bounce := absf(sin(gait_clock * 2.0)) * (0.016 if running else 0.008) * fade
	# Landing compression and takeoff stretch affect posture, never the collision body.
	var squat: float = -0.055*landing_visual + 0.025*takeoff_visual
	avatar.position.y = lerpf(avatar.position.y,bounce+squat,minf(1.0,delta*12.0))

func reset_at(world_x: float, base_y: float, world_z: float, index: int) -> void:
	global_position = Vector3(world_x, base_y + 0.12, world_z)
	velocity = Vector3.ZERO
	lane_index = index
	gait_clock = 0.0
	smoothed_input = 0.0
	latest_axis = 0.0
	latest_sprint = false
	jump_buffer_left = 0.0
	coyote_left = 0.0
	jump_key_down = false
	airborne_time = 0.0
	landing_visual = 0.0
	takeoff_visual = 0.0
	jump_state = "GROUNDED"
	for group in upper_leg + knee + shoulder + feet:
		group.rotation = Vector3.ZERO
	avatar.position = Vector3.ZERO
	avatar.rotation = Vector3.ZERO
	device.call("instant_stow")
