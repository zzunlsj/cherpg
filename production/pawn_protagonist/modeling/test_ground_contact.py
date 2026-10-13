"""Offline CheRPG 0.0.3v rule tests. No bpy required."""
import pathlib
import sys
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
from direction_contact_solver import PRESETS, solve

for case in ("flat","slope_10deg_x","slope_8deg_diagonal","micro_terrain"):
    report=solve(PRESETS[case])
    assert report["safe"], f"Expected supported terrain: {case}"
    assert len(report["feet"])==4
    assert all(f["safe"] and f["minimum_gap_m"] > -1e-7 for f in report["feet"])
    assert all(f["within_tile"] and f["within_stroke"] for f in report["feet"])
    assert report["ring_edge_tile_clearance_m"] > .2
    print("GROUND_CONTACT_OK",case,
          [(round(f["lower_length"],4),round(f["minimum_gap_m"],7))
           for f in report["feet"]])

steep=solve(PRESETS["too_steep_30deg"])
assert not steep["safe"]
assert any(not f["within_stroke"] for f in steep["feet"])
print("GROUND_CONTACT_REJECTED","too_steep_30deg")
