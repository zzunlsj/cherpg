# CheRPG 0.0.19v — 제공된 `pawn_player(2).cs` 이식 기록

**원본:** 사용자가 제공한 Unity C# `pawn_player(2).cs`. 비교·추적을 위해 [원본 내용을 수정하지 않은 TXT](unity_reference/pawn_player_2_original.cs.txt)를 저장했습니다. **대상:** Godot 4.7.2 GDScript `scripts/pawn_controller.gd` 및 `scripts/motion_lab.gd` (독립 모션 테스트장).

## 원본 분석 / 이식

| Unity 원본 | Godot 적용 |
|---|---|
| `Update()`: WASD/방향키 `inputVec.x/y`를 `MoveTowards(...,Time.deltaTime*10)` | `Pawn._process(delta)`에서 양 축 입력을 원본 속도 **10 단위/초**로 부드럽게 보간 |
| `FixedUpdate()`: `fixedInputVec=ClampMagnitude(inputVec,1)` | `_source_feel_horizontal()`에서 `Vector2.limit_length(1)` |
| 정지 속도 `<=minSpeed(0.1)` | 정지 마찰 **`max(inputMagnitude*maxForce - mass*gravityScale*0.5,0)`** |
| 그 외 이동 상황 | **`input*20000 - velocity.normalized*mass*gravityScale*0.3`** |
| 입력값 `<minForce(0.1)`이고 이동 중 | 기존 힘에서 **`velocity.normalized*maxForce`**를 추가 감산 |
| 계산된 힘 크기 `<0.1` | 힘과 수평 이동 속도를 **즉시 0**으로 |
| `isSprint`이면 `force*=2.0` | **Ctrl** 누르고 달릴 때 같은 힘 배율 적용 |
| `AddForce(force*Time.fixedDeltaTime)` (기본 `ForceMode2D.Force`) | 수평 속도 업데이트 `v+=force*delta*delta/mass`; 원본처럼 한 번 더 곱해진 시간값 유지 |
| `maxSpeed=4`, `sprintSpeedScaile=1.5` | 힘 적용 후 **걷기 4m/s / 달리기 6m/s** 속도 상한 |
| `LateUpdate()`: `ResetTrigger("attack"); SetTrigger("attack")` | 마우스 왼쪽 클릭마다 0.36초짜리 기본도형 팔 공격 동작을 **처음부터 다시 재생** (실제 공격 판정 없음) |
| `anim.SetFloat("speed",linearVelocity.magnitude)` | 현재 수평 실이동 속도를 `source_anim_speed`에 기록하고 절차적 관절 보행에 전달 |
| `Rigidbody2D` 평면 x/y | Godot `CharacterBody3D`의 **수평 XZ** 속도로 대응하며 점프/중력 Y 및 충돌은 기존 CheRPG 시스템 유지 |

## 사용자 지정 기존 키 배치 우선 (명시적 예외)

**원본 C#은 `LeftShift=달리기`**지만, 사용자의 최신 명시 요청을 우선하여 **`Shift=웅크리기, Ctrl=달리기·등반`을 그대로 유지**합니다. 원본의 달리기 힘 2배 및 6m/s 속도 상한은 **Ctrl 달리기**에 적용합니다. Shift 웅크리기 중에는 속도 상한 1.8m/s와 낮은 충돌 캡슐을 적용합니다.

기존 카메라 기준 WASD, F 앵커, I 판면 **이동 규칙만** 해제(4m 타일 표시 유지), 30° 이상 표면 등반, 벽 접선 좌표계 W/S/A/D, 벽 턱 넘기, 지형/파츠 충돌 및 카메라 벽 충돌 방지 기능은 바꾸지 않았습니다.

## 물리 엔진 차이와 정확성 한계

Unity `Rigidbody2D`에는 mass/gravityScale이 있지만 Godot `CharacterBody3D`에는 동등한 속성이 없습니다. C# 원본의 수치 계산을 보존하기 위해 `source_rigidbody_mass=1.0`, `source_rigidbody_gravity_scale=1.0`을 **조정 가능한 가상 입력값**으로 두었습니다. Godot에서는 물리 엔진이 자체적으로 `AddForce`를 적분하지 않으므로 `ForceMode2D.Force` 효과를 수평 속도에 직접 적용합니다.

**따라서 연산 분기·순서·수치를 가능한 한 그대로 옮겼지만, Unity 2D와 Godot 3D에서 프레임 스케줄·충돌 반응까지 픽셀/물리적으로 동일하다는 의미는 아닙니다.** 특히 C#의 `maxForce=20000`과 `delta²`는 즉각적인 가속/제동 느낌을 만들 수 있습니다. 이는 원본의 실제 설정이며 임의 완화하지 않았습니다.

`SpriteRenderer`, Unity `Animator`, `UnityEditor`, `Unity.VisualScripting` 의존성은 Godot에 존재하지 않습니다. 이들은 Godot 기본도형 리그의 애니메이션/입력 처리로 대응합니다. Godot 프로젝트는 비-C# 빌드이므로 Unity C# 원본은 `.cs.txt` 보존용 파일로 저장하여 오해로 직접 임포트되지 않도록 했습니다.

## 사용자 직접 테스트

1. W/A/S/D와 방향키로 카메라 기준 이동, 입력 시작과 놓았을 때 가속/급감속 비교.
2. Ctrl을 누르고 이동 시 최대 6m/s, Ctrl 미입력 시 최대 4m/s인지 확인.
3. Shift 누르는 동안 웅크리고, Ctrl과 Shift 동시일 때 **웅크리기 우선** 확인.
4. 대각선 이동이 `ClampMagnitude(...,1)`처럼 속도를 초과하지 않는지 확인.
5. 왼클릭을 연속으로 하면 공격 자세가 처음부터 다시 재생되는지 확인.
6. HUD의 `Unity C# input / force / anim speed` 값을 확인하고 30°/90° 벽, I 판면, F 앵커와 함께 사용할 때 문제가 없는지 기록.

자동 빌드는 **소스·짧은 엔진 시작·Windows EXE 생성**까지만 검사합니다. **1분 이상 걸리는 주요 플레이 테스트는 사용자 직접 수행**합니다. Windows 파일 회사 메타데이터는 `CheRPG`이고 디지털 코드 서명은 현재 미적용입니다.
