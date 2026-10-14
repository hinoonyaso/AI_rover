# 040 — host: Gazebo가 로딩 중 멈춤 / 스캔 메쉬가 Gazebo에 안 보임·회색 / 로봇 메쉬 경로 / 처리 스크립트가 안 꺼짐 (2026-10-14)

- 상태: **해결**(host에서 재현·확인), 원인 하나(gz-transport 전송 막힘)는 왜 생겼는지 미확인
- 관련: `tools/scan/host_rtabmap.sh`, `tsdf_from_rtabmap.py`, `room_assets.py`, `blender_ply_to_glb.py`, `host_sim_check.sh`, `sim_color_check.py`,
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

## 5. 색이 회색 → 텍스처로 굽기
- 증상: RGB는 정상(PLY 정점 색 표준편차 0.26~0.28, glb에 `COLOR_0` 있음)인데 Gazebo GUI·시뮬레이션 카메라 모두 회색(채도 0.1).
- 원인: 이 glb의 정점 색이 Gazebo Harmonic 메쉬 로딩·렌더링 경로에서 반영되지 않는다(머티리얼에 텍스처 없음 → 기본 재질).
- 해결: `blender_ply_to_glb.py ... bake=2048` — UV를 만들고 Cycles로 DIFFUSE COLOR만(조명 제외) 2048² 알베도에 구워
  `baseColorTexture`로 연결(glb에 PNG 내장). 거친 단계:
  1. `uv.smart_project`: 노이즈 많은 스캔 메쉬가 삼각형마다 섬이 되어 텍스처 4.9 %만 채움(점 무늬) → `uv.lightmap_pack`.
  2. lightmap_pack + 30만 삼각형: 칸이 약 4×4 px라 굽지 못한 칸·mipmap이 이웃(다른 물체) 색을 섞어 흰 벽에 검은 얼룩.
     margin 1 → 16(EXTEND)으로 88.7 % 채웠지만 얼룩 남음. 검은 정점의 98.9 %는 실제 어두운 물체 위(데이터 문제 아님).
  3. **visual 10만 삼각형 + 2048**: 얼룩 사라짐(4096도 눈으로 차이 없음, 640×360 카메라). LiDAR-지도 거리 중앙값 그대로(11.0 vs 10.9 cm).
  xatlas(UV 전용 라이브러리)는 30만 삼각형에서 15분 넘게 끝나지 않아 중단.
- GUI 주의: 노트북 host는 화면이 Intel(UHD 630)에 붙어 있어 GUI가 Mesa로 그리면 회색·RTF 0.52·카메라 7.8 fps.
  **`__NV_PRIME_RENDER_OFFLOAD=1 __GLX_VENDOR_LIBRARY_NAME=nvidia`**로 띄우면 색 정상, RTF 0.91, 카메라 13.9 fps.

## 6. 로봇이 안 보임 / 스캔 바닥이 4 cm 떠 있음 / 시뮬레이션 LiDAR가 자기 덮개를 봄 (2026-10-14 밤, 물체 추가 중)
- 로봇 안 보임: 매 실행 로그에 `Unable to find file model://jetrover_description/meshes/...` 70개 — GZ_SIM_RESOURCE_PATH에
  jetrover_gazebo/models만 있었다. 몸체 visual·충돌 메쉬가 전부 빠진 채(바퀴 구 충돌만) 돌고 있었다.
  → sim.launch.py가 jetrover_description share의 상위 폴더도 추가. 오류 0개, GUI에 로봇 표시.
- 스캔 바닥 z = 0.044 m: 높이 3 cm 큐브가 메쉬 바닥에 묻힌다. → room_assets.py가 바닥(위쪽 법선 정점 중앙값)을 z = 0으로 내리고,
  visual은 바닥 유지(+3 mm, 바닥 평면과 깜빡임 방지), 충돌 메쉬에서는 바닥 제거(물리는 평평한 바닥 평면).
- 메쉬가 들어오자 시뮬레이션 LiDAR가 뒤쪽 검은 덮개(back_shell_black, z 0.002~0.158 m가 LiDAR 높이 0.04 m를 가로지름)를
  0.16~0.27 m(LiDAR 프레임 ±12~25°)로 잡았다. 실기는 그 구간 값이 없다(tol015 bag 243 스캔, 유효 0 %; 0.3 m 미만 빔 0개).
  → 덮개 visual에 `visibility_flags 2`, LiDAR에 `visibility_mask 0xFFFFFFFD`: LiDAR만 덮개를 못 본다. 0.3 m 미만 빔 0개.
  남는 차이: 그 구간에서 실기는 값이 없고 시뮬레이션은 너머를 본다.
  (sim xacro의 "팔이 뒤쪽을 가린다" 주석은 메쉬가 없어 적용된 적이 없었다 — 고침.)

## 7. 시뮬레이션 그리퍼가 큐브를 못 집음 (mimic)
- 증상: `r_joint`만 명령대로 움직이고 손가락 관절 5개는 `/joint_states`에도 없음. 로그 `Attempting to create a mimic constraint for
  joint [l_in_joint] but the chosen physics engine does not support mimic constraints`(DART).
- 해결: sim xacro ros2_control에 l_joint, l_in/l_out, r_in/r_out을 상태 인터페이스만으로 등록 → gz_ros2_control이
  `Joint 'l_joint' is mimicking joint 'r_joint' with multiplier -1` 식으로 따라 움직임(공식 gripper_mimic_joint_example 방식).
  확인: 6개 관절이 배율대로 일치, 큐브 3개 집어 들어 올림. 위 DART 오류 문구는 계속 찍히지만 무해.
- 실수 기록: 확인 명령에 `pgrep -f "...arm_hold.py"`를 ssh 명령줄에 그대로 넣어 그 셸 자신이 잡혀 죽음(exit 255) → 스크립트 파일로,
  패턴을 나눠 씀(`"arm_""hold.py"`).

## 확인 못 한 것 / 남은 한계
- 1번의 근본 원인(왜 discovery 전송이 막히는지).
- Intel(Mesa) GUI에서 텍스처가 왜 회색인지(같은 실행의 시뮬레이션 카메라는 색이 나옴).
