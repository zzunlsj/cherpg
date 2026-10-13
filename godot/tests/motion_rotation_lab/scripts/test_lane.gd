extends StaticBody3D
## CheRPG independent testing ground: 100m x 100m completely flat base;
## modular slope blocks and terrain specimens sit ON TOP of the flat base.
## The chess-board overlay is an editor/test visualization, not visible canon.
const BOARD_RULES = preload("res://scripts/board_rules.gd")
# All obstacle surfaces are independent from the large flat floor.
const WIDTH_M := 100.0
const DEPTH_M := 100.0
const TILE_M := 4.0
const RAMP_ANGLES := [8.0, 15.0, 30.0, 45.0, 60.0, 75.0, 90.0]
const RAMP_X := [-38.0, -26.0, -14.0, -2.0, 10.0, 22.0, 38.0]
const RAMP_Z := 19.0
const SPAWN_X := [0.0, -38.0, -26.0, -14.0, -2.0, 10.0, 22.0, 38.0, -22.0, 20.0]
const SPAWN_Z := [38.0, 30.0, 30.0, 30.0, 30.0, 30.0, 30.0, 30.0, -18.0, -18.0]
const GROUND_TOP_Y := 0.0
var grid_material: ShaderMaterial
var all_grid_materials: Array[ShaderMaterial] = []
var board_grid_visible := true
const CLIMBABLE_FROM_DEG := 30.0

func setup() -> void:
	name = "CheRPG_Flat100x100_WithSlopeTestStations"
	collision_layer = 1
	collision_mask = 0
	_create_flat_ground()
	for i in range(RAMP_ANGLES.size()):
		_create_ramp(i)
	_create_uneven_area()
	_create_stairs()
	_create_labels()

func _checker_material(light: Color, dark: Color) -> ShaderMaterial:
	var shader := Shader.new()
	shader.code = """
shader_type spatial;
render_mode cull_disabled, diffuse_burley;
uniform vec4 pale : source_color = vec4(0.60,0.69,0.64,1.0);
uniform vec4 deep : source_color = vec4(0.32,0.46,0.42,1.0);
uniform float border_opacity : hint_range(0.0,1.0) = 0.92;
uniform float board_visible : hint_range(0.0,1.0) = 1.0;
varying vec3 world_pos;
void vertex() {
	world_pos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
}
void fragment() {
	// 4m x 4m chess grid aligned to (x,z)=(0,0) in the same world.
	vec2 cell_uv = (world_pos.xz + vec2(2.0)) / 4.0;
	float dark_tile = mod(floor(cell_uv.x) + floor(cell_uv.y), 2.0);
	vec3 surface_color = mix(pale.rgb, deep.rgb, dark_tile * board_visible);
	vec2 d = min(fract(cell_uv), vec2(1.0) - fract(cell_uv));
	float edge_m = min(d.x, d.y) * 2.0;
	float outline = 1.0 - smoothstep(0.023,0.068,edge_m);
	ALBEDO = mix(surface_color,vec3(0.09,0.11,0.13),outline * border_opacity * board_visible);
	ROUGHNESS = 1.0;
}
"""
	var material := ShaderMaterial.new()
	material.shader = shader
	material.set_shader_parameter("pale", light)
	material.set_shader_parameter("deep", dark)
	material.set_shader_parameter("board_visible", 1.0 if board_grid_visible else 0.0)
	all_grid_materials.append(material)
	return material

func _create_flat_ground() -> void:
	# Its TOP FACE is exactly y=0, and extends x,z in [-50,+50].
	var ground_mesh := BoxMesh.new()
	ground_mesh.size = Vector3(WIDTH_M, 0.4, DEPTH_M)
	var ground := MeshInstance3D.new()
	ground.name = "100m_by_100m_OneFlatBase_25x25Tiles"
	ground.mesh = ground_mesh
	ground.position = Vector3(0, -0.2, 0)
	grid_material = _checker_material(Color("adbdaf"), Color("788e85"))
	ground.material_override = grid_material
	add_child(ground)
	var floor_shape := BoxShape3D.new()
	floor_shape.size = ground_mesh.size
	var floor_collision := CollisionShape3D.new()
	floor_collision.name = "BaseFloorCollision_100x100"
	floor_collision.position = ground.position
	floor_collision.shape = floor_shape
	add_child(floor_collision)

func _create_ramp(index: int) -> void:
	var angle: float = RAMP_ANGLES[index]
	var x: float = RAMP_X[index]
	var run_m: float = 7.0
	if angle >= 60.0:
		run_m = 3.0 if angle == 60.0 else 1.6
	var rise_m: float = run_m * tan(deg_to_rad(angle))
	if angle == 90.0:
		# A vertical face is NOT a walkable Godot floor. Climbing is handled
		# separately by pawn_controller's contact-climbing branch.
		rise_m = 3.0
		var wall_size := Vector3(6.0, rise_m, 0.55)
		var mesh := BoxMesh.new()
		mesh.size = wall_size
		var obj := MeshInstance3D.new()
		obj.name = "Ramp07_90degVerticalTestWall"
		obj.mesh = mesh
		obj.position = Vector3(x, rise_m * 0.5, RAMP_Z - 0.28)
		obj.material_override = _checker_material(Color("d9b5a5"),Color("ab776f"))
		add_child(obj)
		var collider := CollisionShape3D.new()
		collider.name = "VerticalWallCollision"
		var shape := BoxShape3D.new()
		shape.size = wall_size
		collider.shape = shape
		collider.position = obj.position
		var wall_body := StaticBody3D.new()
		wall_body.name = "Grabbable90degWall"
		wall_body.collision_layer = 1
		wall_body.collision_mask = 0
		wall_body.add_to_group("cherpg_grabbable")
		add_child(wall_body)
		wall_body.add_child(collider)
		# Small, safe landing deck behind the 90° vertical face.
		# Upper surface exactly y=3.0m, overlapping wall's back side.
		var deck_mesh := BoxMesh.new()
		deck_mesh.size = Vector3(6.0,0.30,4.0)
		var deck := MeshInstance3D.new()
		deck.name = "VerticalWall3mTopLandingPlatform"
		deck.mesh = deck_mesh
		deck.position = Vector3(x,rise_m-0.15,RAMP_Z-2.3)
		deck.material_override = _checker_material(Color("d8c9ae"),Color("aa967a"))
		add_child(deck)
		var deck_shape := BoxShape3D.new()
		deck_shape.size = deck_mesh.size
		var deck_collider := CollisionShape3D.new()
		deck_collider.name = "VerticalWallTopLandingCollision"
		deck_collider.position = deck.position
		deck_collider.shape = deck_shape
		add_child(deck_collider)
		return
	var half_w := 3.0
	var z_front: float = RAMP_Z
	var z_back: float = RAMP_Z - run_m
	var a := Vector3(x-half_w,0,z_front)
	var b := Vector3(x+half_w,0,z_front)
	var c := Vector3(x-half_w,rise_m,z_back)
	var d := Vector3(x+half_w,rise_m,z_back)
	var e := Vector3(x-half_w,0,z_back)
	var f := Vector3(x+half_w,0,z_back)
	# Closed, static wedge mesh, collision generated from the same surface.
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	var tris := [a,b,c, b,d,c,
		a,b,e, b,f,e,
		e,f,c, f,d,c,
		a,e,c, b,d,f]
	for vertex in tris:
		st.add_vertex(vertex)
	st.generate_normals()
	var mesh2 := st.commit()
	var ramp := MeshInstance3D.new()
	ramp.name = "Slope_%02d_Deg" % int(angle)
	ramp.mesh = mesh2
	ramp.material_override = _checker_material(Color("b2bea1"),Color("728765"))
	add_child(ramp)
	var coll := CollisionShape3D.new()
	coll.name = "SlopeCollision_%02d" % int(angle)
	var trimesh: ConcavePolygonShape3D = mesh2.create_trimesh_shape()
	trimesh.backface_collision = true
	coll.shape = trimesh
	# Give each incline its own collider owner. The Pawn may climb ONLY
	# surfaces tagged grabbable and at least 30 degrees from horizontal.
	var slope_body := StaticBody3D.new()
	slope_body.name = "SlopeBody_%02d" % int(angle)
	slope_body.collision_layer = 1
	slope_body.collision_mask = 0
	if angle >= CLIMBABLE_FROM_DEG:
		slope_body.add_to_group("cherpg_grabbable")
	add_child(slope_body)
	slope_body.add_child(coll)

func _create_uneven_area() -> void:
	# A localized terrain specimen; the full surrounding field stays level.
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	var center := Vector2(-22.0,-18.0)
	var radius := 7.0
	var divisions := 40
	for ix in range(divisions):
		for iz in range(divisions):
			var x0: float = center.x-radius + float(ix) * 2.0 * radius / divisions
			var x1: float = center.x-radius + float(ix+1) * 2.0 * radius / divisions
			var z0: float = center.y-radius + float(iz) * 2.0 * radius / divisions
			var z1: float = center.y-radius + float(iz+1) * 2.0 * radius / divisions
			var a := Vector3(x0, height_at(x0,z0)+.008, z0)
			var b := Vector3(x0, height_at(x0,z1)+.008, z1)
			var c := Vector3(x1, height_at(x1,z0)+.008, z0)
			var d := Vector3(x1, height_at(x1,z1)+.008, z1)
			for vertex in [a,b,c,c,b,d]:
				st.add_vertex(vertex)
	st.generate_normals()
	var mesh := st.commit()
	var terrain := MeshInstance3D.new()
	terrain.name = "UnevenGroundPatch"
	terrain.mesh = mesh
	terrain.material_override = _checker_material(Color("c6baa2"),Color("927d66"))
	add_child(terrain)
	var coll := CollisionShape3D.new()
	coll.name = "UnevenPatchCollision"
	var shape: ConcavePolygonShape3D = mesh.create_trimesh_shape()
	shape.backface_collision = true
	coll.shape = shape
	add_child(coll)

func _create_stairs() -> void:
	for i in range(8):
		var obj := MeshInstance3D.new()
		var mesh := BoxMesh.new()
		var height := (float(i)+1.0)*0.16
		mesh.size = Vector3(4.4,height,0.8)
		obj.mesh = mesh
		obj.position = Vector3(20.0,height*0.5,-15.0-float(i)*0.8)
		obj.name = "Step_%02d" % i
		obj.material_override = _checker_material(Color("adb2ba"),Color("697887"))
		add_child(obj)
		var col := CollisionShape3D.new()
		var shape := BoxShape3D.new()
		shape.size = mesh.size
		col.name = "StepCollision_%02d" % i
		col.position = obj.position
		col.shape = shape
		add_child(col)

func height_at(x: float,z: float) -> float:
	# Exact height of the separate uneven patch. Base terrain otherwise y=0.
	var dx: float = absf(x+22.0)/7.0
	var dz: float = absf(z+18.0)/7.0
	if dx >= 1.0 or dz >= 1.0:
		return GROUND_TOP_Y
	var fade: float = pow(sin(PI * (1.0-dx) * 0.5), 2.0) * pow(sin(PI*(1.0-dz)*0.5),2.0)
	return maxf(0.0, fade * (0.24 + 0.21 * sin(x*1.3) * cos(z*1.8)))

func spawn_count() -> int:
	return SPAWN_X.size()

func spawn_position(index: int) -> Vector3:
	var i: int = clampi(index,0,SPAWN_X.size()-1)
	return Vector3(SPAWN_X[i],height_at(SPAWN_X[i],SPAWN_Z[i]),SPAWN_Z[i])

func station_name(index: int) -> String:
	var i: int = clampi(index,0,SPAWN_X.size()-1)
	var labels := ["FLAT","8 DEG","15 DEG","30 DEG","45 DEG","60 DEG","75 DEG",
		"90 DEG CLIMB WALL","UNEVEN PATCH","STAIRS"]
	return labels[i]

func set_board_debug_visible(enabled: bool) -> void:
	# I toggles all chess-cell boundaries and the checker contrast at once.
	board_grid_visible = enabled
	for mat in all_grid_materials:
		mat.set_shader_parameter("board_visible", 1.0 if enabled else 0.0)

func board_visible() -> bool:
	return board_grid_visible

func _create_labels() -> void:
	for i in range(SPAWN_X.size()):
		var loc := spawn_position(i)
		var label := Label3D.new()
		label.name = "StationLabel_%02d" % i
		label.text = "%02d | %s" % [i,station_name(i)]
		label.font_size = 35
		label.pixel_size = 0.008
		label.outline_size = 4
		label.billboard = BaseMaterial3D.BILLBOARD_ENABLED
		label.position = loc + Vector3(-1.6,2.1,-1.0)
		add_child(label)
