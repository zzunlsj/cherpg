# CheRPG

CheRPG의 3D 캐릭터/Blender 파이프라인 저장소입니다.

현재 기준 주인공 Pawn 모델의 소스, 정리/리깅/렌더 자동화 스크립트, GitHub Actions, 검증용 렌더와 버전별 Blender/GLB 산출물을 보관합니다.

## Current state

- Current modeling stage: **v0.5.5 silhouette correction**
- Source sculpt GLB: `cherpg_pipeline/cherpg-pawn-protagonist-sculpt-refined-v0.5.2.glb`
- Blender version used by CI: **5.2.2**
- Current direction-device rule: changing `movement_heading` does **not** rotate the character's physical body orientation.
- The waist device remains independent from `visual_facing`.

## Repository layout

```
.github/workflows/
  cherpg-*.yml
cherpg_pipeline/
  cleanup_v053.py
  rig_v054.py
  rig_v0541.py
  rig_v055.py
  silhouette_v055.py
  render_*.py
  diagnose_*.py
  renders_v054/
  renders_v0541/
  renders_actual_v0541/
  renders_actual_v055/
artifacts/
  v0.5.3/
  v0.5.4/
  v0.5.4.1/
  v0.5.5/
```

## Version artifacts

### v0.5.3
Blender-ready cleanup pass. Includes cleaned GLB, BLEND, and validation report.

### v0.5.4
First actual Armature/rig pass. Includes rigged GLB, BLEND, and rig report.

### v0.5.4.1
Direction-device hierarchy and elbow-ring classification correction. Device rest-pose drift was validated against the source.

### v0.5.5
Silhouette correction pass. Reduces excessive helmet brim, scarf/ankle ring stacking, backpack boxiness, and refines torso/face/device proportions.

## Render references

- `cherpg_pipeline/renders_v054/`: six-view v0.5.4 geometry previews
- `cherpg_pipeline/renders_v0541/`: corrected six-view v0.5.4.1 previews
- `cherpg_pipeline/renders_actual_v0541/`: actual Blender PBR render
- `cherpg_pipeline/renders_actual_v055/`: actual Blender PBR render after silhouette correction

## Development branch

The migrated pipeline also uses the branch:

`cherpg-blender-pipeline`

The existing workflows retain that branch name so the pipeline can continue without rewriting every historical workflow trigger.

## Migration

This repository was migrated from the temporary development workspace `zzunlsj/claude-config` / `cherpg-blender-pipeline`. CheRPG-specific source files, workflows, committed renders, the original v0.5.2 GLB, and versioned GitHub Actions artifacts through v0.5.5 were copied here.
