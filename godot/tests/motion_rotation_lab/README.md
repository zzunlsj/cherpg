# CheRPG 0.0.22v — 계단 오르기 / 발바닥·손의 지형 접촉 보정

**Godot 4.7.2 독립 테스트장.** 계단 시험 지점(키 **0**)이 계단 충돌체 안에서 시작하던 문제를 수정했습니다. 기존 Godot 경사 처리에 없던 **0.225m 이하 턱 올라가기 판정**을 추가해 0.16m 높이 계단을 실제 충돌 검사 후 올라갑니다. 충돌 장애물/천장/4m 판면 규칙은 유지합니다.

**지지 발 IK:** 지면의 실제 높이와 법선을 양발 레이로 검사해 2관절 고관절·무릎으로 발을 디딜 수 있는 위치에 맞추고, 스윙 발이 지면에 들어가려 할 때만 보정합니다. **벽 손 IK:** 실제 벽·턱의 손잡이 위치에 어깨·팔꿈치를 맞춥니다. 지형과 파츠 충돌에서는 정상적인 발 접촉과 깊은 관통을 별도로 분류합니다. **모든 메시 원래 크기는 유지**합니다.

[0.0.22v Windows 실행/IK/계단 검사 안내](docs/WINDOWS_EXE_0.0.22v.md). 캐릭터 물리 충돌을 넘어서는 완벽한 지형/자체 무관통이 보장된 것은 아닙니다. 1분 이상 플레이 테스트는 사용자 담당입니다.

---

# CheRPG 0.0.21v — 걷기·점프·웅크리기·등반·앵커 모션의 크기 변형 제거

Godot 4.7.2 독립 테스트장. **캐릭터 모델과 장치 파츠가 애니메이션 중 길어지거나 납작해지던 런타임 스케일 조작을 제거했습니다.** 전신 높이를 67%로 압축하던 기존 웅크리기는 새 `RIG_UpperBodyWaistHinge_NoScaling` 상체 관절 굽힘, 무릎/고관절, 골반 하강을 조합합니다. 무릎 역방향 굽힘 제한과 지형 적응 동작은 계속 유지합니다.

휴대용 회전장치는 **고정 지름 수납/전개 링의 교차 페이드, 이동식 레일, 일정 길이의 중첩 슬라이딩 앵커 튜브**를 사용합니다. 링·막대·발판 자체의 크기는 애니메이션 도중 변하지 않습니다.

[0.0.21v Windows 실행 및 테스트 범위 안내](docs/WINDOWS_EXE_0.0.21v.md). Godot에서 실제 **70개 기본도형 메시와 80회 동작 샘플의 크기 변화가 0건**임을 확인하는 짧은 회귀 검사를 추가했습니다. 기존 카메라 기준 이동·Ctrl 달리기/등반·Shift 웅크리기·I 판면 제약·F 앵커·90° 탑뷰는 유지합니다.

1분 이상 주요 플레이 테스트는 사용자 담당입니다.

---

# CheRPG 0.0.20v — 카메라 이동 방향 복원 · 떨림 제동 수정 · 실제 물리 플레이 검증

WASD 입력의 힘 계산을 **기존 카메라 수평 회전각**에 맞춰 변환하여, W가 90° 탑뷰에서도 카메라 정면 방향으로 진행하도록 복원했습니다. **저속 임계 속도를 0.1→0.6m/s**로 높였고, 강한 `maxForce=20000` 제동이 속도를 반전시켜 반복되는 떨림을 막도록 **키 해제 시 역방향 속도 오버슈트를 0으로 제한**했습니다.

이번 요청에 한해 **실제 Godot 4.7.2 물리 엔진 입력 시뮬레이션 플레이 테스트**를 진행했습니다. 첫 테스트에서 손을 놓고도 속도가 4m/s로 반복되는 문제를 재현했고, 제동 보정 후 카메라 0°·90°·탑뷰 90° 방향 이동, Ctrl 달리기 6m/s, 키 해제 후 0m/s, Shift 웅크리기 검사가 **전부 통과**했습니다.

[전체 테스트 로그·검사 값](docs/PLAYTEST_RESULT_0.0.20v.md) · [Windows 0.0.20v 실행 안내](docs/WINDOWS_EXE_0.0.20v.md)

**이후 CI에서는 물리 플레이 테스트를 자동 실행하지 않습니다.** 다음 장시간 검수는 사용자 담당이며 한 번 수행한 테스트 스크립트만 수동 재현용으로 남깁니다. 본편 main과 독립된 모션 테스트 프로젝트입니다.

---

# CheRPG 0.0.19v — `pawn_player(2).cs` 이동·힘 계산 이식

**Godot 4.7.2 / 독립 테스트장.** 사용자가 제공한 Unity `pawn_player(2).cs`를 분석하여 W/A/S/D·방향키 입력 보간(10/s), Unity 2D 수평 힘/마찰 분기(`maxForce=20000`, 정지/이동 마찰 0.5/0.3, 입력 중단 제동), 기본 ForceMode2D의 `fixedDeltaTime` 추가 적용 및 **4m/s·6m/s 속도 제한**을 Godot 3D XZ 운동에 대응시켰습니다. 왼쪽 클릭 공격 동작 재시작, 이동 속도 애니메이션 매개변수도 대응시켰습니다.

**사용자 최신 조작법은 우선 보존:** 원본 Unity 스크립트가 `Shift=달리기`지만 이 프로젝트는 요청대로 **Shift=웅크리기 / Ctrl=달리기·등반**을 유지합니다. 카메라 기준 조작, 벽 등반 접선 좌표계, 4m 판면 행마 규칙, F 앵커, I 행마 제약만 전환, 충돌 카메라 및 맨틀 기능은 그대로입니다. 기본도형 모델도 유지합니다.

[원본 C#과 Godot 코드 줄별 대응/물리 한계](docs/UNITY_PAWN_PLAYER2_PORT_0.0.19v.md) · [Windows 실행/검수 안내](docs/WINDOWS_EXE_0.0.19v.md)

자동 검증은 정적 계산·Godot 짧은 임포트/시작·Windows EXE 생성이며, **1분 이상 실제 플레이 테스트는 사용자 담당**입니다.

---

# CheRPG 0.0.18v — 벽을 뚫지 않는 추적 카메라

**Godot 4.7.2 / 독립 테스트장.** 카메라의 기본 추적 거리 **6.8m**를 유지하면서 지형·벽·바닥·천장과의 충돌을 카메라 반지름 0.23m 구체 스윕으로 확인합니다. 벽으로 가려질 때 카메라를 벽 바로 앞쪽(추가 여유 0.08m)으로 당기고, 장애물이 없어지면 6.8m로 복구합니다. 보간된 최종 카메라 위치도 재검사해 마우스 회전 도중 벽을 통과하는 문제를 방지합니다.

벽 등반 중에는 벽 법선 바깥으로 카메라 충돌 시작점을 보정해 캐릭터의 시야를 확보하고, 근거리에서는 카메라 시야각을 확대합니다. HUD에서 추적 카메라의 실제 거리와 벽 차단 여부를 확인할 수 있습니다. **90° 탑뷰·Ctrl 등반 W/S/A/D 벽 접선 방향·Shift 웅크리기·F 앵커·I 4m 판면 제약 토글**은 유지합니다.

[0.0.18v Windows EXE 및 사용자 검수 안내](docs/WINDOWS_EXE_0.0.18v.md). 실제 1분 이상 플레이 검수는 사용자 담당입니다.

---

# CheRPG 0.0.17v — 카메라 독립 벽 등반 조작

Godot 4.7.2 독립 테스트장. 벽을 Ctrl+W로 잡은 뒤에는 **벽의 접선 좌표계**를 사용합니다. **Ctrl만 유지하면 그 자리에서 매달리며**, **Ctrl+W/S**는 벽 위·아래, **Ctrl+A/D**는 벽 왼쪽·오른쪽 이동입니다. 카메라를 회전해도 벽 접선/몸 방향이 바뀌지 않습니다. 고정된 4m 판면 이동 제약과 90° 벽 상단 턱 넘기는 유지하며, 턱 넘기는 위쪽으로 계속 이동할 때만 발동합니다.

[Windows 실행 안내·등반 조작 및 사용자 검수](docs/WINDOWS_EXE_0.0.17v.md). 기존 Ctrl 달리기·Shift 웅크리기·I 이동 제약 토글·F 앵커, 100×100m 4m 판면 테스트장을 유지합니다. **1분 이상 걸리는 주요 플레이 테스트는 사용자만 수행합니다.**

---

# CheRPG 0.0.16v — 턱 넘기·파츠 충돌·지형 연동 모션

Godot 4.7.2 독립 테스트장. **Ctrl+W로 잡을 수 있는 벽을 오르고 상단에 도착하면, 손 뻗기→몸 들어올리기→다리 넘기기→착지의 4단계 맨틀 애니메이션과 물리 루트 이동**을 수행합니다. 각 단계는 실제 충돌과 4m 판면 행마를 확인하고 위험한 경로를 중단합니다.

**전신 기본도형 메시 파츠별 충돌 검사 영역**을 생성해 지형/다른 파츠와 겹치는 애니메이션은 마지막 안전 관절 자세로 보정합니다. 양팔 팔꿈치를 실제 힌지로 분리하고, 발별 레이캐스트/경사 법선을 이용해 걷기·달리기·웅크리기·착지 자세를 적응시킵니다.

기존 **100×100m 평지, 4m×4m 타일, I 행마 제약만 OFF(타일 무늬 유지), F 앵커, Ctrl 달리기·등반, Shift 웅크리기, 90° 카메라**는 유지합니다. 정밀한 변형 메시·래그돌·완전 IK 충돌 보증이 아닌 **기본도형 단계의 검사 및 보정 구현**입니다.

[Windows 실행 파일·기능·검수 안내](docs/WINDOWS_EXE_0.0.16v.md). 실제 1분 이상 플레이 테스트는 사용자 담당입니다.

---

# CheRPG 0.0.15v — I=행마 제약만 해제, Ctrl=달리기·등반, Shift=웅크리기

Godot 4.7.2 Windows 독립 테스트 맵. 100m×100m 테스트장, **4m×4m 판면(25×25칸)**, 경사/요철/계단, 90° 탑뷰와 F 앵커 시스템을 유지합니다.

이번 업데이트:
- **I**: 실제 4m 판면의 자발 이동 방향 제약만 해제/재적용. **바닥의 타일 패턴·경계선은 항상 표시**되며 일반 물리 충돌도 계속 적용됩니다.
- **Ctrl 누르고 있기**: 4m/s 걷기에서 최대 6m/s 달리기. **Ctrl+W**, 근처에 잡을 수 있는 30° 이상 표면이 있을 때 등반 시도.
- **Shift 누르고 있기**: 웅크리기, 느린 이동, 낮아진 충돌 캡슐. 머리 위 장애물이 있으면 일어나지 않습니다. Shift 우선.
- **무릎 방향 수정**: 본 기본도형 다리의 무릎이 앞쪽으로 꺾이던 양수 X 대신 뒤쪽 음수 X로 굽혀지도록 교체하고, 전 애니메이션 관절각 범위를 제한했습니다. 걷기·점프·등반·웅크리기에 적용.
- 기존 Shift 대시 삭제. **F 누르면 설치 범위 미리보기 / 떼면 앵커 설치·회수**, 설치 중 A/D 방향 전환 유지.

[Windows 0.0.15v 실행 안내와 검수 항목](docs/WINDOWS_EXE_0.0.15v.md). **1분 이상 소요되는 주요 실플레이 검수는 사용자 담당**입니다.

---

# CheRPG 0.0.14v — 4m 판면 / 30° 잡기 등반 / 실제 보행 주기

**Godot 4.7.2 독립 테스트장**에서 기존 2m×2m 판면을 **4m×4m**로 확대했습니다. 100m×100m 바닥은 **25×25=625칸**이고 논리 행마 판정·체커 색·홀로그램 칸 테두리가 같은 좌표를 사용합니다. **I 키로 바닥의 판면 경계와 명암을 함께 끄거나 켤 수 있습니다.**

**F를 누르고 있으면 설치 범위/네 받침/현재 4m칸 홀로그램, 떼면 설치·회수**하도록 기존 R 홀로그램 기능을 통합했습니다. R은 별도 기능이 없습니다. 설치 완료 시 A/D로 행마 방향만 변경합니다. W를 누르며 **명시적으로 잡을 수 있는 표면(cherpg_grabbable)**에 가까이 접촉한 경우에만 **경사 30° 이상 90° 이하**에서 표면 방향 등반을 시도합니다.

걷기는 60% 지지기/40% 유각기, 착지 충격 흡수·발끝 밀기·무릎 전진·반대쪽 팔 교차를 적용한 절차적 기본도형 애니메이션입니다. 실제 발 IK/품질 검수는 별도입니다.

[Windows 실행 안내와 사용자 검수 항목](docs/WINDOWS_EXE_0.0.14v.md). 주요 1분 이상 테스트는 사용자 담당이며 자동 CI는 짧은 로드·빌드만 검사합니다.

---

# CheRPG 0.0.13v — 90° 카메라 탑뷰 지원

Godot 4.7.2 독립 테스트장 카메라를 **수평 기준 90° 위, 완전한 탑뷰**까지 올릴 수 있습니다. 마우스를 위로 움직여 시점을 올립니다. Godot `Camera3D.look_at()`의 수직 방향 특이점을 처리하고, WASD는 카메라 orbit의 수평 회전각을 따르므로 90°에서도 화면 기준 전진이 유지됩니다. HUD에서 현재 카메라 각도를 확인할 수 있습니다.

그 외 **100×100m 평지/2×2m 타일, 시험 경사, F 앵커, A/D 방향 전환, R 홀로그램, O 리셋, Shift 대시와 기존 모션**은 유지했습니다.

[Windows 0.0.13v 실행 안내](docs/WINDOWS_EXE_0.0.13v.md). 1분 이상 주요 플레이 테스트는 사용자 담당입니다.

---

# CheRPG 0.0.12v — 100×100m 평지 / 2×2m 판면 / 90° 경사 시험

**Godot 4.7.2, 독립 테스트 맵.** 면적 100m×100m의 완전 평지 위에 8°·15°·30°·45°·60°·75° 경사대, 90° 수직벽, 요철, 계단을 별도로 배치했습니다. 평지는 2×2m 격자 50×50(2,500칸)로 시각화합니다. 90° 벽은 일반 바닥 경사가 아니므로 별도 W 접촉 등반 동작을 시험합니다.

**키 배치:** WASD 카메라 기준 이동 · Shift 짧은 대시 · Space 점프 · F 앵커 설치/회수 · **앵커 설치 중 A/D ±90° 회전** · **R 누르고 있는 동안 설치 범위 홀로그램** · O 시험 지점 리셋 · 1~9,0 시험 시설 선택 · F1 판면 경계 강조. 기존 기본도형 캐릭터는 유지합니다.

[설계 및 동작 변경](docs/FLAT_FIELD_AND_INPUT_0.0.12v.md) · [Windows 실행 안내](docs/WINDOWS_EXE_0.0.12v.md)

1분 이상 소요되는 **실제 플레이/품질 테스트는 사용자만** 수행하며, 자동 빌드는 소스 검사·짧은 시작 확인·EXE 생성까지만 진행합니다. 설치 정보의 회사 이름은 CheRPG, 코드 서명은 별도입니다.

---

# CheRPG 0.0.11v — 5개 지역이 연결된 판면 모션 테스트장

**Godot 4.7.2 / PC 독립 테스트장 / 기본도형 유지.** 5개 구역(평지→8°→15°→요철→30°)을 **하나의 연속 지형**으로 합쳤습니다. 바닥의 2m 판면은 어둡고 밝은 타일 명암과 경계선으로 항상 보이며(F1은 강조), 이는 **개발용 표시**로 세계관 정사에서 실제 판면이 보인다는 뜻은 아닙니다.

WASD·방향키로 카메라 기준 수평 이동, 왼쪽 클릭으로 기본 공격 관절 포즈, Shift 달리기, Space 별도 점프. 달리기와 점프 모션은 기본도형 리그 관절에서 개선했습니다. **1~5**는 같은 맵의 다른 구역으로 순간이동하며 실제로 걸어서도 전 구역을 연결할 수 있습니다. 신체 방향과 폰 행마 기준 방향 분리, 2m 칸 경계 전진 제한은 유지합니다.

[설계/검수 사항](docs/CONNECTED_MAP_MOTION_0.0.11v.md) · [Windows 실행 안내](docs/WINDOWS_EXE_0.0.11v.md)

장시간 주요 플레이 테스트는 사용자 담당입니다.

---

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
