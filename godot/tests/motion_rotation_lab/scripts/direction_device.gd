extends Node3D
## Basic geometric ring + four independently raycast/adjusted anchor shoes.
## Move the Pawn's chess HEADING only: its body yaw never changes.
const WAIST_Y := 0.748
const CLOSED_RADIUS := 0.232
const OPEN_RADIUS := 0.68
const COLLAR_Y := 0.420
const FOOT_THICKNESS := 0.052
const FOOT_RADIUS := 0.075
const MIN_STROKE := 0.18
const MAX_STROKE := 0.54
const TWEEN_SECONDS := 1.8
const TURN_SECONDS := 0.62
const ANCHOR_ANGLES := [45.0, 135.0, 225.0, 315.0]
const BOARD_RULES = preload("res://scripts/board_rules.gd")
enum Phase {STOWED, DEPLOYING, GROUNDED, TURNING, RETRACTING}
var phase: Phase = Phase.STOWED
var phase_time := 0.0
var heading_visual := 0.0
var heading_start := 0.0
var heading_goal := 0.0
var turn_target_index := 0
var reason := "READY"
var locked_cell: Vector2i = Vector2i.ZERO
var pawn
var components: Array[Dictionary] = []
var contact_cache: Array[Dictionary] = []
var opening_ring: MeshInstance3D
var heading_pivot: Node3D
var dark: StandardMaterial3D
var silver: StandardMaterial3D
var accent: StandardMaterial3D

func bind_pawn(character: CharacterBody3D) -> void:
	pawn = character
	dark = _mat(Color("38434a"),0.62)
	silver = _mat(Color("738188"),0.48)
	accent = _mat(Color("2b9aab"),0.25)
	_make_torus("PermanentWaistBelt",0.206,0.023,dark)
	opening_ring = _make_torus("ExpandingRing",OPEN_RADIUS,0.024,dark)
	_make_box(self,"FrontBuckle",Vector3(0,WAIST_Y,-0.207),Vector3(0.085,0.055,0.039),silver)
	for i in range(4):
		var angle: float = deg_to_rad(ANCHOR_ANGLES[i])
		var rail := _make_box(self,"ACTUATOR_%d"%(i+1),Vector3.ZERO,Vector3(.455,.046,.046),silver)
		var joint := _make_cylinder("JOINT_%d"%(i+1),0.040,0.06,dark)
		var upper := _make_cylinder("ANCHOR_UPPER_%d"%(i+1),0.025,1.0,silver)
		var lower := _make_cylinder("ANCHOR_LOWER_%d"%(i+1),0.018,1.0,silver)
		var collar := _make_cylinder("ANCHOR_COLLAR_%d"%(i+1),0.035,0.069,dark)
		var shoe := _make_cylinder("ANCHOR_FOOT_%d"%(i+1),FOOT_RADIUS,FOOT_THICKNESS,dark)
		components.append({"angle":angle,"rail":rail,"joint":joint,"upper":upper,
			"lower":lower,"collar":collar,"shoe":shoe})
	heading_pivot = Node3D.new()
	heading_pivot.name = "ChessHeadingMarker_NoBodyYaw"
	add_child(heading_pivot)
	heading_pivot.position.y = WAIST_Y
	_make_box(heading_pivot,"ArrowShaft",Vector3(0.52,0.052,0),Vector3(0.14,0.03,0.035),accent)
	var arrowhead := _make_cylinder("ArrowHead",0.062,0.11,accent)
	arrowhead.reparent(heading_pivot)
	arrowhead.position = Vector3(.645,.052,0)
	arrowhead.rotation.z = -PI/2.0
	heading_visual = PI/2.0
	instant_stow()

func _mat(color: Color, metal: float) -> StandardMaterial3D:
	var m := StandardMaterial3D.new()
	m.albedo_color = color
	m.metallic = metal
	m.roughness = 0.73
	return m

func _make_box(parent: Node3D, title: String, at: Vector3, size: Vector3, mat: Material) -> MeshInstance3D:
	var mesh := BoxMesh.new()
	mesh.size = size
	var obj := MeshInstance3D.new()
	obj.name = title
	obj.mesh = mesh
	obj.material_override = mat
	parent.add_child(obj)
	obj.position = at
	return obj

func _make_cylinder(title: String, radius: float, height: float, mat: Material) -> MeshInstance3D:
	var mesh := CylinderMesh.new()
	mesh.top_radius = radius
	mesh.bottom_radius = radius
	mesh.height = height
	mesh.radial_segments = 10
	var obj := MeshInstance3D.new()
	obj.name = title
	obj.mesh = mesh
	obj.material_override = mat
	add_child(obj)
	return obj

func _make_torus(title: String, major: float, minor: float, mat: Material) -> MeshInstance3D:
	var mesh := TorusMesh.new()
	mesh.inner_radius = major - minor
	mesh.outer_radius = major + minor
	mesh.rings = 24
	mesh.ring_segments = 8
	var obj := MeshInstance3D.new()
	obj.name = title
	obj.mesh = mesh
	obj.material_override = mat
	add_child(obj)
	obj.position.y = WAIST_Y
	return obj

func is_busy() -> bool:
	return phase != Phase.STOWED

func phase_name() -> String:
	return ["STOWED","EXPANDING","ANCHORED","CHANGING HEADING","RETRACTING"][phase]

func instant_stow() -> void:
	phase = Phase.STOWED
	phase_time = 0.0
	contact_cache.clear()
	reason = "READY"
	if pawn != null:
		heading_visual = PI/2.0 - float(pawn.heading_index) * PI/2.0
	_apply_pose(0.0,0.0)

func request_deploy() -> void:
	if pawn == null or not pawn.is_on_floor() or pawn.velocity.y > 0.01 or Vector2(pawn.velocity.x,pawn.velocity.z).length() > 0.15:
		reason = "STOP AND STAND ON THE GROUND"
		return
	if phase != Phase.STOWED:
		return
	var result := _probe_all_feet()
	if not bool(result["ok"]):
		reason = str(result["reason"])
		return
	contact_cache = result["contacts"]
	locked_cell = BOARD_RULES.cell_at(pawn.global_position, pawn.board_origin)
	phase_time = 0.0
	phase = Phase.DEPLOYING
	reason = "SUPPORT LOCKED"

func request_turn() -> void:
	if pawn == null or not pawn.is_on_floor():
		reason = "GROUNDED BODY REQUIRED"
		return
	if phase != Phase.GROUNDED:
		return
	if locked_cell != BOARD_RULES.cell_at(pawn.global_position, pawn.board_origin):
		reason = "BOARD ANCHOR DISCONNECTED: TILE CHANGED"
		return
	# Recheck during active use: if the ground has become unsafe, don't turn.
	var result := _probe_all_feet()
	if not bool(result["ok"]):
		reason = str(result["reason"])
		return
	contact_cache = result["contacts"]
	turn_target_index = (pawn.heading_index + 1) % 4
	heading_start = heading_visual
	heading_goal = heading_visual - PI/2.0
	phase = Phase.TURNING
	phase_time = 0.0

func request_stow() -> void:
	if phase != Phase.GROUNDED:
		return
	phase = Phase.RETRACTING
	phase_time = 0.0

func _physics_process(delta: float) -> void:
	if pawn == null:
		return
	if phase == Phase.DEPLOYING:
		phase_time += delta
		var p := clampf(phase_time/TWEEN_SECONDS,0.0,1.0)
		_apply_pose(smoothstep(0.0,0.46,p),smoothstep(0.38,0.95,p))
		if p >= 1.0:
			phase = Phase.GROUNDED
	elif phase == Phase.RETRACTING:
		phase_time += delta
		var p := clampf(phase_time/TWEEN_SECONDS,0.0,1.0)
		_apply_pose(1.0-smoothstep(0.45,1.0,p),1.0-smoothstep(0.0,0.60,p))
		if p >= 1.0:
			instant_stow()
	elif phase == Phase.TURNING:
		phase_time += delta
		var p := smoothstep(0.0,1.0,clampf(phase_time/TURN_SECONDS,0.0,1.0))
		heading_visual = lerpf(heading_start,heading_goal,p)
		_apply_pose(1.0,1.0)
		if phase_time >= TURN_SECONDS:
			pawn.heading_index = turn_target_index
			phase = Phase.GROUNDED
			reason = "DIRECTION CHANGED / PAWN BODY UNROTATED"
	elif phase == Phase.GROUNDED:
		_apply_pose(1.0,1.0)

func _probe_all_feet() -> Dictionary:
	if pawn == null:
		return {"ok":false,"reason":"NO PAWN","contacts":[]}
	var tile: Vector2i = BOARD_RULES.cell_at(pawn.global_position, pawn.board_origin)
	var center: Vector3 = BOARD_RULES.cell_center(tile, pawn.board_origin)
	var offset_x: float = absf(pawn.global_position.x - center.x)
	var offset_z: float = absf(pawn.global_position.z - center.z)
	# Extended ring + four feet must stay inside this tile.
	if maxf(offset_x, offset_z) + OPEN_RADIUS + FOOT_RADIUS >= BOARD_RULES.HALF_TILE_M:
		return {"ok":false,"reason":"ALIGN TO TILE CENTER BEFORE DEPLOYING","contacts":[]}
	var space := get_world_3d().direct_space_state
	var contacts: Array[Dictionary] = []
	for i in range(4):
		var a: float = deg_to_rad(ANCHOR_ANGLES[i])
		var dx := OPEN_RADIUS * cos(a)
		var dz := -OPEN_RADIUS * sin(a)
		var xy: Vector3 = pawn.global_position + Vector3(dx,0,dz)
		var ray := PhysicsRayQueryParameters3D.create(xy+Vector3.UP*1.7,xy+Vector3.DOWN*0.8,1,[pawn.get_rid()])
		var hit := space.intersect_ray(ray)
		if hit.is_empty():
			return {"ok":false,"reason":"ANCHOR %d: NO GROUND" % (i+1),"contacts":[]}
		var normal: Vector3 = hit["normal"]
		if normal.y < 0.80:
			return {"ok":false,"reason":"ANCHOR %d: FOOT TOO TILTED" % (i+1),"contacts":[]}
		var ground_y: float = hit["position"].y
		var highest_correction := 0.0
		# Sample the actual collider below the pad rim so the pad won't clip small bumps.
		for j in range(8):
			var theta := TAU*float(j)/8.0
			var px := FOOT_RADIUS*cos(theta)
			var pz := FOOT_RADIUS*sin(theta)
			var world_center: Vector3 = xy + Vector3(px,0,pz)
			var sub_ray := PhysicsRayQueryParameters3D.create(world_center+Vector3.UP*1.7,world_center+Vector3.DOWN*.8,1,[pawn.get_rid()])
			var sample := space.intersect_ray(sub_ray)
			if sample.is_empty():
				return {"ok":false,"reason":"ANCHOR %d: FOOT EDGE UNSUPPORTED"%(i+1),"contacts":[]}
			var floor_sample_y: float = sample["position"].y
			var plane_y: float = ground_y - (normal.x*px + normal.z*pz)/normal.y
			highest_correction = maxf(highest_correction,floor_sample_y-plane_y)
		var center_y := ground_y + FOOT_THICKNESS*0.5 + highest_correction
		var length: float = COLLAR_Y-(center_y-pawn.global_position.y+FOOT_THICKNESS*.5)
		if length < MIN_STROKE or length > MAX_STROKE:
			return {"ok":false,"reason":"ANCHOR %d: STROKE %.2fm OUT OF RANGE" % [i+1,length],"contacts":[]}
		# The 1.36-m deployed ring plus foot diameter stays inside a 2x2-m tile.
		if maxf(absf(dx),absf(dz))+FOOT_RADIUS >= 1.0:
			return {"ok":false,"reason":"RING EXCEEDS 2-M TILE","contacts":[]}
		contacts.append({"x":dx,"z":dz,"center_y":center_y-pawn.global_position.y,
			"normal":normal,"stroke":length,"correction":highest_correction})
	return {"ok":true,"reason":"ALL FOUR FEET SUPPORTED","contacts":contacts}

func _apply_pose(ring_frac: float,anchor_frac: float) -> void:
	if opening_ring == null:
		return
	var r := lerpf(CLOSED_RADIUS,OPEN_RADIUS,ring_frac)
	opening_ring.scale = Vector3(r/OPEN_RADIUS,r/OPEN_RADIUS,r/OPEN_RADIUS)
	heading_pivot.rotation.y = heading_visual
	heading_pivot.scale = Vector3.ONE * (r/OPEN_RADIUS)
	for i in range(4):
		var row: Dictionary = components[i]
		var a: float = row["angle"]
		var dx: float = cos(a)
		var dz: float = -sin(a)
		var rail_length := lerpf(0.045,0.455,ring_frac)
		var distance := lerpf(0.225,OPEN_RADIUS,ring_frac)
		var radial_center := lerpf(.213,.45,ring_frac)
		var rail: MeshInstance3D = row["rail"]
		rail.position = Vector3(radial_center*dx,WAIST_Y,radial_center*dz)
		rail.rotation.y = a
		rail.scale = Vector3(rail_length/.455,1,1)
		var hinge: MeshInstance3D = row["joint"]
		hinge.position = Vector3(distance*dx,WAIST_Y,distance*dz)
		var upper: MeshInstance3D = row["upper"]
		var lower: MeshInstance3D = row["lower"]
		var collar: MeshInstance3D = row["collar"]
		var shoe: MeshInstance3D = row["shoe"]
		var ground_center_y := 0.055
		var ground_normal := Vector3.UP
		if contact_cache.size() == 4:
			ground_center_y = float(contact_cache[i]["center_y"])
			ground_normal = contact_cache[i]["normal"]
		var top_end := WAIST_Y-0.012
		upper.position = Vector3(distance*dx,lerpf(WAIST_Y-.02,(top_end+COLLAR_Y)*.5,anchor_frac),distance*dz)
		upper.scale = Vector3(1,lerpf(.045,top_end-COLLAR_Y,anchor_frac),1)
		collar.position = Vector3(distance*dx,lerpf(WAIST_Y-.055,COLLAR_Y,anchor_frac),distance*dz)
		collar.scale = Vector3(1,lerpf(.35,1,anchor_frac),1)
		var bottom_top := ground_center_y+FOOT_THICKNESS*.5
		var bar_end := lerpf(WAIST_Y-.07,bottom_top,anchor_frac)
		lower.position = Vector3(distance*dx,lerpf(WAIST_Y-.07,(COLLAR_Y+bottom_top)*.5,anchor_frac),distance*dz)
		lower.scale = Vector3(1,lerpf(.045,maxf(.01,COLLAR_Y-bar_end),anchor_frac),1)
		shoe.position = Vector3(distance*dx,lerpf(WAIST_Y-.1,ground_center_y,anchor_frac),distance*dz)
		shoe.scale = Vector3(1,lerpf(.05,1.0,anchor_frac),1)
		shoe.quaternion = Quaternion.IDENTITY.slerp(Quaternion(Vector3.UP,ground_normal),anchor_frac)
