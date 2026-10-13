# CheRPG 0.0.10v — 위쪽 시점 지면 표시 + 제작자 메타데이터

모든 테스트 지형에 `BaseMaterial3D.CULL_DISABLED`를 적용해 위에서 내려다보는 시점에서도 바닥이 렌더링되도록 수정했습니다. Windows 내보내기의 리소스 메타데이터도 활성화해 **제작자/회사: CheRPG**를 지정했습니다. 이는 디지털 코드 서명이 아니며, Windows 보안창의 검증된 게시자 이름을 대신하지 못합니다. [Windows 실행 안내](docs/WINDOWS_EXE_0.0.10v.md).

1분 이상 소요되는 주요 플레이 검증은 사용자 담당입니다. Godot 4.7.2, 기존 카메라 기준 WASD와 기본도형 유지.

---

# CheRPG 0.0.9v — 카메라 WASD와 시작 위치 수정

**Godot 4.7.2 / 독립 테스트 맵.** W/A/S/D가 카메라의 수평 전방·우측 방향을 기준으로 움직입니다. 발 도형과 충돌 캡슐 기준을 맞췄고 최초 시작도 해당 지형 높이를 사용합니다. **세계 행마 기준 방향은 카메라와 별개**이며, 칸을 넘는 자발적 이동에만 적용됩니다. [수정 내용과 사용자 검수 항목](docs/CAMERA_SPAWN_FIX_0.0.9v.md) · [Windows 실행 안내](docs/WINDOWS_EXE_0.0.9v.md).

1분 이상 걸리는 주요 플레이 테스트는 사용자가 수행합니다.

---

# CheRPG 0.0.8v — Godot 4.7.2 업데이트

독립 테스트 맵의 엔진과 Windows 빌드를 **Godot 4.7.2 stable**로 마이그레이션했습니다. 기존 0.0.7v의 판면/행마/점프/기본도형/회전장치 구현은 유지합니다. 1분 이상 주요 플레이 테스트는 사용자가 수행하며, GitHub 테스트 워크플로는 **수동 실행 전용**입니다. Windows EXE 안내는 [docs/WINDOWS_EXE_0.0.8v.md](docs/WINDOWS_EXE_0.0.8v.md)를 참조하세요.

---

# ⚠ CheRPG Godot 설정집 반영: 0.0.7v

이번 버전은 [세계관 정사 적용 사항](docs/CANON_ALIGNMENT_0.0.7v.md)과 함께 확인하세요. 한 칸 안에서는 `W/A/S/D` 자유 이동, 다른 칸으로 넘어갈 때에만 폰의 전진 행마 제한을 적용합니다. `Z/C`는 **몸만 돌리는** 키이고, `F1`은 평소 보이지 않는 판면 좌표의 디버그 표식을 켭니다. 0.0.6v 때 적힌 'W/S만 이동'은 예전 버전 설명입니다.

**Godot 플레이·장시간 테스트는 사용자 진행입니다.** 이 변경에 대한 Godot 런타임 검증은 실행하지 않았습니다.

---

# CheRPG — Terrain Motion + Direction Device Test Map (0.0.6v)

**Standalone Godot 4.5.2 project** — independent from the main game map, village and checkpoint. This branch changes no production scenes.

Open `godot/tests/motion_rotation_lab/project.godot` in Godot 4.5.2 and run the project (F5).

## Keyboard
- W/S or Up/Down: move forward/back along the Pawn's current chess-rule heading. No A/D strafing.
- Left Shift: sprint.
- Space: jump; release early for a shorter jump.
- 1–5: flat, 8° incline, 15° incline, uneven, 30° incline test lanes.
- R: expand waist ring and drop four terrain-contact anchors, **only when standing and stopped**.
- E: while grounded device is deployed, rotate only the logical heading 90°, never the body.
- Q: retract anchors and ring. T: reset position. Mouse: orbit camera. Esc: mouse capture toggle.

## Based on uploaded Unity pawn_player.cs
The user-provided 2D source uses input easing at 10/sec, 4.0 max walk speed, 1.5× sprint speed cap (6.0), sprint force multiplier 2, speed/force thresholds 0.1, friction and powerful release braking. This prototype preserves those movement **characteristics**, but recalibrates horizontal force into Godot CharacterBody3D acceleration rather than assuming Rigidbody2D mass and ForceMode units match. `SOURCE_*` constants document the original parameters.

The source has no jump. Godot's jump is separate: takeoff, in-air movement control, early-release lower jump, coyote time, input buffer, landing recovery and visual poses.

## Terrain and device
All parts are simple boxes, spheres, cylinders or torus meshes. Height and grid: Pawn 1.55m; one tile 2m × 2m. Dynamic walk/run joint swing, upper-body pitch and knee lift vary with slope. The four anchor shoes raycast the actual scene collision terrain (plus edge samples) and reject unsupported contacts or telescopic strokes outside 0.18–0.54m. Test lane colliders are two-sided after actual Godot validation.

## Test and limitations
`Godot --headless --path godot/tests/motion_rotation_lab -- --smoke-test` creates and checks five lanes, two leg pivots, four anchors, a grounded deployment, then jump and landing. GitHub Actions additionally checks the parser. CI validates code and geometrical contacts, **not subjective control feel**, original Unity physics equivalence, production map integration, or final sculpted/rigged art. The PR is intentionally a draft.
