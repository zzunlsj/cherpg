extends RefCounted
## CheRPG: invisible 2 m board overlain by ordinary physical terrain.
## Within one tile, movement is unrestricted. Crossing into another tile
## voluntarily uses the Pawn's active heading (-Z, +X, +Z, -X).
## Forced movement is processed separately by pawn_controller.gd.
const TILE_SIZE_M := 2.0
const HALF_TILE_M := 1.0
const EDGE_EPSILON := 0.002
const CARDINAL_OFFSETS := [Vector2i(0, -1), Vector2i(1, 0), Vector2i(0, 1), Vector2i(-1, 0)]

static func cell_at(world_pos: Vector3, origin: Vector3) -> Vector2i:
	return Vector2i(
		floori((world_pos.x - origin.x + HALF_TILE_M) / TILE_SIZE_M),
		floori((world_pos.z - origin.z + HALF_TILE_M) / TILE_SIZE_M)
	)

static func cell_center(cell: Vector2i, origin: Vector3) -> Vector3:
	return origin + Vector3(float(cell.x) * TILE_SIZE_M, 0.0, float(cell.y) * TILE_SIZE_M)

static func permitted_step(from_cell: Vector2i, to_cell: Vector2i, heading_index: int) -> bool:
	if from_cell == to_cell:
		return true
	return to_cell - from_cell == CARDINAL_OFFSETS[posmod(heading_index, 4)]

static func constrain_voluntary(start: Vector3, desired: Vector3, origin: Vector3, heading_index: int) -> Dictionary:
	var before: Vector2i = cell_at(start, origin)
	var after: Vector2i = cell_at(desired, origin)
	var legal: Vector2i = CARDINAL_OFFSETS[posmod(heading_index, 4)]
	var center: Vector3 = cell_center(before, origin)
	var limited: Vector3 = desired
	var blocked_x := false
	var blocked_z := false
	if after.x != before.x and after.x != before.x + legal.x:
		limited.x = clampf(desired.x, center.x - HALF_TILE_M + EDGE_EPSILON, center.x + HALF_TILE_M - EDGE_EPSILON)
		blocked_x = true
	if after.y != before.y and after.y != before.y + legal.y:
		limited.z = clampf(desired.z, center.z - HALF_TILE_M + EDGE_EPSILON, center.z + HALF_TILE_M - EDGE_EPSILON)
		blocked_z = true
	return {
		"position": limited,
		"resisted": blocked_x or blocked_z,
		"blocked_x": blocked_x,
		"blocked_z": blocked_z,
		"from_cell": before,
		"to_cell": cell_at(limited, origin)
	}
