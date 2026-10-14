# CheRPG 0.0.20v — 이번 요청에서 1회 허용한 실제 물리 플레이 테스트 결과

**환경:** GitHub Actions Ubuntu Godot 4.7.2 Stable, 독립 모션 테스트장 `res://scenes/MotionLab.tscn`.
**실행:** 실제 씬을 인스턴스화해 실제 `InputEventKey`를 공급하고 Godot `physics_frame`을 반복하는 헤드리스 게임 물리 검증.
**결과:** [Workflow run 38484576045](https://github.com/zzunlsj/cherpg/actions/runs/38484576045) **성공**, `CHERPG_REAL_PLAYTEST_PASS`.

## 두 단계 실험

### 첫 시도 (실패): [run 38484428309](https://github.com/zzunlsj/cherpg/actions/runs/38484428309)

- 카메라 yaw 0°: W → 월드 -Z 방향 이동, **성공**.
- 카메라 yaw 90°: W → 월드 -X 방향 이동, **성공**.
- 수직 90° 탑뷰: 동일 yaw의 수평 이동, **성공**.
- Ctrl 달리기: 최고 **6.000m/s**, **성공**.
- **W 해제 후 24프레임에도 속도 4.000m/s, 실패**. Ctrl 달리기 해제 후에도 속도 4.000m/s 잔존.
- 원인: 기본 60Hz `force=20000`의 감속 충격 `force * dt² / mass`는 약 5.56m/s로 걷기 4m/s를 한 틱에 넘어가며, 해제 후 속도가 반대방향으로 뒤집히는 진동이 지속됨. 단순한 정지 임계 속도 0.1→0.6 상향으로는 해결되지 않음.

### 수정 후 최종 실험 (성공): [run 38484576045](https://github.com/zzunlsj/cherpg/actions/runs/38484576045)

- 카메라 yaw 0°: W 입력 후 위치 `(0.0, 0.000843, 34.92289)`, 속도 **4.000m/s**. 시작 z=38에서 -Z로 진행, **성공**.
- 카메라 yaw 90°: W 입력 후 `(-3.117774, 0.000843, 38.0)`, 즉 카메라 기준 -X 방향, **성공**.
- yaw 90° 및 90° 완전 탑뷰: W 입력 후 `(-3.089457, 0.000843, 38.0)`, **성공**.
- Ctrl+W: 속도 **6.000m/s**, 원래 Ctrl 달리기 유지, **성공**.
- W/Ctrl 해제 후 28프레임 정지: **0.000m/s**, **성공**.
- Shift: `crouching == true`, `running == false`, **성공**.
- `CHERPG_PLAYTEST_END issues=0` 및 `CHERPG_REAL_PLAYTEST_PASS`.

## 최종 코드 변경
- `pawn_controller.gd`: C# 입력을 `camera_forward/camera_right`로 월드 XZ에 투영해 원래 CheRPG 카메라 기준 진행 방향 복구.
- `SOURCE_MIN_SPEED := 0.6`으로 변경 (이전 `0.1`에서 증가).
- 키 해제 등 `input_magnitude < SOURCE_MIN_FORCE` 제동 중, 예상 속도가 이전 속도와 반대방향이 되면 물리 속도를 `Vector2.ZERO`로 한정. 이는 **원본 Unity 힘 적분의 불안정한 역방향 오버슈트를 제거하는 CheRPG 전용 수정**.
- **4m×4m 판면 이동 제한·앵커·Ctrl 벽 좌표계 등반·Shift 웅크리기 및 90° 탑뷰 카메라** 로직은 그대로 유지.

## 범위와 이후 조치
- 이번 요청에 한해 코드로 실제 씬을 움직이는 엔진 물리 실험을 수행.
- 테스트를 자동 배포 CI에서 다시 제거하여 **향후 장시간 테스트는 사용자 담당**. `tests/playtest_camera_motion_0.0.20v.gd`는 수동 재현용으로만 보존.
- **헤드리스 입력·물리 테스트**이며 Windows GUI에서 조작하는 시각적 애니메이션 품질 및 장시간 경사·등반 안정성까지 검증한 것은 아님.
