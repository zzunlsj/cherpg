"""Subsecond static/source-rule check; NOT a Godot engine test."""
from pathlib import Path
import math
root=Path(__file__).resolve().parents[1]
board=(root/'scripts/board_rules.gd').read_text()
pawn=(root/'scripts/pawn_controller.gd').read_text()
device=(root/'scripts/direction_device.gd').read_text()
lab=(root/'scripts/motion_lab.gd').read_text()
assert 'TILE_SIZE_M := 2.0' in board
assert 'cell_at(' in board and 'constrain_voluntary(' in board
assert 'permitted_step(' in board
assert 'KEY_A' in pawn and 'KEY_D' in pawn
assert 'smoothed_strafe' in pawn
assert pawn.count('constrain_voluntary(') == 2
assert 'func apply_forced_displacement' in pawn
assert 'func rotate_body_only' in pawn
assert 'func queue_jump()' in pawn
assert 'locked_cell' in device and 'ALIGN TO TILE CENTER' in device
assert 'BOARD_RULES.cell_center' in device
assert 'KEY_F1' in lab and 'KEY_Z' in lab and 'KEY_C' in lab
def cell_at(x,z):
    return (math.floor((x+1)/2),math.floor((z+1)/2))
assert cell_at(0,0)==(0,0)
assert cell_at(.7,-.7)==(0,0)
assert cell_at(0,-1.01)==(0,-1)
assert cell_at(1.01,0)==(1,0)
assert cell_at(0,1.01)==(0,1)
print('CHERPG_CANON_QUICK_SOURCE_CHECK_OK (NOT A GODOT RUNTIME TEST)')
