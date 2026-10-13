extends Node3D
## Standalone lab -- no shared world scenes or production maps.
const LANE_SCRIPT = preload("res://scripts/test_lane.gd")
const PAWN_SCRIPT = preload("res://scripts/pawn_controller.gd")
var lanes: Array[StaticBody3D] = []
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
	for i in range(5):
		var lane: StaticBody3D = LANE_SCRIPT.new()
		add_child(lane)
		lane.call("setup",i)
		lanes.append(lane)
	pawn = PAWN_SCRIPT.new()
	add_child(pawn)
	camera = Camera3D.new()
	camera.name = "FollowCamera"
	camera.fov = 65.0
	camera.current = true
	add_child(camera)
	pawn.set_movement_camera(camera)
	# Use the selected lane terrain height for initial spawn and resets.
	_teleport_to_lane(0)
	_build_ui()
	camera_target = pawn.global_position+Vector3.UP*1.1
	_update_camera(1.0)
	Input.set_mouse_mode(Input.MOUSE_MODE_CAPTURED)
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
	bg.custom_minimum_size = Vector2(520.0,170.0)
	hud.add_child(bg)
	var content := VBoxContainer.new()
	bg.add_child(content)
	info = Label.new()
	info.name = "MotionAndDeviceState"
	info.add_theme_font_size_override("font_size",16)
	content.add_child(info)
	help_label = Label.new()
	help_label.text = "WASD: CAMERA-RELATIVE MOVE (W = camera forward) | tile exit: Pawn heading only\nShift: run | Space: variable jump (same board rule) | 1-5: test terrain\nR: deploy | E: heading +90 deg | Q: stow | Z/C: body-only turn | F1: board debug | T: reset\nMouse: orbit camera | Esc: capture/release | forced motion not bound to a key"
	help_label.add_theme_font_size_override("font_size",15)
	content.add_child(help_label)
	_update_hud()

func _physics_process(_delta: float) -> void:
	_update_hud()

func _process(delta: float) -> void:
	_update_camera(delta)

func _update_camera(delta: float) -> void:
	if pawn == null or camera == null:
		return
	var desired_target: Vector3 = pawn.global_position+Vector3.UP*1.13
	camera_target = camera_target.lerp(desired_target,clampf(delta*7.0,0.0,1.0))
	var lateral := Vector3(sin(camera_yaw),0,cos(camera_yaw))
	var desired := camera_target + lateral * camera_distance * cos(camera_pitch) + Vector3.UP * camera_distance * (0.24-sin(camera_pitch))
	camera.global_position = camera.global_position.lerp(desired,clampf(delta*8.0,0.0,1.0))
	camera.look_at(camera_target,Vector3.UP)

func _input(event: InputEvent) -> void:
	if event is InputEventMouseMotion and Input.mouse_mode == Input.MOUSE_MODE_CAPTURED:
		camera_yaw -= event.relative.x*0.004
		camera_pitch = clampf(camera_pitch+event.relative.y*0.003,-0.7,0.5)

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
		KEY_1,KEY_2,KEY_3,KEY_4,KEY_5:
			var lane_id: int = int(event.physical_keycode)-int(KEY_1)
			_teleport_to_lane(lane_id)
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
			_teleport_to_lane(pawn.lane_index)
		KEY_F1:
			grid_debug_visible = not grid_debug_visible
			for lane in lanes:
				lane.call("set_board_debug_visible", grid_debug_visible)
		KEY_ESCAPE:
			var new_mode := Input.MOUSE_MODE_VISIBLE if Input.mouse_mode == Input.MOUSE_MODE_CAPTURED else Input.MOUSE_MODE_CAPTURED
			Input.set_mouse_mode(new_mode)
	get_viewport().set_input_as_handled()

func _teleport_to_lane(index: int) -> void:
	if index < 0 or index >= lanes.size():
		return
	var lane: StaticBody3D = lanes[index]
	var y: float = lane.call("height_at",0.0,9.3)
	pawn.call("reset_at",lane.global_position.x,y,9.3,index)
	camera_target = pawn.global_position+Vector3.UP

func _update_hud() -> void:
	if pawn == null or info == null:
		return
	var lane_name: String = ["FLAT", "8 DEG SLOPE", "15 DEG SLOPE", "UNEVEN", "30 DEG LIMIT"][pawn.lane_index]
	info.text = "CheRPG | CANON-ALIGNED CAMERA MOVEMENT LAB 0.0.9v\n" \
		+ "LANE %d/5: %s | MOVE: %s | FLOOR: %.1f deg\n" % [pawn.lane_index+1,lane_name,pawn.move_state,pawn.floor_deg] \
		+ "BODY YAW: %.0f deg | CHESS HEADING: %s\n" % [rad_to_deg(pawn.avatar.rotation.y), pawn.HEADING_NAMES[pawn.heading_index]] \
		+ "JUMP: %s | COUNT: %d | DEVICE: %s | %s\n" % [pawn.jump_state,pawn.jump_count,pawn.device.call("phase_name"),pawn.device.reason] \
		+ "TILE: (%d,%d) | RULE: %s | INPUT: (%.2f,%.2f) | SPEED: %.2f m/s" % [pawn.current_cell.x, pawn.current_cell.y, ("RESISTANCE" if pawn.resistance_time > 0.0 else "CLEAR"), pawn.smoothed_strafe, pawn.smoothed_input, Vector2(pawn.velocity.x,pawn.velocity.z).length()]

func _run_smoke_test() -> void:
	# Fail CI loudly on scene construction, ground generation or missing primitives.
	assert(lanes.size()==5,"Expected five independent terrain test lanes")
	assert(pawn != null and pawn.device != null,"Pawn/device not created")
	assert(pawn.upper_leg.size()==2 and pawn.knee.size()==2,"Leg pivots missing")
	assert(pawn.device.components.size()==4,"Expected four anchors")
	for i in range(5):
		_teleport_to_lane(i)
		await get_tree().physics_frame
		assert(pawn.lane_index==i,"Lane switching failed")
	_teleport_to_lane(0)
	for settle_frame in range(30):
		await get_tree().physics_frame
		if pawn.is_on_floor():
			break
	var ray := PhysicsRayQueryParameters3D.create(pawn.global_position+Vector3.UP*2.0,pawn.global_position+Vector3.DOWN*4.0,1,[pawn.get_rid()])
	var ground_hit: Dictionary = get_world_3d().direct_space_state.intersect_ray(ray)
	print("CHERPG_FLOOR_DIAGNOSTIC position=",pawn.global_position," velocity=",pawn.velocity," grounded=",pawn.is_on_floor()," ray_hit=",ground_hit.get("position","NONE"))
	if not pawn.is_on_floor():
		push_error("Pawn did not reach ground before anchor test")
		get_tree().quit(1)
		return
	var flat_probe: Dictionary = pawn.device.call("_probe_all_feet")
	assert(bool(flat_probe["ok"]),"Flat ground must allow four-foot grounding")
	pawn.device.call("request_deploy")
	assert(pawn.device.phase_name()=="EXPANDING","Deploy command was ignored")
	pawn.device.call("instant_stow")
	# Jump is separate from run. Verify takeoff, landing and device exclusion.
	pawn.queue_jump()
	await get_tree().physics_frame
	assert(pawn.jump_count >= 1,"Jump input did not create an upward impulse")
	assert(pawn.velocity.y > 0.0,"Jump must have positive vertical velocity")
	pawn.device.request_deploy()
	assert(pawn.device.phase_name() == "STOWED","Cannot deploy in mid-air")
	pawn.release_jump()
	for frame in range(100):
		await get_tree().physics_frame
		if pawn.is_on_floor() and pawn.jump_state == "GROUNDED":
			break
	assert(pawn.is_on_floor(),"Pawn did not land after jump")
	print("CHERPG_GODOT_TESTMAP_SMOKE_OK 5 lanes / 4 anchors / jump / landing")
	get_tree().quit(0)
