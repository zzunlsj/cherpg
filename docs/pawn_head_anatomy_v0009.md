# CheRPG Pawn head: anatomy research and v0.0.9 sculpt notes

## Evidence and references
- US NIH **Anatomy of the Ear**: https://elementsofmorphology.nih.gov/anatomy-ear.shtml
  - Outer helix is a partial curved rim, while antihelix branches into two crura; concha is recessed; tragus lies at its anterior margin; lobule is inferior.
- NCBI/StatPearls **External Ear Anatomy**: https://www.ncbi.nlm.nih.gov/books/NBK470359/
  - The auricle contains layered, unequal-depth folds rather than concentric circular grooves.
- Blender Studio **Stylized Character Workflow**: https://studio.blender.org/training/stylized-character-workflow/
  - Use deliberate edge flow and adequate sculpting resolution around articulating facial features.
- Blender Manual **Subdivision Surface**: https://docs.blender.org/manual/en/latest/modeling/geometry_nodes/mesh/operations/subdivision_surface.html
  - Subdivision increases geometry resolution; v0.0.9 uses SIMPLE applied subdivision as a sculpt checkpoint, not approved production retopology.

## Diagnosis of actual v0.0.7 and v0.0.8 renders
1. Ear: radial/elliptical closed groove rather than helix/antihelix/concha relationships.
2. Eye region: narrow hollow-like slit and eyelid shading discontinuity; user explicitly prohibits ocular spheres, irises and pupils.
3. Nose: somewhat pinched forward tip/flat alar plane; avoid detached nose primitives.
4. Full head concept match remains **unverified**; no reference-registration overlay has been completed. Old mouth remains from early retopo and is out of scope for the specific ear/nose/eye-only request.

## Modeling change in v0.0.9
- Start from genuine v0.0.8 Blender scene.
- Retrieve index-aligned v0.0.4 pre-ring ear baseline and blend original side-head vertices back locally.
- Integrate upper/lower eye-lid surface into the same stone material; no eye globe, pupil or iris object.
- Apply two SIMPLE subdivision levels, then displace actual dense head vertices using named **open** helix C-curve, **branched** antihelix Y-curve, conchal bowl, tragus and lobule in ear-local Y/Z coordinates.
- Minor nose alar/tip transition adjustment; leave mouth unchanged.
- Produce Blender source .blend and five actual render views. A successful automation run is a **technical checkpoint**, not visual acceptance or Godot-readiness.

## Must-pass review
- Zero ocular objects and no new detached face-feature primitives.
- Ears must have visibly distinct nonconcentric landmarks under side lighting and from profile/three-quarter views.
- Eye region should read as subtle relief, not an aperture, slit or painted eyeball.
- No non-finite coordinates or visible tears; compare real renders side-by-side with original illustration before approval.
- High-poly sculpt requires final manual retopology, UV, normal and rig compatibility review before production export.
