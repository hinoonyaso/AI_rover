# 048. Gazebo 시험에서 Nav2 목표가 1초 안에 취소됨 ("Transform data too old")

## 증상
- host Gazebo + Nav2에서 NavigateToPose 목표를 보내면 1초 안에 aborted. 로그에 "Transform data too old".

## 원인
- 설정 파일에 `use_sim_time: false`가 노드마다 명시돼 있어, launch 인자 `use_sim_time:=true`가 덮어쓰지 못했다. Nav2가 벽시계를 쓰고 TF/센서는 시뮬레이션 시간이라 시각이 어긋났다.

## 해결
- `src/jetrover_navigation/launch/nav2.launch.py`: `use_sim_time`이 true일 때 params 파일을 읽어 `use_sim_time: true`로 고친 임시 파일을 써서 쓴다(실기 경로는 그대로). 같은 자리에서 sim 전용으로 depth 최소 높이 −0.1 → 0.09도 바꾼다(050).

## 확인·재발 방지
- sim 시험 시 `ros2 param get /controller_server use_sim_time`이 true인지 본다. 실기 파라미터 파일은 바뀌지 않는다.
