# 040 — host: Gazebo가 로딩 중 멈춤 / 스캔 메쉬가 Gazebo에 안 보임 / 처리 스크립트가 안 꺼짐 (2026-10-14)

- 상태: **해결**(host에서 재현·확인), 원인 하나(gz-transport 전송 막힘)는 왜 생겼는지 미확인
- 관련: `tools/scan/host_rtabmap.sh`, `tsdf_from_rtabmap.py`, `room_assets.py`, `blender_ply_to_glb.py`, `host_sim_check.sh`,
  `src/jetrover_gazebo/models/room_lap2/`, 기록 `docs/benchmarks/sim/room_scan_20261014.md`

## 1. Gazebo가 월드 로딩 중 멈춤 (시뮬레이션 시간이 안 흐름)
- 증상: `Switch controller timed out after 5 seconds!`, 컨트롤러 inactive, /scan·/odom 등 모두 NO DATA. 로봇 없는 빈 월드
  (`gz sim -s -r --iterations 2000 lap2_room.sdf`)도 끝나지 않음. CPU 3 %, SIGTERM에도 안 꺼짐.
- 원인(관찰): gz 프로세스 스레드 3개가 소켓 전송(`sock_alloc_send_pskb`)에서 막힘 — gz-transport의 네트워크 discovery 전송.
  같은 날 처음 한 번은 정상이었다(왜 막히기 시작했는지는 **미확인**: Wi-Fi + 유선 + docker0 인터페이스가 함께 있는 host).
- 해결: **`export GZ_IP=127.0.0.1`**(gz-transport를 loopback만). 빈 월드 2000 스텝이 5 s에 끝나고 시뮬레이션 정상.
  `host_sim_check.sh`에 넣었다. 수동 실행 때도 같은 터미널에서 export(→ `src/jetrover_gazebo/README.md`).

## 2. launch를 꺼도 `gz sim` 서버가 고아로 남음
- 증상: 위 시험을 반복하는 동안 `gz sim -s ...` 프로세스 7개가 부모 없이 누적, 다음 실행이 같은 gz 네트워크에서 섞임.
- 원인: launch는 `ruby gz` 래퍼만 끄고 실제 서버는 남는다. 비대화형 셸의 백그라운드 작업은 SIGINT를 무시한다(rtabmap도 같은 이유로 안 꺼짐).
- 해결: 스크립트에 `set -m`(job control → 별도 프로세스 그룹), 종료 때 그룹 전체에 INT → TERM → KILL. 실행마다 `GZ_PARTITION` 분리.

## 3. Open3D 0.20.0 TSDF가 빈 메쉬
- 증상: `ScalableTSDFVolume`(및 tensor `VoxelBlockGrid`)이 정상 RGB-D 한 장에서도 정점 0개. `UniformTSDFVolume`만 됨.
- 해결: host uv venv에서 **open3d 0.19.0 + numpy<2** 고정(같은 프레임 5.8천 정점). README에 기록.

## 4. 스캔 메쉬가 Gazebo에서 안 보임 → 보이지만 어긋남
- Open3D가 쓴 glb는 Gazebo Assimp가 거부: `Unable to import mesh`, `Cannot load mesh with zero sub-meshes` → 시뮬레이션 LiDAR가 방을 못 봄.
  → Blender(5.2, 헤드리스)로 PLY → glb 변환(`blender_ply_to_glb.py`).
- Blender 기본 `export_yup=True`(glTF 규약 Y-up)로 내보내면 Gazebo가 되돌리지 않아 방이 눕는다: 시뮬레이션 스캔과 지도 벽 거리 중앙값 19.7 cm.
  → **Z-up 그대로**(`export_yup=False`) 내보내면 시뮬레이션 스캔 = 메쉬 직접 레이캐스트(Open3D) 중앙값 5 cm 이내.

## 확인 못 한 것 / 남은 한계
- 정점 색이 Gazebo에서 렌더링되지 않는다(GUI에서 회색). 텍스처 굽기(Blender bake)가 필요 — 미실시.
- 1번의 근본 원인(왜 discovery 전송이 막히는지).
