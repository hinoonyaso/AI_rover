# 046. Gazebo 스캔 월드에서 자동 위치 추정(scan_match_init)이 37 cm·35° 틀림

- 날짜: 2026-10-18
- 상태: **미해결(우회)**. 시뮬레이션 실행기는 정답 위치로 초기화한다.

## 증상
`room_lap2_objects.sdf`에서 로봇을 (1.02, 0.65, 83°)에 스폰하고 `nav2.launch.py use_sim_time:=true`(기본 `auto_localize:=true`)를 띄우자
`scan_match_init`이 `published /initialpose (0.95, 1.02, 118deg)`를 냈다. 정답과 37 cm, 35° 다르다. AMCL은 그 자리로 수렴했다("0.3 cm from match").

## 원인 (추정)
- 스캔 매칭 후보 중 틀린 곳의 점수가 더 높았다. 스캔한 방 메쉬의 LiDAR 높이 형상(가구·메쉬 구멍)이 2D 지도(2026-10-04 실기 지도)와 군데군데 달라서일 수 있다.
  방 정합 잔차 중앙값은 4.4 cm지만 국소적으로는 더 다를 수 있다.
- 미확인: 이 자리에서만 생기는지, 매칭 신뢰 기준(점수 ≥ 0.80·차이 ≥ 0.10)을 통과했는지 로그로 보지 않았다.

## 우회
- 시뮬레이션 주행 시험은 `auto_localize:=false`로 띄우고, 회차마다 Gazebo 정답 자세를 `/initialpose`로 준다(`tools/sim/run_scenarios.sh`와 같은 방식).

## 남은 일
- 정밀 접근(`prd/sim-avoidance-precision.md` 4단계)은 AMCL을 믿으므로, 시뮬레이션에서 AMCL 추정과 정답의 차이를 회차마다 기록한다.
- 새 2D 지도(같은 스캔 bag으로 slam_toolbox, 체크리스트 8.14.7)가 생기면 다시 확인한다.
