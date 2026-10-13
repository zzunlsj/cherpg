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
const NORMAL_FLOOR_CUTOFF_DEG := 29.5  # >=30° requires grabbable contact-climbing
const WALL_CLIMB_MPS := 2.5
const CLIMB_MIN_ANGLE_DEG := 30.0
const GRAB_REACH_M := 0.95
const CROUCH_MPS := 1.8
const STANDING_HEIGHT_M := 1.43
const CROUCH_HEIGHT_M := 1.02
const CROUCH_TRANSITION_RATE := 7.5
const MAX_KNEE_FLEX_RAD := 1.65
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
var board_rules_enabled := true
var crouching := false
var running := false
var crouch_blend := 0.0
var capsule_shape: CapsuleShape3D
var capsule_collider: CollisionShape3D
var climbing := false
var climb_normal := Vector3.ZERO
const MANTLE_TIME := 1.16
var mantle_active := false
var mantle_clock := 0.0
var mantle_start := Vector3.ZERO
var mantle_up := Vector3.ZERO
var mantle_over := Vector3.ZERO
var mantle_finish := Vector3.ZERO
var mantle_blocked_seconds := 0.0
var mantle_stage := "NONE"
var ground_normal := Vector3.UP
var device: Node3D
var movement_camera: Camera3D
# Stable camera yaw-forward vector used at every pitch, including true 90°.
var camera_orbit_forward := Vector3.FORWARD
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
	capsule_shape = CapsuleShape3D.new()
	capsule_shape.radius = 0.235
	capsule_shape.height = STANDING_HEIGHT_M
	capsule_collider = CollisionShape3D.new()
	capsule_collider.name = "PawnCollisionCapsule"
	capsule_collider.shape = capsule_shape
	capsule_collider.position.y = STANDING_HEIGHT_M * 0.5
	add_child(capsule_collider)
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

func _can_stand() -> bool:
	# Sweep/test a taller shape without relocating the character. The collider
	# bottom remains at y=0 in both poses, and obstacles block standing up.
	var stand_capsule := CapsuleShape3D.new()
	stand_capsule.radius = capsule_shape.radius
	stand_capsule.height = STANDING_HEIGHT_M
	var query := PhysicsShapeQueryParameters3D.new()
	query.shape = stand_capsule
	query.transform = Transform3D(Basis.IDENTITY,
		global_position + Vector3.UP * (STANDING_HEIGHT_M * 0.5 + 0.015))
	query.collision_mask = collision_mask
	query.exclude = [get_rid()]
	query.collide_with_bodies = true
	query.collide_with_areas = false
	return get_world_3d().direct_space_state.intersect_shape(query,1).is_empty()

func _update_crouch_collider(delta: float, requested: bool) -> void:
	if requested:
		crouching = true
	elif not crouching or _can_stand():
		crouching = false
	var target := 1.0 if crouching else 0.0
	crouch_blend = move_toward(crouch_blend,target,CROUCH_TRANSITION_RATE*delta)
	var height: float = lerpf(STANDING_HEIGHT_M,CROUCH_HEIGHT_M,crouch_blend)
	capsule_shape.height = height
	capsule_collider.position.y = height * 0.5

func _wall_contact(move_forward: Vector3) -> Dictionary:
	# Contact alone is not enough: collider must explicitly be grabbable.
	# 30° is measured from horizontal (normal relative to Vector3.UP).
	# The separate test ramps and the vertical wall carry this group tag.
	if move_forward.length_squared() < 0.25:
		return {}
	var cast_from: Vector3 = global_position + Vector3.UP * 0.56
	var cast_to: Vector3 = cast_from + move_forward.normalized() * GRAB_REACH_M
	var ray := PhysicsRayQueryParameters3D.create(cast_from,cast_to,1,[get_rid()])
	var hit: Dictionary = get_world_3d().direct_space_state.intersect_ray(ray)
	if hit.is_empty():
		return {}
	var hit_body: CollisionObject3D = hit.get("collider") as CollisionObject3D
	if hit_body == null or not is_instance_valid(hit_body):
		return {}
	if not hit_body.is_in_group("cherpg_grabbable"):
		return {}
	var normal: Vector3 = hit["normal"].normalized()
	var face_angle: float = rad_to_deg(acos(clampf(normal.dot(Vector3.UP),-1.0,1.0)))
	if face_angle < CLIMB_MIN_ANGLE_DEG - 0.1 or face_angle > 90.1:
		return {}
	# Character must be facing and pressing toward the wall.
	if -move_forward.normalized().dot(normal) < 0.40:
		return {}
	hit["slope_angle"] = face_angle
	return hit

func _begin_mantle(target: Vector3) -> void:
	mantle_active = true
	mantle_clock = 0.0
	mantle_blocked_seconds = 0.0
	mantle_start = global_position
	mantle_finish = target
	mantle_up = Vector3(mantle_start.x, target.y + 0.30, mantle_start.z)
	mantle_over = Vector3(target.x, target.y + 0.30, target.z)
	mantle_stage = "REACH"
	climbing = false
	velocity = Vector3.ZERO

func _try_climb_top_ledge(forward: Vector3) -> void:
	if not climbing or mantle_active or climb_normal.y > 0.12:
		return
	var ray_start: Vector3 = global_position + Vector3.UP * 1.55 + forward * 1.05
	var query := PhysicsRayQueryParameters3D.create(ray_start, ray_start + Vector3.DOWN * 2.8, 1, [get_rid()])
	var hit: Dictionary = get_world_3d().direct_space_state.intersect_ray(query)
	if hit.is_empty():
		return
	var normal: Vector3 = hit["normal"]
	var roof_y: float = hit["position"].y
	var remaining: float = roof_y - global_position.y
	if normal.y < 0.88 or roof_y < 0.8 or remaining > 0.53 or remaining < -0.15:
		return
	var destination: Vector3 = global_position + forward * 1.12
	destination.y = roof_y + 0.055
	if bool(_constrain_step(global_position,destination)["resisted"]):
		return
	var roof_capsule := CapsuleShape3D.new()
	roof_capsule.radius = capsule_shape.radius
	roof_capsule.height = STANDING_HEIGHT_M
	var clearance := PhysicsShapeQueryParameters3D.new()
	clearance.shape = roof_capsule
	clearance.transform = Transform3D(Basis.IDENTITY,destination+Vector3.UP*(STANDING_HEIGHT_M*0.5+0.03))
	clearance.collision_mask = collision_mask
	clearance.exclude = [get_rid()]
	if not get_world_3d().direct_space_state.intersect_shape(clearance,1).is_empty():
		return
	_begin_mantle(destination)

func _mantle_goal(fraction: float) -> Vector3:
	var t: float = clampf(fraction,0.0,1.0)
	if t < 0.18:
		return mantle_start
	if t < 0.53:
		return mantle_start.lerp(mantle_up,smoothstep(0.18,0.53,t))
	if t < 0.80:
		return mantle_up.lerp(mantle_over,smoothstep(0.53,0.80,t))
	return mantle_over.lerp(mantle_finish,smoothstep(0.80,1.0,t))

func _update_mantle(delta: float) -> void:
	if not mantle_active:
		return
	velocity = Vector3.ZERO
	var next_t: float = minf(1.0,(mantle_clock+delta)/MANTLE_TIME)
	var desired: Vector3 = _mantle_goal(next_t)
	var constrained: Dictionary = _constrain_step(global_position,desired)
	if bool(constrained["resisted"]):
		_abort_mantle()
		return
	var motion: Vector3 = constrained["position"]-global_position
	if motion.length_squared() > 0.00000001:
		var impact: KinematicCollision3D = move_and_collide(motion)
		if impact != null:
			mantle_blocked_seconds += delta
			if mantle_blocked_seconds > 0.22:
				_abort_mantle()
			return
	mantle_blocked_seconds = 0.0
	mantle_clock = next_t*MANTLE_TIME
	var t: float = next_t
	mantle_stage = "REACH" if t < .18 else ("PULL" if t < .53 else ("SWING" if t < .80 else "LAND"))
	_update_mantle_pose(t,delta)
	_clamp_anatomical_joints()
	_apply_terrain_pose(delta)
	_prevent_part_penetration(delta)
	current_cell = BOARD_RULES.cell_at(global_position,board_origin)
	move_state = "MANTLE "+mantle_stage
	jump_state = "MANTLING"
	if next_t >= 1.0:
		mantle_active = false
		mantle_stage = "DONE"
		velocity = Vector3.ZERO
		jump_state = "GROUNDED"

func _abort_mantle() -> void:
	mantle_active = false
	mantle_stage = "BLOCKED"
	velocity = Vector3.ZERO
	jump_state = "FALLING"

func _update_mantle_pose(t: float, delta: float) -> void:
	var blend: float = minf(1.0,delta*15.0)
	var reach: float = smoothstep(0.0,.18,t)
	var lift: float = smoothstep(.18,.58,t)
	var leg_over: float = smoothstep(.53,.84,t)
	var settle: float = smoothstep(.82,1.0,t)
	for i in range(2):
		var delay: float = .08 if i == 0 else 0.0
		var arm: float = lerpf(0.15,1.06,reach)
		arm = lerpf(arm,0.75,lift)
		arm = lerpf(arm,0.02,settle)
		var knee_bend: float = lerpf(-.35,-1.28,leg_over)
		knee_bend = lerpf(knee_bend,-.06,settle)
		var thigh: float = lerpf(-.08,.56,smoothstep(.48+delay,.75+delay,t))
		thigh = lerpf(thigh,0.0,settle)
		upper_leg[i].rotation.x = lerpf(upper_leg[i].rotation.x,thigh,blend)
		knee[i].rotation.x = lerpf(knee[i].rotation.x,knee_bend,blend)
		feet[i].rotation.x = lerpf(feet[i].rotation.x,.12*(1.0-settle),blend)
		shoulder[i].rotation.x = lerpf(shoulder[i].rotation.x,arm,blend)
		shoulder[i].rotation.z = lerpf(shoulder[i].rotation.z,(-.13 if i==0 else .13)*reach*(1.0-settle),blend)
	avatar.rotation.x = lerpf(avatar.rotation.x,lerpf(-.12,-.29,lift)*(1.0-settle),blend)
	avatar.position.y = lerpf(avatar.position.y,-.04*lift*(1.0-settle),blend)

func trigger_attack() -> void:
	# Unity source: ResetTrigger("attack"), then SetTrigger("attack").
	# Placeholder arm motion; no combat hitbox or damage is invented.
	if device != null and bool(device.call("is_busy")):
		return
	attack_timer = ATTACK_POSE_SECONDS

func set_movement_camera(source: Camera3D) -> void:
	movement_camera = source

func set_camera_orbit_yaw(yaw: float) -> void:
	# Follow the orbit's azimuth rather than project camera look into XZ:
	# at 90° top-down the projection becomes zero, and camera motion lags.
	camera_orbit_forward = Vector3(-sin(yaw),0.0,-cos(yaw))

func _camera_flat_forward() -> Vector3:
	# W is screen-up on the horizontal board at all camera elevations.
	# Camera pitch and Pawn chess-heading are independent of the move axis.
	return camera_orbit_forward

func _horizontal_velocity() -> Vector3:
	return Vector3(velocity.x, 0.0, velocity.z)

func _constrain_step(from_position: Vector3, to_position: Vector3) -> Dictionary:
	# I changes logical tile collision only; visual 4m checker stays intact.
	if board_rules_enabled:
		return BOARD_RULES.constrain_voluntary(from_position,to_position,board_origin,heading_index)
	return {"position":to_position,"resisted":false,"blocked_x":false,"blocked_z":false}

## Independent testable planar physics adapter for the Unity movement feel.
## Godot move_and_slide() will handle final collider response after this update.
func _source_feel_horizontal(current: Vector3, input_vector: Vector2, sprint: bool, delta: float, floor: bool, slope_multiplier: float) -> Vector3:
	var speed_cap: float = (RUN_MPS if sprint else WALK_MPS) * slope_multiplier
	if crouching:
		speed_cap = minf(speed_cap,CROUCH_MPS)
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
	if mantle_active:
		_update_mantle(delta)
		return
	_update_crouch_collider(delta,Input.is_key_pressed(KEY_SHIFT))
	# Ctrl takes priority as a sustained run/climb input; Shift crouch prevents running.
	running = Input.is_key_pressed(KEY_CTRL) and not crouching
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
	var wants_run: bool = running and (not is_zero_approx(raw_axis) or not is_zero_approx(raw_strafe))
	latest_axis = input_vector.y
	latest_sprint = wants_run
	var forward: Vector3 = _camera_flat_forward()
	var direction: Vector3 = (forward * input_vector.y + forward.cross(Vector3.UP) * input_vector.x).normalized()
	var contact: Dictionary = _wall_contact(forward) if raw_axis > 0.35 and running and not device_busy else {}
	# Grabbing requires Ctrl + forward movement + tagged surface 30° or steeper.
	climbing = not contact.is_empty()
	if climbing:
		climb_normal = contact["normal"]

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
	if jump_buffer_left > 0.0 and coyote_left > 0.0 and not device_busy and not climbing:
		velocity.y = JUMP_VELOCITY
		jump_buffer_left = 0.0
		coyote_left = 0.0
		jump_count += 1
		jump_state = "RISING"
		takeoff_visual = 1.0
		was_on_floor = false

	if climbing:
		# Surface-tangent ascent works from 30° inclines to 90° walls.
		var ascent: Vector3 = (Vector3.UP - climb_normal * climb_normal.y).normalized()
		velocity.y = ascent.y * WALL_CLIMB_MPS - climb_normal.y * 0.18
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

	var next_horizontal := _source_feel_horizontal(current_horizontal, input_vector, wants_run, delta, was_on_floor, slope_factor)
	if climbing:
		var tangent_up: Vector3 = (Vector3.UP - climb_normal * climb_normal.y).normalized()
		next_horizontal = Vector3(tangent_up.x,0.0,tangent_up.z) * WALL_CLIMB_MPS 			- Vector3(climb_normal.x,0.0,climb_normal.z) * 0.18
	if device_busy:
		next_horizontal = Vector3.ZERO
	var starting_position: Vector3 = global_position
	var prediction: Dictionary = _constrain_step(starting_position,starting_position+next_horizontal*delta)
	var projected_pos: Vector3 = prediction["position"]
	next_horizontal = (projected_pos - starting_position) / maxf(delta, 0.000001)
	velocity.x = next_horizontal.x
	velocity.z = next_horizontal.z
	move_and_slide()
	_try_climb_top_ledge(forward)
	# Physical collision resolution and airborne drift must obey the same rule.
	var resolved: Dictionary = _constrain_step(starting_position,global_position)
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
	elif crouching and is_on_floor():
		move_state = "CROUCH MOVE" if _horizontal_velocity().length() > 0.10 else "CROUCH"
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
	elif crouching and is_on_floor():
		_update_crouch_pose(delta,horizontal_speed,input_vector.length())
	elif is_on_floor():
		_update_gait(delta,horizontal_speed,wants_run,input_vector.length())
	else:
		_update_air_pose(delta)
	_apply_attack_pose(delta)
	_clamp_anatomical_joints()
	avatar.scale.y = lerpf(1.0,0.67,crouch_blend)
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
		knee[i].rotation.x = lerpf(knee[i].rotation.x,-(.78 + .17*cos(phase)),blend)
		feet[i].rotation.x = lerpf(feet[i].rotation.x,-.20,blend)
		shoulder[i].rotation.x = lerpf(shoulder[i].rotation.x,-1.05 + .25*sin(phase+PI),blend)
	avatar.rotation.x = lerpf(avatar.rotation.x,-.12 - .22 * (1.0-climb_normal.y),blend)
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
		knee[i].rotation.x = lerpf(knee[i].rotation.x, -absf(knee_target), smooth)
		shoulder[i].rotation.x = lerpf(shoulder[i].rotation.x, arm_target, smooth)
		feet[i].rotation.x = lerpf(feet[i].rotation.x, -0.22 if rising else 0.12, smooth)
		shoulder[i].rotation.z = lerpf(shoulder[i].rotation.z, lead * 0.10, smooth)
	avatar.rotation.x = lerpf(avatar.rotation.x, -0.05 if rising else 0.045, minf(1.0, delta * 6.5))
	avatar.position.y = lerpf(avatar.position.y, 0.02 * takeoff_visual, minf(1.0, delta * 9.0))

func _gait_joint_targets(phase: float, run_amount: float) -> Vector3:
	# Simplified gait-cycle key poses, not a pure sine wave.
	# Literature-inspired 60% stance/40% swing; loading knee ~15-20°,
	# initial swing knee approaching ~60° for toe clearance.
	# Result vector: hip sagittal, knee flexion, ankle/foot pitch (radians).
	var hip: float = 0.0
	var knee_angle: float = 0.0
	var ankle: float = 0.0
	var stride_scale: float = lerpf(1.0,1.35,run_amount)
	if phase < 0.12:
		# Heel strike -> loading response: slight knee shock absorption.
		var t: float = smoothstep(0.0,0.12,phase)
		hip = lerpf(0.37,0.18,t) * stride_scale
		knee_angle = lerpf(0.04,0.30,t)
		ankle = lerpf(0.11,-0.04,t)
	elif phase < 0.40:
		# Weight passes over the planted foot; knee straightens.
		var t: float = smoothstep(0.12,0.40,phase)
		hip = lerpf(0.18,-0.26,t) * stride_scale
		knee_angle = lerpf(0.30,0.08,t)
		ankle = lerpf(-0.04,-0.12,t)
	elif phase < 0.60:
		# Heel rises, toe pushes off, knee folds for preswing.
		var t: float = smoothstep(0.40,0.60,phase)
		hip = lerpf(-0.26,-0.38,t) * stride_scale
		knee_angle = lerpf(0.08,0.49,t)
		ankle = lerpf(-0.12,-0.34,t)
	elif phase < 0.80:
		# Swing: knee flexes to clear toe and thigh advances.
		var t: float = smoothstep(0.60,0.80,phase)
		hip = lerpf(-0.38,0.16,t) * stride_scale
		knee_angle = lerpf(0.49,1.05,t)
		ankle = lerpf(-0.34,0.16,t)
	else:
		# Terminal swing extends knee before heel strike.
		var t: float = smoothstep(0.80,1.0,phase)
		hip = lerpf(0.16,0.37,t) * stride_scale
		knee_angle = lerpf(1.05,0.04,t)
		ankle = lerpf(0.16,0.11,t)
	return Vector3(hip,knee_angle * lerpf(1.0,1.13,run_amount),ankle)

func _update_gait(delta: float, horizontal_speed: float, running: bool, axis: float) -> void:
	# Human-inspired phase organization; 60% foot support + 40% leg swing.
	# This is artistic procedural animation for the 1.55m primitive Pawn.
	# Real-time planted-foot IK is not yet implemented.
	var moving: float = clampf(horizontal_speed / WALK_MPS,0.0,1.0)
	var activity: float = moving * clampf(axis * 2.0,0.0,1.0)
	var target_run: float = 1.0 if running and horizontal_speed > 2.0 else 0.0
	run_blend = move_toward(run_blend,target_run,delta * 5.2)
	# Body movement speed is retained from Unity input, but animation cadence
	# is clamped to natural-looking proportions rather than 4m stride length.
	if activity > 0.03:
		var cycles_per_sec: float = lerpf(0.72,1.65,run_blend) * lerpf(0.45,1.0,moving)
		gait_clock = fposmod(gait_clock + TAU * cycles_per_sec * delta, TAU)
	var phase: float = fposmod(gait_clock / TAU,1.0)
	var slope_ratio: float = clampf(floor_deg / 45.0,0.0,1.0)
	var uphill: float = maxf(0.0,slope_sign) * slope_ratio
	var downhill: float = maxf(0.0,-slope_sign) * slope_ratio
	var blend: float = minf(1.0,delta * 13.5)
	for i in range(2):
		var local_phase: float = fposmod(phase + (0.0 if i == 0 else 0.5),1.0)
		var joints: Vector3 = _gait_joint_targets(local_phase,run_blend)
		var thigh: float = (joints.x + uphill * 0.12) * activity
		var knee_target: float = (joints.y + uphill * 0.16 + downhill * 0.06) * activity
		var foot_target: float = (joints.z - uphill * 0.08) * activity
		upper_leg[i].rotation.x = lerpf(upper_leg[i].rotation.x,thigh,blend)
		knee[i].rotation.x = lerpf(knee[i].rotation.x,-absf(knee_target),blend)
		feet[i].rotation.x = lerpf(feet[i].rotation.x,foot_target,blend)
		# Right arm moves forward with left thigh (counter-swing).
		shoulder[i].rotation.x = lerpf(shoulder[i].rotation.x,-thigh * .68,blend)
		shoulder[i].rotation.z = lerpf(shoulder[i].rotation.z,(1.0 if i == 0 else -1.0) * .038 * activity,blend)
	# Alternating support allows small centre-of-mass bob and lateral shift.
	var support: float = absf(sin(phase * TAU))
	var bob: float = (0.006 + .014 * run_blend) * support * activity
	var compression: float = -0.07 * landing_visual + 0.035 * takeoff_visual
	var forward_lean: float = -.040 * activity - .065 * run_blend * activity - uphill * .10 + downhill * .035
	avatar.rotation.x = lerpf(avatar.rotation.x,forward_lean,minf(1.0,delta*8.0))
	avatar.rotation.z = lerpf(avatar.rotation.z,.025 * cos(phase * TAU) * activity,minf(1.0,delta * 7.0))
	avatar.position.y = lerpf(avatar.position.y,bob+compression,minf(1.0,delta * 13.0))



func _update_crouch_pose(delta: float, horizontal_speed: float, axis: float) -> void:
	# Anatomical knee hinge: X-negative folds shin toward the rear (+Z).
	# Never bend the knee through the front of the shin.
	var blend: float = minf(1.0,delta*12.0)
	var crawl_activity: float = clampf(horizontal_speed/CROUCH_MPS,0.0,1.0) * clampf(axis*2.0,0.0,1.0)
	if crawl_activity > 0.02:
		gait_clock = fposmod(gait_clock+TAU*.82*delta,TAU)
	for i in range(2):
		var phase: float = gait_clock+(0.0 if i==0 else PI)
		var phase_swing: float = sin(phase)*crawl_activity
		var hip_target: float = 0.36 + 0.12*phase_swing
		var flex_target: float = -(0.91 + 0.12*maxf(0.0,phase_swing))
		upper_leg[i].rotation.x = lerpf(upper_leg[i].rotation.x,hip_target,blend)
		knee[i].rotation.x = lerpf(knee[i].rotation.x,flex_target,blend)
		feet[i].rotation.x = lerpf(feet[i].rotation.x,0.19,blend)
		shoulder[i].rotation.x = lerpf(shoulder[i].rotation.x,-0.23 - 0.08*phase_swing,blend)
	avatar.rotation.x = lerpf(avatar.rotation.x,0.09,blend)
	avatar.rotation.z = lerpf(avatar.rotation.z,0.01*sin(gait_clock)*crawl_activity,blend)
	avatar.position.y = lerpf(avatar.position.y,0.0,blend)

func _clamp_anatomical_joints() -> void:
	# The shin mesh extends down from its knee pivot. In this rig a
	# NEGATIVE X knee rotation means bending BACK, toward the heel.
	# Prevent hyperextension/reverse knees in ALL poses, even after blending.
	for i in range(2):
		knee[i].rotation.x = clampf(knee[i].rotation.x,-MAX_KNEE_FLEX_RAD,0.0)
		upper_leg[i].rotation.x = clampf(upper_leg[i].rotation.x,-0.85,0.85)
		feet[i].rotation.x = clampf(feet[i].rotation.x,-0.50,0.48)
		shoulder[i].rotation.x = clampf(shoulder[i].rotation.x,-1.60,1.20)
		shoulder[i].rotation.z = clampf(shoulder[i].rotation.z,-0.28,0.28)
	avatar.rotation.x = clampf(avatar.rotation.x,-0.38,0.18)
	avatar.rotation.z = clampf(avatar.rotation.z,-0.10,0.10)

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
	board_origin = Vector3.ZERO # continuous world-aligned 4m x 4m tiles
	current_cell = BOARD_RULES.cell_at(global_position, board_origin)
	resistance_time = 0.0
	resistance_attempts = 0
	smoothed_strafe = 0.0
	gait_clock = 0.0
	crouching = false
	running = false
	crouch_blend = 0.0
	capsule_shape.height = STANDING_HEIGHT_M
	capsule_collider.position.y = STANDING_HEIGHT_M*0.5
	avatar.scale = Vector3.ONE
	climbing = false
	mantle_active = false
	mantle_clock = 0.0
	mantle_stage = "NONE"
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
