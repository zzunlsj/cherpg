extends CharacterBody3D
## A separate Godot implementation of the retained primitive-only 1.55 m Pawn.
## Deliberately uses no sculpted face, textures or reworked hero silhouette.
# Adapted from the user-provided Unity Rigidbody2D pawn_player.cs.
# The Pawn moves freely inside a tile; voluntary crossing obeys chess heading.
# Source input smoothing: Mathf.MoveTowards(current, raw, delta * 10).
# Source speed caps: 4.0 walk; 4.0 * 1.5 = 6.0 sprint.
# Source force model: force=20000, sprint x2, strong release braking.
# Unity's AddForce(force * fixedDeltaTime) uses an EXTRA timestep; direct
# numeric port to CharacterBody3D would be mass/step dependent. Expose an
# intentionally calibrated acceleration instead, preserving the response shape.
const BOARD_RULES = preload("res://scripts/board_rules.gd")
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
# Pawn root at ground level; spawn starts above the sampled surface.
const SPAWN_CLEARANCE_M := 0.20
const COYOTE_SECONDS := 0.115    # jump just after losing the edge
const JUMP_BUFFER_SECONDS := 0.135 # retain jump pressed before touching ground
const JUMP_VELOCITY := 6.25      # calculated vertical impulse (separate from 2D locomotion)
const JUMP_RELEASE_GRAVITY_MULT := 2.35 # early release => shorter hop
const FALL_GRAVITY_MULT := 1.20
const MAX_UPWARD_SPEED := 7.0
const MAX_ASCENT_ANGLE_DEG := 90.0
const NORMAL_FLOOR_CUTOFF_DEG := 89.9  # wall at 90 uses contact climbing
const WALL_CLIMB_MPS := 2.5
const DASH_SPEED_MPS := 10.5
const DASH_SECONDS := 0.20
const DASH_COOLDOWN_SECONDS := 0.85
const HEADING_NAMES := ["NORTH / -Z", "EAST / +X", "SOUTH / +Z", "WEST / -X"]
const HEADINGS := [Vector3.FORWARD, Vector3.RIGHT, Vector3.BACK, Vector3.LEFT]
var heading_index := 0
var lane_index := 0
var move_state := "IDLE"
var floor_deg := 0.0
var slope_sign := 0.0
var gait_clock := 0.0
var run_blend := 0.0
var attack_timer := 0.0
const ATTACK_POSE_SECONDS := 0.36
var smoothed_input := 0.0
var smoothed_strafe := 0.0
var board_origin: Vector3 = Vector3.ZERO
var current_cell: Vector2i = Vector2i.ZERO
var resistance_time := 0.0
var resistance_attempts := 0
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
var dash_timer := 0.0
var dash_cooldown := 0.0
var dash_direction := Vector3.FORWARD
var climbing := false
var climb_normal := Vector3.ZERO
var ground_normal := Vector3.UP
var device: Node3D
var movement_camera: Camera3D
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
	floor_max_angle = deg_to_rad(NORMAL_FLOOR_CUTOFF_DEG)
	floor_stop_on_slope = true
	var capsule := CapsuleShape3D.new()
	capsule.radius = 0.235
	capsule.height = 1.43
	var collider := CollisionShape3D.new()
	collider.name = "PawnCollisionCapsule"
	collider.shape = capsule
	collider.position.y = capsule.height * 0.5 # capsule bottom aligns with character root
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
		_box(foot, "BODY_" + side + "_Foot", Vector3(0, -0.038, -0.05), Vector3(0.19, 0.12, 0.25), dark)
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

func queue_dash() -> void:
	if dash_cooldown > 0.0 or dash_timer > 0.0 or not is_on_floor():
		return
	if device != null and bool(device.call("is_busy")):
		return
	var input_dir := Vector2(smoothed_strafe, smoothed_input).limit_length(1.0)
	if input_dir.length() < 0.12:
		input_dir = Vector2(0.0,1.0)
	var fwd := _camera_flat_forward()
	dash_direction = (fwd * input_dir.y + fwd.cross(Vector3.UP) * input_dir.x).normalized()
	if dash_direction.length_squared() < 0.01:
		return
	dash_timer = DASH_SECONDS
	dash_cooldown = DASH_COOLDOWN_SECONDS

func _wall_contact(camera_forward: Vector3) -> Dictionary:
	# A true 90° wall does not count as a floor in CharacterBody3D.
	# Near vertical surfaces receive a separate W-to-climb adhesion velocity.
	var cast_from: Vector3 = global_position + Vector3.UP * 0.55
	var cast_to: Vector3 = cast_from + camera_forward * 0.87
	var ray := PhysicsRayQueryParameters3D.create(cast_from,cast_to,1,[get_rid()])
	var hit: Dictionary = get_world_3d().direct_space_state.intersect_ray(ray)
	if hit.is_empty():
		return {}
	var n: Vector3 = hit["normal"]
	if absf(n.y) > 0.12 or -camera_forward.dot(n) < .72:
		return {}
	return hit

func _try_climb_top_ledge(forward: Vector3) -> void:
	# The 90° test wall has a solid landing deck at y=3m. Transfer onto it
	# once the feet are near the top. Still obey voluntary board step limits.
	if not climbing:
		return
	var ray_start: Vector3 = global_position + Vector3.UP*1.7 + forward*1.0
	var ray_end: Vector3 = ray_start + Vector3.DOWN*2.8
	var query := PhysicsRayQueryParameters3D.create(ray_start,ray_end,1,[get_rid()])
	var hit: Dictionary = get_world_3d().direct_space_state.intersect_ray(query)
	if hit.is_empty():
		return
	var normal: Vector3 = hit["normal"]
	var roof_y: float = hit["position"].y
	var remaining: float = roof_y - global_position.y
	if normal.y < .88 or roof_y < 1.0 or remaining > .50 or remaining < -.12:
		return
	var landing: Vector3 = global_position + forward * 1.08
	landing.y = roof_y + 0.055
	var permitted: Dictionary = BOARD_RULES.constrain_voluntary(global_position,landing,board_origin,heading_index)
	if bool(permitted["resisted"]):
		return
	global_position = permitted["position"]
	velocity = Vector3.ZERO
	climbing = false
	jump_state = "GROUNDED"

func trigger_attack() -> void:
	# Unity source: ResetTrigger("attack"), then SetTrigger("attack").
	# Placeholder arm motion; no combat hitbox or damage is invented.
	if device != null and bool(device.call("is_busy")):
		return
	attack_timer = ATTACK_POSE_SECONDS

func set_movement_camera(source: Camera3D) -> void:
	movement_camera = source

func _camera_flat_forward() -> Vector3:
	# Forward input always uses camera view projected onto the XZ plane.
	# Never use chess-rule heading or camera pitch to steer the input.
	if is_instance_valid(movement_camera):
		var horizontal: Vector3 = -movement_camera.global_transform.basis.z
		horizontal.y = 0.0
		if horizontal.length_squared() > 0.0001:
			return horizontal.normalized()
	return Vector3.FORWARD

func _horizontal_velocity() -> Vector3:
	return Vector3(velocity.x, 0.0, velocity.z)

## Independent testable planar physics adapter for the Unity movement feel.
## Godot move_and_slide() will handle final collider response after this update.
func _source_feel_horizontal(current: Vector3, input_vector: Vector2, sprint: bool, delta: float, floor: bool, slope_multiplier: float) -> Vector3:
	var speed_cap: float = (RUN_MPS if sprint else WALK_MPS) * slope_multiplier
	var forward: Vector3 = _camera_flat_forward()
	var right: Vector3 = forward.cross(Vector3.UP)
	var intended: Vector3 = (right * input_vector.x + forward * input_vector.y).limit_length(1.0)
	var magnitude: float = minf(1.0, input_vector.length())
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
	dash_cooldown = maxf(0.0,dash_cooldown-delta)
	dash_timer = maxf(0.0,dash_timer-delta)
	var was_on_floor: bool = is_on_floor()
	var fwd: float = float(Input.is_key_pressed(KEY_W) or Input.is_key_pressed(KEY_UP))
	var back: float = float(Input.is_key_pressed(KEY_S) or Input.is_key_pressed(KEY_DOWN))
	var left: float = float(Input.is_key_pressed(KEY_A) or Input.is_key_pressed(KEY_LEFT))
	var right: float = float(Input.is_key_pressed(KEY_D) or Input.is_key_pressed(KEY_RIGHT))
	var raw_axis: float = fwd - back
	var raw_strafe: float = right - left
	var device_busy: bool = bool(device.call("is_busy"))
	if device_busy:
		raw_axis = 0.0
		raw_strafe = 0.0
	smoothed_input = move_toward(smoothed_input, raw_axis, INPUT_SMOOTHING_PER_SEC * delta)
	smoothed_strafe = move_toward(smoothed_strafe, raw_strafe, INPUT_SMOOTHING_PER_SEC * delta)
	# Free bodily motion within a tile; tile crossing remains a world rule.
	var input_vector := Vector2(smoothed_strafe, smoothed_input).limit_length(1.0)
	if device_busy:
		input_vector = Vector2.ZERO
	var wants_run: bool = dash_timer > 0.0  # Shift is a short dash, never hold-to-sprint
	latest_axis = input_vector.y
	latest_sprint = wants_run
	var forward: Vector3 = _camera_flat_forward()
	var direction: Vector3 = (forward * input_vector.y + forward.cross(Vector3.UP) * input_vector.x).normalized()
	var contact: Dictionary = _wall_contact(forward) if raw_axis > 0.35 and not device_busy else {}
	climbing = not contact.is_empty() and (was_on_floor or climbing)
	if climbing:
		climb_normal = contact["normal"]
		dash_timer = 0.0

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

	if climbing:
		velocity.y = WALL_CLIMB_MPS
		jump_state = "CLIMBING"
	elif not was_on_floor:
		var grav_mult: float = FALL_GRAVITY_MULT if velocity.y < 0.0 else (JUMP_RELEASE_GRAVITY_MULT if not jump_key_down else 1.0)
		velocity.y -= GRAVITY * grav_mult * delta
	elif velocity.y <= 0.0:
		velocity.y = -0.4

	var uphill: float = -ground_normal.dot(direction) if was_on_floor else 0.0
	slope_sign = uphill
	# Terrain changes only speed cap, not the original input ramp/brake shape.
	var slope_factor: float = 1.0-clampf(uphill*0.65,-0.10,0.26)
	var current_horizontal: Vector3 = _horizontal_velocity()

	var next_horizontal := _source_feel_horizontal(current_horizontal, input_vector, false, delta, was_on_floor, slope_factor)
	if dash_timer > 0.0 and not device_busy:
		next_horizontal = dash_direction * DASH_SPEED_MPS
	if climbing:
		next_horizontal = -climb_normal * 0.18
	if device_busy:
		next_horizontal = Vector3.ZERO
	var starting_position: Vector3 = global_position
	var prediction: Dictionary = BOARD_RULES.constrain_voluntary(starting_position, starting_position + next_horizontal * delta, board_origin, heading_index)
	var projected_pos: Vector3 = prediction["position"]
	next_horizontal = (projected_pos - starting_position) / maxf(delta, 0.000001)
	velocity.x = next_horizontal.x
	velocity.z = next_horizontal.z
	move_and_slide()
	_try_climb_top_ledge(forward)
	# Physical collision resolution and airborne drift must obey the same rule.
	var resolved: Dictionary = BOARD_RULES.constrain_voluntary(starting_position, global_position, board_origin, heading_index)
	var allowed_position: Vector3 = resolved["position"]
	var resisted: bool = bool(prediction["resisted"]) or bool(resolved["resisted"])
	if bool(resolved["blocked_x"]):
		global_position.x = allowed_position.x
		velocity.x = 0.0
	if bool(resolved["blocked_z"]):
		global_position.z = allowed_position.z
		velocity.z = 0.0
	if resisted:
		resistance_time = 0.24
		resistance_attempts += 1
	else:
		resistance_time = maxf(0.0, resistance_time - delta)
	current_cell = BOARD_RULES.cell_at(global_position, board_origin)
	_update_body_facing(delta, _horizontal_velocity(), device_busy)

	# Resolve landing on the current physics tick, not only on the next tick.
	if is_on_floor() and jump_state != "GROUNDED":
		if airborne_time > 0.055:
			landing_visual = 1.0
		jump_state = "GROUNDED"
	if climbing:
		move_state = "CLIMB"
	elif dash_timer > 0.0 and is_on_floor():
		move_state = "DASH"
	elif not is_on_floor():
		move_state = "JUMP" if velocity.y > 0.05 else "FALL"
	elif _horizontal_velocity().length() < 0.12 and input_vector.length() < SOURCE_MIN_FORCE:
		move_state = "IDLE"
	elif wants_run:
		move_state = "RUN"
	else:
		move_state = "WALK"

	var horizontal_speed: float = Vector2(get_real_velocity().x,get_real_velocity().z).length()
	if climbing:
		_update_climb_pose(delta)
	elif is_on_floor():
		_update_gait(delta,horizontal_speed,wants_run,input_vector.length())
	else:
		_update_air_pose(delta)
	_apply_attack_pose(delta)
	landing_visual = maxf(0.0,landing_visual-delta*6.0)
	takeoff_visual = maxf(0.0,takeoff_visual-delta*9.0)

func _update_body_facing(delta: float, horizontal: Vector3, busy: bool) -> void:
	# Body yaw is physically free; chess heading_index is separate.
	if busy or horizontal.length() < 0.17:
		return
	var yaw: float = atan2(-horizontal.x, -horizontal.z)
	avatar.rotation.y = lerp_angle(avatar.rotation.y, yaw, minf(1.0, delta * 9.0))

func rotate_body_only(degrees: float) -> void:
	avatar.rotation.y += deg_to_rad(degrees)

func apply_forced_displacement(delta_world: Vector3) -> void:
	# External motion (knockback, traps) bypasses voluntary move restrictions.
	# Still collide with solids and do NOT change the chess heading.
	if delta_world.length_squared() <= 0.0:
		return
	move_and_collide(delta_world)
	current_cell = BOARD_RULES.cell_at(global_position, board_origin)

func _update_climb_pose(delta: float) -> void:
	# Deliberately exaggerated basic-joint motion on a true vertical wall.
	gait_clock += delta * 5.6
	var blend := minf(1.0,delta*12.0)
	for i in range(2):
		var phase: float = gait_clock + (0.0 if i == 0 else PI)
		upper_leg[i].rotation.x = lerpf(upper_leg[i].rotation.x,.40 + .33*sin(phase),blend)
		knee[i].rotation.x = lerpf(knee[i].rotation.x,.78 + .17*cos(phase),blend)
		feet[i].rotation.x = lerpf(feet[i].rotation.x,-.20,blend)
		shoulder[i].rotation.x = lerpf(shoulder[i].rotation.x,-1.05 + .25*sin(phase+PI),blend)
	avatar.rotation.x = lerpf(avatar.rotation.x,-.11,blend)
	avatar.position.y = lerpf(avatar.position.y,0.0,blend)

func _update_air_pose(delta: float) -> void:
	# Air poses are separate from horizontal movement / Unity Rigidbody2D code.
	var rising: bool = velocity.y >= 0.0
	var ascent: float = clampf(velocity.y / JUMP_VELOCITY, 0.0, 1.0)
	var descent: float = clampf(-velocity.y / 8.0, 0.0, 1.0)
	var smooth: float = minf(1.0, delta * 10.0)
	for i in range(2):
		var lead: float = 1.0 if i == 0 else -1.0
		var hip_target: float = (0.29 + 0.23 * ascent) * lead if rising else -0.17 + descent * 0.24 * lead
		var knee_target: float = (0.70 - 0.10 * ascent) if rising else 0.28 + 0.22 * descent
		var arm_target: float = (-0.48 + 0.15 * ascent) if rising else 0.13 + 0.12 * descent
		upper_leg[i].rotation.x = lerpf(upper_leg[i].rotation.x, hip_target, smooth)
		knee[i].rotation.x = lerpf(knee[i].rotation.x, knee_target, smooth)
		shoulder[i].rotation.x = lerpf(shoulder[i].rotation.x, arm_target, smooth)
		feet[i].rotation.x = lerpf(feet[i].rotation.x, -0.22 if rising else 0.12, smooth)
		shoulder[i].rotation.z = lerpf(shoulder[i].rotation.z, lead * 0.10, smooth)
	avatar.rotation.x = lerpf(avatar.rotation.x, -0.05 if rising else 0.045, minf(1.0, delta * 6.5))
	avatar.position.y = lerpf(avatar.position.y, 0.02 * takeoff_visual, minf(1.0, delta * 9.0))

func _update_gait(delta: float, horizontal_speed: float, running: bool, axis: float) -> void:
	# Ground locomotion: continuous walk/run blend instead of a frame-cut.
	# Pace follows real planar travel. Arm swing is opposite to each thigh.
	var locomotion: float = clampf(horizontal_speed / WALK_MPS, 0.0, 1.0)
	var target_run: float = 1.0 if running and horizontal_speed > 2.0 else 0.0
	run_blend = move_toward(run_blend, target_run, delta * 4.8)
	var activity: float = locomotion * clampf(axis * 2.1, 0.0, 1.0)
	if activity > 0.02:
		gait_clock += horizontal_speed * delta * lerpf(2.1, 2.68, run_blend)
	var stride: float = lerpf(0.48, 0.80, run_blend) * activity
	var lift: float = lerpf(0.40, 0.76, run_blend) * activity
	var slope_scale: float = clampf(floor_deg / 25.0, 0.0, 1.0)
	var uphill: float = maxf(0.0, slope_sign) * slope_scale
	var downhill: float = maxf(0.0, -slope_sign) * slope_scale
	var smooth: float = minf(1.0, delta * 12.0)
	for i in range(2):
		var phase: float = gait_clock + (0.0 if i == 0 else PI)
		var leg_cycle: float = sin(phase)
		# Bent knee clears the ground during forward recovery and steep climbs.
		var recovering: float = maxf(0.0, leg_cycle)
		var thigh_goal: float = leg_cycle * stride + uphill * 0.08
		var knee_goal: float = (recovering * lift + uphill * 0.24 + downhill * 0.08) * activity
		var foot_goal: float = -knee_goal * 0.38 - leg_cycle * 0.10 * activity
		upper_leg[i].rotation.x = lerpf(upper_leg[i].rotation.x, thigh_goal, smooth)
		knee[i].rotation.x = lerpf(knee[i].rotation.x, knee_goal, smooth)
		feet[i].rotation.x = lerpf(feet[i].rotation.x, foot_goal, smooth)
		shoulder[i].rotation.x = lerpf(shoulder[i].rotation.x, -leg_cycle * stride * 0.77, smooth)
		shoulder[i].rotation.z = lerpf(shoulder[i].rotation.z, (1.0 if i == 0 else -1.0) * run_blend * 0.055 * activity, smooth)
	var forward_lean: float = -0.075 * run_blend * activity - uphill * 0.10 + downhill * 0.035
	avatar.rotation.x = lerpf(avatar.rotation.x, forward_lean, minf(1.0, delta * 7.0))
	# Two support beats per stride. Landing compression remains visual only.
	var support_beat: float = 0.5 - 0.5 * cos(gait_clock * 2.0)
	var bounce: float = support_beat * lerpf(0.011, 0.029, run_blend) * activity
	var compression: float = -0.07 * landing_visual + 0.035 * takeoff_visual
	avatar.position.y = lerpf(avatar.position.y, bounce + compression, minf(1.0, delta * 12.0))

func _apply_attack_pose(delta: float) -> void:
	# Left-click input from pawn_player.cs: right arm swings once, retriggerable.
	attack_timer = maxf(0.0, attack_timer - delta)
	if shoulder.size() < 2:
		return
	if attack_timer > 0.0:
		var elapsed: float = 1.0 - attack_timer / ATTACK_POSE_SECONDS
		var strike: float = pow(maxf(0.0, sin(elapsed * PI)), 1.3)
		shoulder[1].rotation.x = lerpf(shoulder[1].rotation.x, -1.35 * strike, minf(1.0, delta * 24.0))
		shoulder[1].rotation.z = lerpf(shoulder[1].rotation.z, -0.18 * strike, minf(1.0, delta * 18.0))

func reset_at(world_x: float, base_y: float, world_z: float, index: int) -> void:
	global_position = Vector3(world_x, base_y + SPAWN_CLEARANCE_M, world_z)
	velocity = Vector3.ZERO
	lane_index = index
	heading_index = 0
	board_origin = Vector3.ZERO # continuous world-aligned 2m x 2m tiles
	current_cell = BOARD_RULES.cell_at(global_position, board_origin)
	resistance_time = 0.0
	resistance_attempts = 0
	smoothed_strafe = 0.0
	gait_clock = 0.0
	dash_timer = 0.0
	dash_cooldown = 0.0
	climbing = false
	run_blend = 0.0
	attack_timer = 0.0
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
