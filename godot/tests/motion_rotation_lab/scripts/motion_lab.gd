extends Node3D
## Independent CheRPG 100m x 100m ground + slope test obstacles.
const TERRAIN_SCRIPT = preload("res://scripts/test_lane.gd")
const PAWN_SCRIPT = preload("res://scripts/pawn_controller.gd")
var terrain: StaticBody3D
var pawn
var camera: Camera3D
var info: Label
var help_label: Label
var camera_yaw := 0.0
# Elevation measured upward from horizon: 0° horizontal, 90° straight down.
# Mouse up increases elevation; a full 90° top-down view is explicitly allowed.
var camera_elevation := deg_to_rad(24.0)
const CAMERA_ELEVATION_MIN := -PI / 7.2
const CAMERA_ELEVATION_MAX := PI / 2.0
var camera_distance := 6.8 # Desired orbit radius when nothing blocks the view.
const CAMERA_COLLISION_RADIUS := 0.23 # Sphere keeps near-plane away from walls.
const CAMERA_SURFACE_MARGIN := 0.08
const CAMERA_FOLLOW_SPEED := 8.0
const CAMERA_RECOVER_SPEED := 4.5
var camera_actual_distance := 6.8
var camera_wall_blocked := false
var camera_query_sphere: SphereShape3D
var camera_target := Vector3.ZERO
var board_rules_enabled := true
var active_station := 0

func _ready() -> void:
	_build_lighting()
	terrain = TERRAIN_SCRIPT.new()
	add_child(terrain)
	terrain.call("setup")
	pawn = PAWN_SCRIPT.new()
	add_child(pawn)
	camera = Camera3D.new()
	camera.name = "FollowCamera"
	camera.fov = 65.0
	camera.near = 0.06
	camera_query_sphere = SphereShape3D.new()
	camera_query_sphere.radius = CAMERA_COLLISION_RADIUS
	camera.current = true
	add_child(camera)
	pawn.set_movement_camera(camera)
	pawn.board_rules_enabled = board_rules_enabled
	_teleport_to_station(0)
	_build_ui()
	camera_target = pawn.global_position + Vector3.UP * 1.1
	_update_camera(1.0)
	Input.set_mouse_mode(Input.MOUSE_MODE_CAPTURED)
	# Long/major tests belong to the user. Never auto-run simulation.
	if OS.get_cmdline_user_args().has("--smoke-test"):
		_run_smoke_test.call_deferred()

func _build_lighting() -> void:
	var env := WorldEnvironment.new()
	env.name = "NeutralPrototypeSky"
	env.environment = Environment.new()
	env.environment.background_mode = Environment.BG_COLOR
	env.environment.background_color = Color("c9d6dc")
	env.environment.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	env.environment.ambient_light_color = Color("a9b8c4")
	env.environment.ambient_light_energy = .8
	add_child(env)
	var sun := DirectionalLight3D.new()
	sun.rotation_degrees = Vector3(-55,-30,0)
	sun.light_energy = 1.35
	sun.shadow_enabled = true
	add_child(sun)

func _build_ui() -> void:
	var hud := CanvasLayer.new()
	hud.name = "DebugHUD"
	add_child(hud)
	var bg := PanelContainer.new()
	bg.set_anchors_and_offsets_preset(Control.PRESET_TOP_LEFT)
	bg.offset_left = 20.0
	bg.offset_top = 20.0
	bg.custom_minimum_size = Vector2(740.0,195.0)
	hud.add_child(bg)
	var content := VBoxContainer.new()
	bg.add_child(content)
	info = Label.new()
	info.name = "MotionAndDeviceState"
	info.add_theme_font_size_override("font_size",16)
	content.add_child(info)
	help_label = Label.new()
	help_label.text = "WASD: camera movement | Ctrl + W: grab/ascend a 30°+ marked wall\nClimbing + Ctrl: HOLD | W/S: UP/DOWN | A/D: SIDEWAYS (fixed wall axes, no camera steering)\nShift: CROUCH | I: chess movement limits ONLY | F hold: footprint / release: anchor\nO: reset | Space: jump | 1-9,0: stations | Mouse: 90° orbit (wall-safe camera) | Esc: cursor"
	help_label.add_theme_font_size_override("font_size",14)
	content.add_child(help_label)
	_update_hud()

func _physics_process(_delta: float) -> void:
	_update_hud()

func _process(delta: float) -> void:
	_update_camera(delta)
	if pawn != null and pawn.device != null:
		pawn.device.call("set_preview_held",Input.is_key_pressed(KEY_F))

func _camera_collision_clamp(pivot: Vector3, wanted: Vector3) -> Vector3:
	# A sphere sweep tests the entire camera arm, not merely its end point.
	# The same volume is checked on EVERY frame, including camera rotation
	# and target smoothing. Layer 1 = level geometry; Pawn uses layer 2.
	var motion: Vector3 = wanted - pivot
	if motion.length_squared() < 0.000001:
		return pivot
	var query := PhysicsShapeQueryParameters3D.new()
	query.shape = camera_query_sphere
	query.transform = Transform3D(Basis.IDENTITY,pivot)
	query.motion = motion
	query.margin = 0.015
	query.collision_mask = 1
	query.collide_with_bodies = true
	query.collide_with_areas = false
	var safe: PackedFloat32Array = get_world_3d().direct_space_state.cast_motion(query)
	if safe.size() < 1:
		return wanted
	var safe_fraction: float = clampf(safe[0],0.0,1.0)
	var movement_length: float = motion.length()
	var allowed_distance: float = maxf(0.0,movement_length * safe_fraction - CAMERA_SURFACE_MARGIN)
	return pivot + motion.normalized() * allowed_distance

func _update_camera(delta: float) -> void:
	if pawn == null or camera == null:
		return
	var desired_target: Vector3 = pawn.global_position + Vector3.UP * 1.13
	camera_target = camera_target.lerp(desired_target,clampf(delta*7.0,0.0,1.0))
	var lateral := Vector3(sin(camera_yaw),0,cos(camera_yaw))
	var desired := camera_target + lateral * camera_distance * cos(camera_elevation) + Vector3.UP * camera_distance * sin(camera_elevation)
	# First clamp desired orbit against walls/floors/ceilings. Pull forward
	# immediately on collision; restore the normal 6.8m orbit gradually.
	# A climber stands almost against the wall. Cast from a pivot shifted
	# slightly toward the wall's outward normal to avoid starting the camera
	# sweep embedded in the contacted surface.
	var sweep_pivot: Vector3 = camera_target
	if pawn.climbing:
		sweep_pivot += pawn.climb_normal * 0.11
	var obstacle_safe: Vector3 = _camera_collision_clamp(sweep_pivot,desired)
	var safe_distance: float = camera_target.distance_to(obstacle_safe)
	camera_wall_blocked = safe_distance < camera_distance - 0.10
	var speed: float = CAMERA_FOLLOW_SPEED if camera_wall_blocked else CAMERA_RECOVER_SPEED
	var interpolated: Vector3 = camera.global_position.lerp(obstacle_safe,clampf(delta*speed,0.0,1.0))
	# Smoothing/orbit rotation itself might sweep the camera through a wall.
	# Clamp the interpolated final camera as well, not just the desired arm.
	camera.global_position = _camera_collision_clamp(sweep_pivot,interpolated)
	camera_actual_distance = camera.global_position.distance_to(camera_target)
	# Keep the Pawn in view even when a wall forces a very close camera.
	camera.fov = lerpf(80.0,65.0,clampf((camera_actual_distance-0.65)/2.5,0.0,1.0))
	# At 90°, World UP is parallel to the downward view. Choose a stable
	# horizontal camera-up vector to prevent look_at's singularity/roll flip.
	var stable_up: Vector3 = -lateral if camera_elevation >= deg_to_rad(89.0) else Vector3.UP
	camera.look_at(camera_target,stable_up)
	# Steering follows camera orbit yaw, even when camera looks straight down.
	# Screen-up never snaps to a default world axis at 90° elevation.
	pawn.set_camera_orbit_yaw(camera_yaw)

func _input(event: InputEvent) -> void:
	if event is InputEventMouseMotion and Input.mouse_mode == Input.MOUSE_MODE_CAPTURED:
		camera_yaw -= event.relative.x*.004
		camera_elevation = clampf(camera_elevation-event.relative.y*.003,CAMERA_ELEVATION_MIN,CAMERA_ELEVATION_MAX)
	elif event is InputEventMouseButton and event.button_index == MOUSE_BUTTON_LEFT and event.pressed:
		if pawn != null:
			pawn.trigger_attack()

func _unhandled_key_input(event: InputEvent) -> void:
	if pawn == null:
		return
	if event.physical_keycode == KEY_SPACE:
		if event.pressed and not event.echo:
			pawn.queue_jump()
		elif not event.pressed:
			pawn.release_jump()
		get_viewport().set_input_as_handled()
		return
	# Single F key: while held show the required area; on release commit
	# the deploy / stow command once. No R preview action remains.
	if event.physical_keycode == KEY_F:
		if not event.pressed:
			pawn.device.call("set_preview_held",false)
			pawn.device.call("request_toggle")
		get_viewport().set_input_as_handled()
		return
	if not event.pressed or event.echo:
		return
	match event.physical_keycode:
		KEY_A:
			if pawn.device.call("phase_name") == "ANCHORED":
				pawn.device.call("request_turn",-1)
		KEY_D:
			if pawn.device.call("phase_name") == "ANCHORED":
				pawn.device.call("request_turn",1)
		KEY_O:
			_teleport_to_station(active_station)
		KEY_1,KEY_2,KEY_3,KEY_4,KEY_5,KEY_6,KEY_7,KEY_8,KEY_9:
			_teleport_to_station(int(event.physical_keycode)-int(KEY_1))
		KEY_0:
			_teleport_to_station(9)
		KEY_Z:
			pawn.rotate_body_only(-90.0)
		KEY_C:
			pawn.rotate_body_only(90.0)
		KEY_I:
			board_rules_enabled = not board_rules_enabled
			pawn.board_rules_enabled = board_rules_enabled
		KEY_ESCAPE:
			var mode := Input.MOUSE_MODE_VISIBLE if Input.mouse_mode == Input.MOUSE_MODE_CAPTURED else Input.MOUSE_MODE_CAPTURED
			Input.set_mouse_mode(mode)
	get_viewport().set_input_as_handled()

func _teleport_to_station(index: int) -> void:
	if terrain == null or index < 0 or index >= int(terrain.call("spawn_count")):
		return
	active_station = index
	var point: Vector3 = terrain.call("spawn_position",index)
	pawn.call("reset_at",point.x,point.y,point.z,index)
	camera_target = pawn.global_position + Vector3.UP

func _update_hud() -> void:
	if pawn == null or info == null:
		return
	var station: String = str(terrain.call("station_name",active_station))
	var rule_status: String = "RESISTANCE" if pawn.resistance_time > 0.0 else "CLEAR"
	info.text = "CheRPG | 100m x 100m / 4m GRID (25x25) | 0.0.18v\n" \
		+ "STATION %d/10: %s | MOVE: %s | FLOOR: %.1f° (MAX: 90°)\n" % [active_station+1,station,pawn.move_state,pawn.floor_deg] \
		+ "CAMERA: %.0f°/90° | ARM: %.2f/%.2fm (%s) | BODY YAW: %.0f° | CHESS HEADING: %s\n" % [rad_to_deg(camera_elevation),camera_actual_distance,camera_distance,("WALL" if camera_wall_blocked else "CLEAR"),rad_to_deg(pawn.avatar.rotation.y),pawn.HEADING_NAMES[pawn.heading_index]] \
		+ "JUMP: %s | DEVICE: %s | %s\n" % [pawn.jump_state,pawn.device.call("phase_name"),pawn.device.reason] \
		+ "TILE: (%d,%d) | MOVE LIMIT: %s | F: %s | STANCE: %s | RUN: %s\n" % [pawn.current_cell.x,pawn.current_cell.y,("ON / "+rule_status if board_rules_enabled else "OFF"),pawn.device.preview_reason,("CROUCH" if pawn.crouching else "STAND"),("YES" if pawn.running else "NO")] \
		+ "MANTLE: %s | GRIP: %s | WALL INPUT: (%.1f,%.1f) | PARTS: %d | POSE FIXES: %d" % [pawn.mantle_stage,("HOLD" if pawn.climbing and pawn.climb_input.length_squared() < .001 else ("MOVE" if pawn.climbing else "OFF")),pawn.climb_input.x,pawn.climb_input.y,pawn.part_probes.size(),pawn.collision_corrections]

func _run_smoke_test() -> void:
	# User invoked via --smoke-test. Short structure-only check; no long playtest.
	assert(terrain != null)
	assert(terrain.get_node_or_null("BaseFloorCollision_100x100") != null)
	assert(terrain.get_node_or_null("Grabbable90degWall/VerticalWallCollision") != null)
	assert(pawn.device.components.size() == 4)
	for i in range(int(terrain.call("spawn_count"))):
		assert(terrain.call("spawn_position",i) is Vector3)
	print("CHERPG_100X100_4M_GRID_STRUCTURE_OK (USER PLAYTEST REQUIRED)")
	get_tree().quit(0)
