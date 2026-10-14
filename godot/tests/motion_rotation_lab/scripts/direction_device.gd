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
var stowed_ring: MeshInstance3D
var rigid_open_material: StandardMaterial3D
var rigid_closed_material: StandardMaterial3D
var heading_pivot: Node3D
var preview_root: Node3D
var tile_outline_root: Node3D
var ghost_color: StandardMaterial3D
var preview_reason := "NO PREVIEW"
var dark: StandardMaterial3D
var silver: StandardMaterial3D
var accent: StandardMaterial3D

func bind_pawn(character: CharacterBody3D) -> void:
	pawn = character
	dark = _mat(Color("38434a"),0.62)
	silver = _mat(Color("738188"),0.48)
	accent = _mat(Color("2b9aab"),0.25)
	_make_torus("PermanentWaistBelt",0.206,0.023,dark)
	# The two rings are rigid, constant-radius objects. Crossfade assembly
	# states instead of distorting a torus with animated scale.
	rigid_closed_material = _mat(Color("38434a"),0.62)
	rigid_open_material = _mat(Color("38434a"),0.62)
	rigid_closed_material.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	rigid_open_material.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	stowed_ring = _make_torus("CollapsedRigidWaistRing",CLOSED_RADIUS,0.024,rigid_closed_material)
	opening_ring = _make_torus("DeployedRigidWaistRing",OPEN_RADIUS,0.024,rigid_open_material)
	_make_box(self,"FrontBuckle",Vector3(0,WAIST_Y,-0.207),Vector3(0.085,0.055,0.039),silver)
	for i in range(4):
		var angle: float = deg_to_rad(ANCHOR_ANGLES[i])
		var rail := _make_box(self,"ACTUATOR_%d"%(i+1),Vector3.ZERO,Vector3(.455,.046,.046),silver)
		var joint := _make_cylinder("JOINT_%d"%(i+1),0.040,0.06,dark)
		# Rigid telescoping pieces: extension is measured by their overlap
		# and translation, NEVER by lengthwise scaling.
		var upper := _make_cylinder("ANCHOR_UPPER_%d"%(i+1),0.025,0.316,silver)
		var lower := _make_cylinder("ANCHOR_LOWER_%d"%(i+1),0.018,0.31,silver)
		var tip := _make_cylinder("ANCHOR_SLIDING_TIP_%d"%(i+1),0.014,0.28,silver)
		var collar := _make_cylinder("ANCHOR_COLLAR_%d"%(i+1),0.035,0.069,dark)
		var shoe := _make_cylinder("ANCHOR_FOOT_%d"%(i+1),FOOT_RADIUS,FOOT_THICKNESS,dark)
		components.append({"angle":angle,"rail":rail,"joint":joint,"upper":upper,
			"lower":lower,"tip":tip,"collar":collar,"shoe":shoe})
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
	_build_hologram()
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

func _build_hologram() -> void:
	# Required device clearance diameter: Ø(2*(.68+.075))=1.51m.
	# Also draw the CURRENT 4m x 4m board tile independently.
	preview_root = Node3D.new()
	preview_root.name = "F_HoldRequiredFootprintHologram"
	add_child(preview_root)
	ghost_color = StandardMaterial3D.new()
	ghost_color.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	ghost_color.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	ghost_color.cull_mode = BaseMaterial3D.CULL_DISABLED
	ghost_color.albedo_color = Color(0.18,0.91,0.75,0.24)
	var area := MeshInstance3D.new()
	area.name = "RequiredClearanceSquare_1p51m"
	var area_mesh := BoxMesh.new()
	area_mesh.size = Vector3(2.0*(OPEN_RADIUS+FOOT_RADIUS),0.012,2.0*(OPEN_RADIUS+FOOT_RADIUS))
	area.mesh = area_mesh
	area.material_override = ghost_color
	preview_root.add_child(area)
	var disk_mesh := CylinderMesh.new()
	disk_mesh.top_radius = FOOT_RADIUS
	disk_mesh.bottom_radius = FOOT_RADIUS
	disk_mesh.height = .018
	disk_mesh.radial_segments = 16
	for i in range(4):
		var a: float = deg_to_rad(ANCHOR_ANGLES[i])
		var shoe := MeshInstance3D.new()
		shoe.name = "AnchorFootPrint_%d" % (i + 1)
		shoe.mesh = disk_mesh
		shoe.material_override = ghost_color
		shoe.position = Vector3(OPEN_RADIUS*cos(a),.025,-OPEN_RADIUS*sin(a))
		preview_root.add_child(shoe)
	# Full tile boundary is a true 4m x 4m SQUARE, aligned to board origin.
	tile_outline_root = Node3D.new()
	tile_outline_root.name = "WorldAligned4mTileBorder"
	preview_root.add_child(tile_outline_root)
	for i in range(4):
		var side := MeshInstance3D.new()
		side.name = "FourMetreTileEdge_%d" % i
		var edge := BoxMesh.new()
		edge.size = Vector3(4.0,0.018,0.024) if i < 2 else Vector3(0.024,0.018,4.0)
		side.mesh = edge
		side.material_override = ghost_color
		side.position = Vector3(0.0,.01,(-2.0 if i == 0 else 2.0)) if i < 2 else Vector3((-2.0 if i == 2 else 2.0),.01,0.0)
		tile_outline_root.add_child(side)
	preview_root.visible = false

func set_preview_held(held: bool) -> void:
	if preview_root == null:
		return
	if not held or phase != Phase.STOWED:
		preview_root.visible = false
		return
	preview_root.visible = true
	preview_root.position = Vector3(0.0,0.08,0.0)
	var tile: Vector2i = BOARD_RULES.cell_at(pawn.global_position,pawn.board_origin)
	var center: Vector3 = BOARD_RULES.cell_center(tile,pawn.board_origin)
	tile_outline_root.position = Vector3(center.x-pawn.global_position.x,0.0,center.z-pawn.global_position.z)
	var valid: bool = pawn != null and pawn.is_on_floor() and Vector2(pawn.velocity.x,pawn.velocity.z).length() < .15
	if valid:
		var result: Dictionary = _probe_all_feet()
		valid = bool(result["ok"])
		preview_reason = "ANCHOR CLEAR" if valid else str(result["reason"])
	else:
		preview_reason = "STOP ON THE GROUND TO INSTALL"
	ghost_color.albedo_color = Color(0.13,0.87,0.63,.25) if valid else Color(1.0,.20,.16,.25)

func request_toggle() -> void:
	if phase == Phase.STOWED:
		request_deploy()
	elif phase == Phase.GROUNDED:
		request_stow()
	else:
		reason = "WAIT FOR DEVICE ANIMATION"

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

func request_turn(step: int = 1) -> void:
	if abs(step) != 1:
		return
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
	turn_target_index = posmod(pawn.heading_index + step, 4)
	heading_start = heading_visual
	heading_goal = heading_visual - float(step) * PI/2.0
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
		# The 1.36-m deployed ring plus foot diameter stays inside a 4x4-m tile.
		if maxf(absf(dx),absf(dz))+FOOT_RADIUS >= BOARD_RULES.HALF_TILE_M:
			return {"ok":false,"reason":"RING EXCEEDS BOARD TILE","contacts":[]}
		contacts.append({"x":dx,"z":dz,"center_y":center_y-pawn.global_position.y,
			"normal":normal,"stroke":length,"correction":highest_correction})
	return {"ok":true,"reason":"ALL FOUR FEET SUPPORTED","contacts":contacts}

func _apply_pose(ring_frac: float, anchor_frac: float) -> void:
	if opening_ring == null:
		return
	# NO runtime scale anywhere: ring sizes and rod lengths are immutable.
	# Small waist ring fades out as the larger rigid assembly fades in.
	var closed_alpha: float = 1.0-smoothstep(0.13,0.72,ring_frac)
	var open_alpha: float = smoothstep(0.30,0.96,ring_frac)
	var closed_color: Color = rigid_closed_material.albedo_color
	closed_color.a = closed_alpha
	rigid_closed_material.albedo_color = closed_color
	var open_color: Color = rigid_open_material.albedo_color
	open_color.a = open_alpha
	rigid_open_material.albedo_color = open_color
	stowed_ring.visible = closed_alpha > 0.01
	opening_ring.visible = open_alpha > 0.01
	heading_pivot.visible = ring_frac > 0.35
	heading_pivot.rotation.y = heading_visual
	for i in range(4):
		var row: Dictionary = components[i]
		var a: float = row["angle"]
		var dx: float = cos(a)
		var dz: float = -sin(a)
		var distance: float = lerpf(0.225,OPEN_RADIUS,ring_frac)
		var radial_center: float = lerpf(.213,.45,ring_frac)
		var rail: MeshInstance3D = row["rail"]
		# Every box's original mesh dimensions are held constant.
		rail.position = Vector3(radial_center*dx,WAIST_Y,radial_center*dz)
		rail.rotation.y = a
		rail.visible = ring_frac > .10
		var hinge: MeshInstance3D = row["joint"]
		hinge.position = Vector3(distance*dx,WAIST_Y,distance*dz)
		hinge.visible = ring_frac > .10
		var upper: MeshInstance3D = row["upper"]
		var lower: MeshInstance3D = row["lower"]
		var tip: MeshInstance3D = row["tip"]
		var collar: MeshInstance3D = row["collar"]
		var shoe: MeshInstance3D = row["shoe"]
		var ground_center_y: float = 0.055
		var ground_normal := Vector3.UP
		if contact_cache.size() == 4:
			ground_center_y = float(contact_cache[i]["center_y"])
			ground_normal = contact_cache[i]["normal"]
		var top_end: float = WAIST_Y-0.012
		var bottom_top: float = ground_center_y+FOOT_THICKNESS*.5
		# Fixed-length sections slide over one another. At full extension,
		# upper spans top_end→COLLAR_Y, lower spans collar→0.11m, and the
		# tip reaches the actual floor. Varying stroke alters only overlap.
		upper.position = Vector3(distance*dx,
			lerpf(WAIST_Y-.02,(top_end+COLLAR_Y)*.5,anchor_frac),distance*dz)
		lower.position = Vector3(distance*dx,
			lerpf(WAIST_Y-.07,COLLAR_Y-.155,anchor_frac),distance*dz)
		tip.position = Vector3(distance*dx,
			lerpf(WAIST_Y-.10,bottom_top+.14,anchor_frac),distance*dz)
		collar.position = Vector3(distance*dx,
			lerpf(WAIST_Y-.055,COLLAR_Y,anchor_frac),distance*dz)
		shoe.position = Vector3(distance*dx,
			lerpf(WAIST_Y-.1,ground_center_y,anchor_frac),distance*dz)
		upper.visible = anchor_frac > 0.10
		lower.visible = anchor_frac > 0.10
		tip.visible = anchor_frac > 0.15
		collar.visible = anchor_frac > 0.10
		shoe.visible = anchor_frac > 0.13
		shoe.quaternion = Quaternion.IDENTITY.slerp(
			Quaternion(Vector3.UP,ground_normal),anchor_frac)
