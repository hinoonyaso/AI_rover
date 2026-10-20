# 050. 깊이 장애물: 오검출(바닥 요철·벽 램프), 상자 일부만 찍힘, 옆을 지나면 지워짐, 팽창 반경이 내접 반경보다 작음

## 증상
- 빈 방에서 24개 지점 중 20곳에서 깊이 장애물이 찍힘. 상자는 앞면만 찍히고, 로봇이 옆을 지날 때 상자 코스트맵이 줄어들었다.
  상자 간격이 −1~3 cm(스침)로 나왔고 여유/팽창을 키워도 개선되지 않았다.

## 원인 (데이터로 확인)
- 바닥 요철과 벽 아래 램프가 기준 깊이 영상과의 차이로 검출됨 → 오검출.
- 깊이 압출 0.15 m가 상자 두께(0.22 m)보다 짧아 뒤쪽 면이 코스트맵에 없음.
- depth 레이어의 레이캐스트 지우기가 카메라 시야 밖/옆을 지날 때 상자 칸을 지움(`costmap_snapshot.py --near-box`로 확인: 로봇 중심값 0/72인데 상자 가장자리까지 0.16 m).
- 팽창 반경 0.25가 내접 반경(0.13 + 여유)에 거의 같거나 작아서 여유를 키워도 비용 구배가 사라짐(여유 12~16 cm에서 오히려 우회 폭 감소).

## 해결 (sim 전용, 실기 설정 불변)
- `sim.launch.py`: `background_margin_mm` 100, `extrude_depth_m` 0.25(환경변수 `SIM_DEPTH_MARGIN_MM`, `SIM_DEPTH_EXTRUDE_M`).
- `nav2.launch.py`: sim에서 `min_obstacle_height` 0.09.
- 시험용 변형 `nav2_params_sim_avoid.yaml`: depth 레이어 `clearing: false`, `inflation_radius` 0.30, footprint 여유 +5 cm.

## 확인·재발 방지
- `tools/sim/check_depth_obstacles.py`(상자 35/35), `depth_fp_survey.py`(빈 방 오검출), `costmap_snapshot.py`.
- `inflation_radius`는 항상 내접 반경 + 여유보다 크게 둔다.
- 실기에서 depth 지우기를 끄면 움직이는 물체의 잔상이 남으므로 실기 적용은 따로 검증한다.
