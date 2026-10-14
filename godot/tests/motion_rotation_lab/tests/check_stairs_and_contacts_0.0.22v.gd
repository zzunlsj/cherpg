extends SceneTree
## Short (<15s) real Godot physics validation of 16cm stairs and contact rig.
## No automatic 1-minute+ gameplay test. Fails CI if steps are still blocked.
var fail_reason := ""

func _key(code: Key, down: bool) -> void:
	var event := InputEventKey.new()
	event.keycode = code
	event.physical_keycode = code
	event.pressed = down
	Input.parse_input_event(event)

func _run() -> void:
	var packed: PackedScene = load("res://scenes/MotionLab.tscn")
	if packed == null:
		push_error("STAIR_CONTACT_FAIL scene not found")
		quit(1)
		return
	var lab: Node3D = packed.instantiate()
	root.add_child(lab)
	await physics_frame
	var pawn: CharacterBody3D = lab.pawn
	lab._teleport_to_station(9)
	lab.camera_yaw = 0.0
	lab.camera_elevation = 0.5
	lab._update_camera(1.0)
	for j in range(18):
		await physics_frame
		await process_frame
	var origin: Vector3 = pawn.global_position
	print("STAIRS_SPAWN position=%s" % str(origin))
	if origin.z < -14.25 or origin.y > 0.6:
		fail_reason = "station 10 spawn is inside stairs or floating"
	_key(KEY_W,true)
	var peak := origin.y
	var deepest := origin.z
	var planted := 0
	for j in range(190):
		await physics_frame
		await process_frame
		peak = maxf(peak,pawn.global_position.y)
		deepest = minf(deepest,pawn.global_position.z)
		for contact in pawn.foot_contact_valid:
			if contact:
				planted += 1
	_key(KEY_W,false)
	for j in range(15):
		await physics_frame
		await process_frame
	print("STAIRS_ASCENT peak_y=%.3f end_z=%.3f steps=%d attempts=%d last=%s foot_contacts=%d part_probes=%d" %
		[peak,deepest,pawn.step_up_count,pawn.step_probe_count,pawn.step_last_reason,planted,pawn.part_probes.size()])
	if pawn.step_up_count < 3:
		fail_reason += " step-up solver did not clear 3 risers"
	if peak < 0.52:
		fail_reason += " actual Pawn capsule did not gain enough elevation"
	if deepest > -17.1:
		fail_reason += " forward movement remains blocked on stair risers"
	if pawn.avatar.scale != Vector3.ONE:
		fail_reason += " avatar scaled during step animation"
	if pawn.part_probes.size() < 22:
		fail_reason += " collision proxies missing"
	if planted < 2:
		fail_reason += " no supporting foot contact detected"
	if not fail_reason.is_empty():
		push_error("STAIR_CONTACT_FAIL "+fail_reason)
		quit(1)
		return
	print("CHERPG_STAIRS_AND_TERRAIN_CONTACTS_PASS steps=%d top=%.3f" %
		[pawn.step_up_count,peak])
	quit(0)

func _initialize() -> void:
	call_deferred("_run")
