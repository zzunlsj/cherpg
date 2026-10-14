extends SceneTree
## Short real Godot geometry test: no scaling while walking, running, crouching,
## jumping, grabbing, mantling, attacking or extending/retracting the device.
## Runtime <10 seconds. Not a long gameplay playtest.

var baseline: Dictionary = {}
var checked := 0

func _initialize() -> void:
	call_deferred("_run")

func _capture(node: Node) -> void:
	if node is MeshInstance3D:
		var mesh_node: MeshInstance3D = node as MeshInstance3D
		baseline[mesh_node.get_instance_id()] = {
			"scale": mesh_node.scale,
			"mesh_size": mesh_node.mesh.get_aabb().size,
			"node": mesh_node
		}
	for child in node.get_children():
		_capture(child)

func _assert_unchanged(phase: String) -> bool:
	for entry in baseline.values():
		var mesh_node: MeshInstance3D = entry["node"]
		if not is_instance_valid(mesh_node):
			push_error("CHERPG_RIGID_GEOMETRY_FAIL missing part " + phase)
			return false
		if not mesh_node.scale.is_equal_approx(entry["scale"]):
			push_error("CHERPG_RIGID_GEOMETRY_FAIL scaled part %s on %s" % [mesh_node.name,phase])
			return false
		if not mesh_node.mesh.get_aabb().size.is_equal_approx(entry["mesh_size"]):
			push_error("CHERPG_RIGID_GEOMETRY_FAIL resized mesh %s on %s" % [mesh_node.name,phase])
			return false
	checked += 1
	return true

func _run() -> void:
	var scene: PackedScene = load("res://scenes/MotionLab.tscn")
	if scene == null:
		quit(1)
		return
	var lab: Node3D = scene.instantiate()
	root.add_child(lab)
	await physics_frame
	var pawn: CharacterBody3D = lab.pawn
	var visual: Node3D = pawn.avatar
	var device: Node3D = pawn.device
	_capture(visual)
	_capture(device)
	var head: Node3D = visual.find_child("HEAD_PawnOrb",true,false) as Node3D
	var head_stand_y: float = head.global_position.y
	if baseline.size() < 28:
		push_error("CHERPG_RIGID_GEOMETRY_FAIL missing visual/anchor components")
		quit(1)
		return
	for i in range(10):
		var delta := 1.0 / 60.0
		pawn._update_gait(delta,4.0,false,1.0)
		if not _assert_unchanged("walk"):
			quit(1)
			return
		pawn._update_gait(delta,6.0,true,1.0)
		if not _assert_unchanged("run"):
			quit(1)
			return
		pawn._update_air_pose(delta)
		if not _assert_unchanged("jump"):
			quit(1)
			return
		pawn._update_climb_pose(delta,Vector2(0.6,0.8))
		if not _assert_unchanged("climb"):
			quit(1)
			return
		pawn._update_mantle_pose(float(i)/9.0,delta)
		if not _assert_unchanged("mantle"):
			quit(1)
			return
		pawn.crouch_blend = float(i)/9.0
		pawn._update_crouch_pose(delta,0.7,1.0)
		pawn.upper_body_pivot.rotation.x = -0.94*pawn.crouch_blend
		if not _assert_unchanged("crouch"):
			quit(1)
			return
		pawn.attack_timer = 0.36
		pawn._apply_attack_pose(delta)
		if not _assert_unchanged("attack"):
			quit(1)
			return
		device._apply_pose(float(i)/9.0,float(i)/9.0)
		if not _assert_unchanged("anchor"):
			quit(1)
			return
	if head.global_position.y > head_stand_y - 0.32:
		push_error("CHERPG_RIGID_GEOMETRY_FAIL crouch did not lower head via joints")
		quit(1)
		return
	if not visual.scale.is_equal_approx(Vector3.ONE):
		push_error("CHERPG_RIGID_GEOMETRY_FAIL scaled entire Pawn")
		quit(1)
		return
	if not device.scale.is_equal_approx(Vector3.ONE):
		push_error("CHERPG_RIGID_GEOMETRY_FAIL scaled entire device")
		quit(1)
		return
	print("CHERPG_RIGID_ANIMATION_GEOMETRY_PASS meshes=%d samples=%d all poses no scale changes" % [baseline.size(),checked])
	quit(0)
