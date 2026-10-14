# CheRPG Motion Lab 0.0.19v — 사용자 Unity C# 조작 코드 이식

**Godot 4.7.2 / Windows x64 / 제작자 파일 속성: CheRPG**

사용자가 제공한 `pawn_player(2).cs`를 분석하여 2D `Rigidbody2D`의 수평 제어 수식을 Godot 3D 수평 XZ 이동에 이식했습니다. [원본·변경 비교 기록](UNITY_PAWN_PLAYER2_PORT_0.0.19v.md)과 [원본 C# 백업](unity_reference/pawn_player_2_original.cs.txt)을 참조하세요.

## 정확히 유지하는 조작 예외
- **Shift: 웅크리기** (누르는 동안); 기존 웅크림 충돌 캡슐과 이동 제한 유지.
- **Ctrl: 달리기 / 벽 등반** (누르는 동안). **왼쪽 Shift로 달리는 원본 C# 부분만 사용자 지시에 따라 Ctrl로 대응**했습니다.
- **WASD / 방향키:** 카메라 기준 지상 이동, 10/초 입력 보간.
- **Ctrl+W로 grabbable 30° 이상 벽 붙잡기 → Ctrl 단독 정지 → Ctrl+W/S 상하, Ctrl+A/D 벽 접선 좌우 이동.**
- **F:** 누르는 동안 앵커 설치 공간 미리보기, 놓으면 설치/회수. 앵커 설치 중 A/D는 행마 기준 방향 전환.
- **I:** 논리 4m×4m 판면의 칸 넘기 제한만 ON/OFF. 바닥 체커 명암/경계선은 항상 표시.
- **Space:** 점프, **O:** 시험 위치 초기화, **1~9/0:** 100×100m 맵의 시험 구역, **마우스:** 회전/90° 탑뷰, **왼클릭:** 공격 팔 자세(피해 없음), **Esc:** 커서 잠금.

## Unity 코드와 동일하게 옮긴 수평 입력 계산
1. `Update`와 동등한 Godot `_process`에서 W/A/S/D·화살표로 각 축의 입력을 계산하고 `move_toward(...,delta*10)`으로 보간.
2. 물리 `_physics_process`에서 대각선을 최대 길이 1로 자른 입력 벡터 생성.
3. 현재 속도 **0.1m/s 이하**일 때 힘 계산 `max(inputSize*20000 - mass*gravityScale*.5,0)`; 정지/입력 부족 시 0.
4. 이동 중 힘 계산 `input*20000 - velocityDirection*mass*gravityScale*.3`. 입력이 0.1보다 작을 때는 `velocityDirection*20000`을 추가로 뺌.
5. 힘이 0.1 미만이면 힘과 속도를 모두 0으로 만들고, **Ctrl 달리기 시 힘 2배**.
6. C#의 `AddForce(force*fixedDeltaTime)`에 대응하도록 **속도에 `force * delta² / mass`을 추가**.
7. 계산 뒤 **걷기 최대 4m/s, Ctrl 달리기 최대 6m/s**, Shift 웅크림 시 최대 1.8m/s.
8. 왼쪽 클릭 시 공격 팔 동작 타이머 재시작, 실이동 속도를 애니메이션 속도 파라미터로 사용.

원본의 Unity 2D와 Godot 3D의 충돌 물리 처리 방식은 다르므로 **비트 단위 동일한 엔진 시뮬레이션은 아닙니다**. Godot에 없는 `Rigidbody2D.mass` 및 `gravityScale`은 가상 매개변수(초기값 모두 1.0)로 노출했습니다. 캐릭터 애니메이션, 카메라 벽 충돌, 파츠 충돌, 턱 넘기, 앵커 및 판면 규칙은 CheRPG 기존 구현을 유지합니다.

## 검수
**HUD 마지막 줄**에서 `Unity C# input / force / anim speed` 확인. 평지에서 WASD 방향과 가감속, Ctrl 최대 6m/s, Shift 웅크림 우선, 대각선 속도, 왼쪽 클릭 공격 리셋을 확인해 주세요. 마찰 수식을 원본 그대로 옮겼으므로 이전 Godot 버전과 조작감은 다를 수 있습니다.

**1분 이상 걸리는 주요 플레이 테스트는 사용자 직접 수행합니다.** 자동 검사·짧은 프로젝트 로드·Windows EXE 빌드만 진행합니다. EXE의 회사 정보는 `CheRPG`이지만 디지털 서명은 별도입니다.
