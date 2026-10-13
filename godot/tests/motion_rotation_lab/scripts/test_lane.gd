extends StaticBody3D
## One physically collidable lane. Does not modify any CheRPG production terrain.
const HALF_WIDTH := 3.15
const HALF_LENGTH := 14.0
const STEP := 0.35
const GRADES_DEG := [0.0, 8.0, 15.0, 0.0, 30.0]
const LABELS := ["01  FLAT", "02  UPHILL 8°", "03  UPHILL 15°", "04  UNEVEN", "05  STEEP 30° / LIMIT"]
const TINTS := [Color("82958a"), Color("8395a9"), Color("ae9b86"), Color("8fa18b"), Color("a88080")]
var lane_index := 0

func setup(index: int) -> void:
	lane_index = index
	name = "TerrainLane_%02d" % (index + 1)
	position.x = float(index - 2) * 8.5
	collision_layer = 1
	collision_mask = 0
	_build_terrain()
	_build_labels()

func height_at(local_x: float, local_z: float) -> float:
	var run_m := clampf(5.5 - local_z, 0.0, 17.0)
	if lane_index == 3:
		# Continuous, modest local relief on top of a subtle overall gradient.
		return 0.065 * run_m + 0.095 * sin(local_z * 1.8) * cos(local_x * 1.7) + 0.04 * sin(local_z * 3.7 + local_x)
	return tan(deg_to_rad(GRADES_DEG[lane_index])) * run_m

func _build_terrain() -> void:
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	var nx := int(round(2.0 * HALF_WIDTH / STEP))
	var nz := int(round(2.0 * HALF_LENGTH / STEP))
	for ix in range(nx):
		for iz in range(nz):
			var x0 := -HALF_WIDTH + float(ix) * 2.0 * HALF_WIDTH / float(nx)
			var x1 := -HALF_WIDTH + float(ix + 1) * 2.0 * HALF_WIDTH / float(nx)
			var z0 := -HALF_LENGTH + float(iz) * 2.0 * HALF_LENGTH / float(nz)
			var z1 := -HALF_LENGTH + float(iz + 1) * 2.0 * HALF_LENGTH / float(nz)
			var a := Vector3(x0, height_at(x0, z0), z0)
			var b := Vector3(x0, height_at(x0, z1), z1)
			var c := Vector3(x1, height_at(x1, z0), z0)
			var d := Vector3(x1, height_at(x1, z1), z1)
			# Correct winding: +Y normal for flat terrain.
			for v in [a, b, c, c, b, d]:
				st.add_vertex(v)
	st.generate_normals()
	var mesh := st.commit()
	var mi := MeshInstance3D.new()
	mi.name = "SculptedTestGround"
	mi.mesh = mesh
	var mat := StandardMaterial3D.new()
	mat.albedo_color = TINTS[lane_index]
	mat.roughness = 1.0
	mi.material_override = mat
	add_child(mi)
	var collision := CollisionShape3D.new()
	collision.name = "GroundCollision"
	var terrain_shape: ConcavePolygonShape3D = mesh.create_trimesh_shape()
	terrain_shape.backface_collision = true
	collision.shape = terrain_shape
	add_child(collision)
	# 2-metre reference tiles, visualization only (no extra collision).
	for x_value in [-2.0, 0.0, 2.0]:
		for z_value in range(-12, 13, 2):
			var marker := MeshInstance3D.new()
			marker.name = "TileMark"
			var box := BoxMesh.new()
			box.size = Vector3(0.055, 0.01, 0.26)
			marker.mesh = box
			marker.position = Vector3(x_value, height_at(x_value, float(z_value)) + 0.016, float(z_value))
			var mm := StandardMaterial3D.new()
			mm.albedo_color = Color(0.88, 0.9, 0.83, 0.8)
			marker.material_override = mm
			add_child(marker)

func _build_labels() -> void:
	var label := Label3D.new()
	label.name = "LaneDescription"
	label.text = LABELS[lane_index]
	label.font_size = 44
	label.pixel_size = 0.008
	label.outline_size = 6
	label.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	label.position = Vector3(0, height_at(0.0, 11.8) + 2.3, 11.8)
	add_child(label)
