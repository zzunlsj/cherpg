extends SceneTree
## ONE-TIME authorized actual game-physics playtest for v0.0.20v.
## Drives real input events into the actual scene and checks its pawn movement,
## camera-orbit controls, stop jitter, running, and 90-degree top-down camera.
## Never invoked from game startup or default standalone Godot CI after v0.0.20v.

var lab: Node3D
var pawn: CharacterBody3D
var issues: Array[String] = []

func _initialize() -> void:
	call_deferred("_run_playtest")

func _key(code: Key, pressed: bool) -> void:
	var event := InputEventKey.new()
	event.keycode = code
	event.physical_keycode = code
	event.pressed = pressed
	Input.parse_input_event(event)

func _frames(n: int) -> void:
	for i in range(n):
		await physics_frame
		await process_frame

func _fail(msg: String) -> void:
	issues.append(msg)
	push_error("CHERPG_PLAYTEST_FAIL " + msg)

func _reset(yaw: float, elevation: float = 0.45) -> void:
	lab.call("_teleport_to_station",0)
	lab.camera_yaw = yaw
	lab.camera_elevation = elevation
	lab._update_camera(1.0)
	pawn.velocity = Vector3.ZERO

func _run_playtest() -> void:
	var packed: PackedScene = load("res://scenes/MotionLab.tscn")
	if packed == null:
		_fail("Could not instantiate real MotionLab scene")
		quit(1)
		return
	lab = packed.instantiate()
	root.add_child(lab)
	await _frames(8)
	pawn = lab.pawn as CharacterBody3D
	if pawn == null:
		_fail("Real CharacterBody3D Pawn missing")
		quit(1)
		return
	# Disable only chess-rule crossings; leave all world collisions enabled.
	# Otherwise an unrelated Pawn tile boundary could mask camera input.
	lab.board_rules_enabled = false
	pawn.board_rules_enabled = false
	print("CHERPG_PLAYTEST_START real physics, real controller, input event simulation")
	_reset(0.0)
	await _frames(5)
	_key(KEY_W,true)
	await _frames(48)
	var forward_a: Vector3 = pawn.global_position
	_key(KEY_W,false)
	print("CHERPG_PLAYTEST_CAMERA_0 position=%s speed=%.3f" % [str(forward_a),Vector2(pawn.velocity.x,pawn.velocity.z).length()])
	if forward_a.z >= 36.8 or absf(forward_a.x) > .45:
		_fail("W at camera yaw=0 did not move toward camera forward (-Z)")
	await _frames(24)
	var rest_velocity_a: float = Vector2(pawn.velocity.x,pawn.velocity.z).length()
	if rest_velocity_a > .61:
		_fail("Pawn keeps oscillating above increased 0.6m/s threshold after releasing W, speed=%.3f" % rest_velocity_a)

	_reset(PI/2.0)
	await _frames(5)
	_key(KEY_W,true)
	await _frames(48)
	var forward_b: Vector3 = pawn.global_position
	_key(KEY_W,false)
	print("CHERPG_PLAYTEST_CAMERA_90YAW position=%s" % str(forward_b))
	if forward_b.x >= -1.2 or absf(forward_b.z-38.0) > .50:
		_fail("W after turning camera 90 degrees failed to move in -X")

	_reset(PI/2.0,PI/2.0)
	await _frames(6)
	_key(KEY_W,true)
	await _frames(48)
	var forward_top: Vector3 = pawn.global_position
	_key(KEY_W,false)
	print("CHERPG_PLAYTEST_TOPDOWN_90 position=%s" % str(forward_top))
	if forward_top.x >= -1.2 or absf(forward_top.z-38.0) > .50:
		_fail("W at full 90-degree top-down camera did not keep orbit direction")

	_reset(0.0)
	await _frames(5)
	_key(KEY_CTRL,true)
	_key(KEY_W,true)
	await _frames(32)
	var running_speed: float = Vector2(pawn.velocity.x,pawn.velocity.z).length()
	_key(KEY_W,false)
	_key(KEY_CTRL,false)
	print("CHERPG_PLAYTEST_CTRL_RUN speed=%.3f cap=6.0" % running_speed)
	if running_speed < 4.2 or running_speed > 6.001:
		_fail("Ctrl run speed did not match 6m/s cap")
	await _frames(28)
	var at_rest: float = Vector2(pawn.velocity.x,pawn.velocity.z).length()
	print("CHERPG_PLAYTEST_RELEASE_STOP speed=%.3f" % at_rest)
	if at_rest > .61:
		_fail("Movement jitter continued after releasing input")

	_key(KEY_SHIFT,true)
	await _frames(10)
	if not pawn.crouching or pawn.running:
		_fail("Shift crouch / Ctrl sprint conflict")
	_key(KEY_SHIFT,false)
	await _frames(10)
	print("CHERPG_PLAYTEST_END issues=%d" % issues.size())
	if issues.is_empty():
		print("CHERPG_REAL_PLAYTEST_PASS camera yaw, top-down, Ctrl sprint, crouch, stop threshold")
		quit(0)
	else:
		quit(1)
