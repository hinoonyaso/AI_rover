# Depth 기반 근거리 장애물 처리

신뢰 수준 표기: 아래 "현재 방식"은 **구현·실기 확인(소수 시험)**, "목표 방식"은 **계획**.
**현재 방식은 임시(temporary near-field obstacle detection strategy)다.** 최종 구조가 아니다.

## 1. 왜 필요한가
2D LiDAR 스캔 평면보다 낮거나 얇은 물체(의자 다리, 낮은 상자)는 `/scan`에 안 잡힌다. 실제 충돌이 있었다
(troubleshooting/021). 뒤쪽 약 160°는 로봇팔에 가려 LiDAR가 없고(022), depth 카메라는 전방 바닥만 본다.

## 2. 현재 방식 (`jetrover_perception/scripts/sparse_point_cloud.py`)
```
depth(stride 8로 성기게) → 기준 depth(background)와 비교 → 기준보다 60 mm 이상 가까운 픽셀만 남김
  → camera_info로 XYZ 투영 → 시선 방향으로 0.3 m까지 0.1 m 간격 복제(extrusion) → PointCloud2
  → local + global costmap의 obstacle_layer(depth_cloud) + collision_monitor
```
기준 이미지(`config/depth_background_ref*.npy`)는 **홈 자세에서 장애물 없이 10프레임 median으로 캡처**한 것.

### 왜 이렇게 했나 (023)
처음엔 `base_footprint` 기준 XY 사각형(self-filter)으로 로봇 자신(바퀴/섀시)을 걸렀는데, 카메라가 팔 끝에서 아래를 보는 시차 때문에
로봇 앞 35 cm 물체가 "로봇 안쪽"으로 계산되어 **진짜 장애물이 지워졌다.** 높이로도 못 가른다(바퀴 윗부분 ≈ 9.7 cm, 물체 4.5~8.8 cm).
→ "그 자리에 원래 뭐가 있었나"(기준 비교)로 바꿨다.

## 3. 한계 (정직하게)
| 한계 | 이유 | 영향 |
|---|---|---|
| 기준 이미지가 **팔 자세·카메라 자세·바닥·로봇 위치·depth 노이즈**에 의존 | 기준과 현재 배경이 달라지면 false positive/negative | 서보 backlash나 home pose 변경 시 기준 재캡처 필요. 거짓 장애물/미검출 가능 |
| **0.3 m extrusion은 휴리스틱** | 카메라는 장애물 앞면만 본다. 뒤쪽 깊이는 모른다 | 얇은 막대(3 cm)도 30 cm로 부풀고, 깊이 60 cm 상자는 부족. 일반적인 장애물 형상이 아니라 *보수적 점유 근사* |
| 감지 범위 약 0.18~0.51 m | 홈 자세에서 카메라가 바닥을 내려다봄 | 회피 여유가 작아 속도를 0.12 m/s로 제한해야 했다(028) |
| 후방 미감시 | 카메라 전방 고정 | 후진 금지로 우회(`min_vel_x 0`, BackUp 제거) |
| global costmap에 넣은 것은 DWB 기준 해결책 | DWB는 전역 경로만 따라가서 depth가 전역에 없으면 장애물 앞에서 멈춤(026) | stale/ghost 장애물 위험 → §5 검증 필요 |
| 시험 횟수 부족 | 성공이 소수 시행 | "한 번 성공한 휴리스틱"인지 반복 가능한지 미판별 → baseline 시나리오 B가 바로 그 검증 |

## 4. 목표 방식 (계획)
```
Depth → 3D PointCloud → TF(camera→base) → 로봇 형상 self-filter(URDF 기반 마스크) → ground filtering
  → ROI/높이 필터 → temporal filtering(여러 프레임 누적) → Nav2 obstacle 입력
```
- self-filter는 XY 사각형이 아니라 **URDF 로봇 형상을 카메라 영상/포인트클라우드 기준으로 마스크**한다 (023의 실패 원인 해소).
- extrusion 대신 **관측 누적 + costmap inflation**으로 두께 불확실성을 처리한다.
- 팔 자세에 독립적이 되도록 TF 기반으로 한다 (현재는 홈 자세 고정이 전제).
- 이 전환은 baseline/엔코더/MPPI **이후** 판단한다 (ROADMAP). 지금 방식의 한계를 정량화하는 것이 먼저다.

## 5. 검증 항목 (baseline 시나리오 B와 함께, 모터 시험 필요)
1. **mark/clear**: 장애물 등장 → costmap에 점유 표시 → 제거 후 몇 초 뒤 clear 되는지(시간 기록).
2. **ghost obstacle**: 장애물을 한 위치에 둔 뒤 다른 위치로 이동했을 때 이전 위치가 남지 않는지.
3. **FOV 밖**: 센서 시야 밖으로 나간 장애물이 stale로 남는지(`clearing`/`obstacle_max_range` 동작).
4. **기준 이탈**: 홈 자세를 일부러 약간 바꿨을 때 false positive가 몇 개 생기는지(기준 의존성의 크기를 수치로).
5. **두께**: 얇은 막대/깊은 상자에서 extrusion이 costmap을 얼마나 과/소 점유시키는지.
(depth를 끈 채 주행하는 대조 시험은 하지 않는다 — 정지 상태 OFF/ON costmap 비교로 대체, `prd/nav2-baseline-test-plan.md`.) 결과는 `docs/benchmarks/navigation/`에 표로 남기고, 실패는 `troubleshooting/`에 기록한다.
