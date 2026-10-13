# CheRPG 방향 전환 장치 0.0.3v — 지면 접촉 검증

## 작업 범위
- **캐릭터 0.0.1v의 기본 도형과 기존 30개 메시를 변경하지 않는다.**
- 링 지름은 수납 약 0.464 m, 전개 약 1.36 m, 허리 높이 0.748 m다.
- 링이 수평으로 확장되면 4개 앵커가 **수직 하강**하고, 각 받침은 지면의 기울기에 맞춰 기울어진다.
- 폰 신체는 회전하지 않는다. DEVICE_CTRL_HeadingOnly만 -Y → +X로 변경한다.
- 설치 반경은 2 m × 2 m 타일 범위 안이다.

## 개선한 문제
기존 0.0.2v의 받침 아래 약 0.019 m 틈을 없앴다. 0.0.3v에서는 지면의 법선 방향을 계산하고, 발판 원판 위 640개 지점을 샘플링해 지형과 겹치지 않도록 받침 높이를 미세 보정한다. 앵커 하부 신축 구간의 길이를 0.18–0.54 m로 제한한다.

## 지형별 수치 테스트 (표준 Python)
| 지면 | 결과 | 네 앵커 신축부 길이(m) |
| --- | --- | --- |
| 평지 | 통과 | 0.368 / 0.368 / 0.368 / 0.368 |
| X 방향 10° 경사 | 통과 | 0.284 / 0.454 / 0.454 / 0.284 |
| 대각 8° 경사 | 통과 | 0.273 / 0.369 / 0.464 / 0.369 |
| 미세 구릉/요철 | 통과 | 0.287 / 0.433 / 0.433 / 0.303 |
| X 방향 30° 경사 | 거부 (앵커 길이 한도 초과) | 0.097 / 0.653 / 0.653 / 0.097 |

이는 **샘플 지형에 대한 기하학적 접촉 계산**이다. 실제 게임 충돌·관절 토크·토질·하중을 검증한 것은 아니다. 30°만 차단한 것이 아니라 길이·범위 제약을 일반적으로 적용한다.

## 저장소 파일
- production/pawn_protagonist/modeling/direction_contact_solver.py: 독립 실행형 지면 판정 및 앵커 길이 계산
- production/pawn_protagonist/modeling/test_ground_contact.py: 네 종류 허용 / 한 종류 거부 자동 검증
- production/pawn_protagonist/modeling/pawn_direction_device_0_0_3v.py: Blender 5.2.2 기본도형 장치 및 키프레임
- .github/workflows/cherpg-direction-device-test.yml: Python 회귀 검사 → Blender 모델/GLB 생성 → 결과 검사

## Blender 도구 실행
기존 CheRPG Blender Tool에서 run_script를 선택하고
production/pawn_protagonist/modeling/pawn_direction_device_0_0_3v.py 를 입력한다.
성공하면 .blend, 애니메이션 .glb, 3개 정적 .glb, 3장 렌더 및 지면 접촉 보고서를 Actions 아티팩트로 받는다.

현재 확인한 것은 **Python 컴파일, 순수 Python 테스트, 별도 trimesh 정적 GLB 내보내기/재불러오기와 캐릭터 메시 동일성 검사**다. Blender 5.2.2 실제 실행 성공 여부와 Godot 통합은 별도 확인이 필요하다.

Godot 실게임 연결 시 발판 접지 높이는 실제 지형을 향한 RayCast3D 또는 PhysicsDirectSpaceState3D를 사용해 읽어야 한다. 현재 수학 지형 함수는 게임 내 실제 지형을 자동으로 읽지 않는다.
