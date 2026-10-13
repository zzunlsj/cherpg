extends StaticBody3D
## ONE connected, collision-enabled terrain. Five zones transition continuously.
## This map is independent from CheRPG production geography.
## The always-visible checker shades/lines mark the invisible 2m board for TESTING.
const HALF_WIDTH := 5.0
const START_Z := 14.0
const END_Z := -56.0
const STEP := 0.35
const ZONE_LABELS := ["FLAT", "8 DEG UPHILL", "15 DEG UPHILL", "UNEVEN", "30 DEG / LIMIT"]
const ZONE_MARKS := [4.0, 18.0, 32.0, 46.0, 60.0]
const ZONE_CUTS := [12.0, 26.0, 40.0, 54.0]
const TILE_SIZE := 2.0
const BOARD_ORIGIN_Z := 10.0
var ground_material: ShaderMaterial

func setup() -> void:
	name = "ConnectedTerrain_FiveZones_OneCollision"
	collision_layer = 1
	collision_mask = 0
	_build_terrain()
	_build_labels()

func zone_index(world_z: float) -> int:
	var run_m: float = START_Z - world_z
	for i in ZONE_CUTS.size():
		if run_m < ZONE_CUTS[i]:
			return i
	return 4

func spawn_z(index: int) -> float:
	return START_Z - ZONE_MARKS[clampi(index, 0, 4)]

func _smooth_hinge(x: float, radius: float) -> float:
	# Integral of smoothstep across [-radius, +radius].
	# h(x)=0 below transition, h(x)=x above it, C1 at both ends.
	if x <= -radius:
		return 0.0
	if x >= radius:
		return x
	var u: float = (x + radius) / (2.0 * radius)
	return 2.0 * radius * (u * u * u - 0.5 * u * u * u * u)

func height_at(local_x: float, local_z: float) -> float:
	var travel: float = clampf(START_Z - local_z, 0.0, START_Z - END_Z)
	# Integrate slope along the single connected route: heights are continuous
	# through zone boundaries, with 1.2m gradual grade transitions.
	var m8: float = tan(deg_to_rad(8.0))
	var m15: float = tan(deg_to_rad(15.0))
	var m_uneven: float = 0.065
	var m30: float = tan(deg_to_rad(30.0))
	var height: float = m8 * _smooth_hinge(travel - 12.0, 1.2)
	height += (m15 - m8) * _smooth_hinge(travel - 26.0, 1.2)
	height += (m_uneven - m15) * _smooth_hinge(travel - 40.0, 1.2)
	height += (m30 - m_uneven) * _smooth_hinge(travel - 54.0, 1.2)
	# Fade microterrain in and out without a cliff at the boundary.
	var micro_t: float = clampf((travel - 40.0) / 14.0, 0.0, 1.0)
	var fade: float = pow(sin(PI * micro_t), 2.0)
	height += fade * (0.12 * sin(local_z * 1.8) * cos(local_x * 1.2) + 0.046 * sin(local_z * 3.1 + local_x))
	return height

func _board_material() -> ShaderMaterial:
	var shader := Shader.new()
	shader.code = """
shader_type spatial;
render_mode cull_disabled, diffuse_burley;
uniform float line_opacity : hint_range(0.0, 1.0) = 0.87;
uniform float checker_strength : hint_range(0.0, 1.0) = 1.0;
varying vec3 world_pos;
void vertex() {
	world_pos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
}
void fragment() {
	// Grid lines are tied to the world, not the terrain triangles.
	// The Pawn board origin is (0, y, 10m); 1 invisible cell = 2m.
	vec2 board = (world_pos.xz - vec2(0.0, 10.0) + vec2(1.0)) / 2.0;
	float alternate = mod(floor(board.x) + floor(board.y), 2.0);
	vec3 pale = vec3(0.51, 0.63, 0.56);
	vec3 deep = vec3(0.32, 0.46, 0.42);
	vec3 tile_color = mix(pale, deep, alternate * checker_strength);
	vec2 edge = min(fract(board), vec2(1.0) - fract(board));
	float meters_to_edge = min(edge.x, edge.y) * 2.0;
	float dark_line = 1.0 - smoothstep(0.024, 0.061, meters_to_edge);
	ALBEDO = mix(tile_color, vec3(0.10, 0.13, 0.15), dark_line * line_opacity);
	ROUGHNESS = 1.0;
}
"""
	var material := ShaderMaterial.new()
	material.shader = shader
	return material

func _build_terrain() -> void:
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	var nx: int = int(ceil(2.0 * HALF_WIDTH / STEP))
	var nz: int = int(ceil((START_Z - END_Z) / STEP))
	for ix in range(nx):
		for iz in range(nz):
			var x0: float = -HALF_WIDTH + float(ix) * (2.0 * HALF_WIDTH) / float(nx)
			var x1: float = -HALF_WIDTH + float(ix + 1) * (2.0 * HALF_WIDTH) / float(nx)
			var z0: float = END_Z + float(iz) * (START_Z - END_Z) / float(nz)
			var z1: float = END_Z + float(iz + 1) * (START_Z - END_Z) / float(nz)
			var a := Vector3(x0, height_at(x0, z0), z0)
			var b := Vector3(x0, height_at(x0, z1), z1)
			var c := Vector3(x1, height_at(x1, z0), z0)
			var d := Vector3(x1, height_at(x1, z1), z1)
			for v in [a, b, c, c, b, d]:
				st.add_vertex(v)
	st.generate_normals()
	var mesh := st.commit()
	var ground := MeshInstance3D.new()
	ground.name = "OneContinuousTestGround_WithBoardContrast"
	ground.mesh = mesh
	ground_material = _board_material()
	ground.material_override = ground_material
	add_child(ground)
	var collision := CollisionShape3D.new()
	collision.name = "ContinuousGroundCollision"
	var terrain_shape: ConcavePolygonShape3D = mesh.create_trimesh_shape()
	terrain_shape.backface_collision = true
	collision.shape = terrain_shape
	add_child(collision)

func set_board_debug_visible(enabled: bool) -> void:
	if ground_material != null:
		ground_material.set_shader_parameter("line_opacity", 1.0 if enabled else 0.87)
		ground_material.set_shader_parameter("checker_strength", 1.0 if enabled else 1.0)

func _build_labels() -> void:
	for i in ZONE_LABELS.size():
		var z: float = spawn_z(i)
		var label := Label3D.new()
		label.name = "ZoneLabel_%02d" % (i + 1)
		label.text = "%02d  %s" % [i + 1, ZONE_LABELS[i]]
		label.font_size = 38
		label.pixel_size = 0.007
		label.outline_size = 6
		label.billboard = BaseMaterial3D.BILLBOARD_ENABLED
		label.position = Vector3(-3.7, height_at(-3.7, z) + 1.8, z)
		add_child(label)
