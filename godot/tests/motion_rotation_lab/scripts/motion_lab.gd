extends Node3D
## CheRPG independent 3D control lab: ONE physically connected map, five zones.
const TERRAIN_SCRIPT = preload("res://scripts/test_lane.gd")
const PAWN_SCRIPT = preload("res://scripts/pawn_controller.gd")
const ZONE_NAMES := ["FLAT", "8 DEG SLOPE", "15 DEG SLOPE", "UNEVEN", "30 DEG LIMIT"]
var terrain: StaticBody3D
var pawn
var camera: Camera3D
var info: Label
var help_label: Label
var camera_yaw := 0.0
var camera_pitch := -0.19
var camera_distance := 6.8
var camera_target := Vector3.ZERO
var grid_debug_visible := false

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
	camera.current = true
	add_child(camera)
	pawn.set_movement_camera(camera)
	_teleport_to_zone(0)
	_build_ui()
	camera_target = pawn.global_position + Vector3.UP * 1.1
	_update_camera(1.0)
	Input.set_mouse_mode(Input.MOUSE_MODE_CAPTURED)
	# Testing is user-led; never run the optional smoke routine automatically.
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
	env.environment.ambient_light_energy = 0.8
	add_child(env)
	var sun := DirectionalLight3D.new()
	sun.rotation_degrees = Vector3(-55, -30, 0)
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
	bg.custom_minimum_size = Vector2(650.0, 185.0)
	hud.add_child(bg)
	var content := VBoxContainer.new()
	bg.add_child(content)
	info = Label.new()
	info.name = "MotionAndDeviceState"
	info.add_theme_font_size_override("font_size", 16)
	content.add_child(info)
	help_label = Label.new()
	help_label.text = "WASD / Arrows: CAMERA MOVEMENT | Shift: sprint | Space: jump | Click: basic attack pose\n1–5: move between zones (all terrain physically CONNECTED) | F1: stronger board edges\nR: deploy | E: turn chess heading | Q: stow | Z/C: body-only turn | T: reset to zone start\nMouse: orbit camera | Esc: capture/release | crossing a cell requires Pawn heading"
	help_label.add_theme_font_size_override("font_size", 14)
	content.add_child(help_label)
	_update_hud()

func _physics_process(_delta: float) -> void:
	if pawn != null and terrain != null:
		pawn.lane_index = int(terrain.call("zone_index", pawn.global_position.z))
	_update_hud()

func _process(delta: float) -> void:
	_update_camera(delta)

func _update_camera(delta: float) -> void:
	if pawn == null or camera == null:
		return
	var desired_target: Vector3 = pawn.global_position + Vector3.UP * 1.13
	camera_target = camera_target.lerp(desired_target, clampf(delta * 7.0, 0.0, 1.0))
	var lateral := Vector3(sin(camera_yaw), 0, cos(camera_yaw))
	var desired := camera_target + lateral * camera_distance * cos(camera_pitch) + Vector3.UP * camera_distance * (0.24 - sin(camera_pitch))
	camera.global_position = camera.global_position.lerp(desired, clampf(delta * 8.0, 0.0, 1.0))
	camera.look_at(camera_target, Vector3.UP)

func _input(event: InputEvent) -> void:
	if event is InputEventMouseMotion and Input.mouse_mode == Input.MOUSE_MODE_CAPTURED:
		camera_yaw -= event.relative.x * 0.004
		camera_pitch = clampf(camera_pitch + event.relative.y * 0.003, -0.7, 0.5)
	elif event is InputEventMouseButton and event.button_index == MOUSE_BUTTON_LEFT and event.pressed:
		# Unity pawn_player.cs: click resets and triggers the attack animation.
		# This primitive arm gesture does not deal combat damage.
		if pawn != null:
			pawn.trigger_attack()

func _unhandled_key_input(event: InputEvent) -> void:
	if event.physical_keycode == KEY_SPACE:
		if event.pressed and not event.echo:
			pawn.queue_jump()
		elif not event.pressed:
			pawn.release_jump()
		get_viewport().set_input_as_handled()
		return
	if not event.pressed or event.echo:
		return
	match event.physical_keycode:
		KEY_1, KEY_2, KEY_3, KEY_4, KEY_5:
			_teleport_to_zone(int(event.physical_keycode) - int(KEY_1))
		KEY_R:
			pawn.device.call("request_deploy")
		KEY_E:
			pawn.device.call("request_turn")
		KEY_Q:
			pawn.device.call("request_stow")
		KEY_Z:
			pawn.rotate_body_only(-90.0)
		KEY_C:
			pawn.rotate_body_only(90.0)
		KEY_T:
			_teleport_to_zone(pawn.lane_index)
		KEY_F1:
			grid_debug_visible = not grid_debug_visible
			terrain.call("set_board_debug_visible", grid_debug_visible)
		KEY_ESCAPE:
			var mode := Input.MOUSE_MODE_VISIBLE if Input.mouse_mode == Input.MOUSE_MODE_CAPTURED else Input.MOUSE_MODE_CAPTURED
			Input.set_mouse_mode(mode)
	get_viewport().set_input_as_handled()

func _teleport_to_zone(index: int) -> void:
	if terrain == null or index < 0 or index >= 5:
		return
	var z: float = float(terrain.call("spawn_z", index))
	var y: float = float(terrain.call("height_at", 0.0, z))
	pawn.call("reset_at", 0.0, y, z, index)
	camera_target = pawn.global_position + Vector3.UP

func _update_hud() -> void:
	if pawn == null or info == null:
		return
	var zone_name: String = ZONE_NAMES[clampi(pawn.lane_index, 0, 4)]
	info.text = "CheRPG | CONNECTED BOARD MOTION LAB 0.0.11v\n" \
		+ "ZONE %d/5: %s | MOVE: %s | FLOOR: %.1f deg\n" % [pawn.lane_index + 1, zone_name, pawn.move_state, pawn.floor_deg] \
		+ "BODY YAW: %.0f deg | CHESS HEADING: %s\n" % [rad_to_deg(pawn.avatar.rotation.y), pawn.HEADING_NAMES[pawn.heading_index]] \
		+ "JUMP: %s | COUNT: %d | DEVICE: %s | %s\n" % [pawn.jump_state, pawn.jump_count, pawn.device.call("phase_name"), pawn.device.reason] \
		+ "TILE: (%d,%d) | RULE: %s | INPUT: (%.2f,%.2f) | SPEED: %.2f m/s" % [pawn.current_cell.x, pawn.current_cell.y, ("RESISTANCE" if pawn.resistance_time > 0.0 else "CLEAR"), pawn.smoothed_strafe, pawn.smoothed_input, Vector2(pawn.velocity.x, pawn.velocity.z).length()]

func _run_smoke_test() -> void:
	# Optional, user-initiated only. This does NOT attempt gameplay validation.
	assert(terrain != null and terrain.get_node_or_null("ContinuousGroundCollision") != null)
	assert(pawn != null and pawn.device != null)
	assert(pawn.upper_leg.size() == 2 and pawn.knee.size() == 2)
	assert(pawn.device.components.size() == 4)
	for i in range(5):
		var z: float = float(terrain.call("spawn_z", i))
		assert(int(terrain.call("zone_index", z)) == i)
	_teleport_to_zone(0)
	print("CHERPG_GODOT_CONNECTED_MAP_STRUCTURE_OK / USER PLAYTEST REQUIRED")
	get_tree().quit(0)
