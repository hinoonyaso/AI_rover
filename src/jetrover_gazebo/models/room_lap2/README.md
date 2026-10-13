# room_lap2 — 스캔한 방 모델 (Phase 3, host Blender → Git LFS)

현재 에셋(2026-10-14)은 **자동 1차본**: `tools/scan/room_assets.py` + `blender_ply_to_glb.py`(수작업 정리 없음, 정점 색은 Gazebo에서 안 보임,
충돌 메쉬는 자동 감량 10.7k 삼각형). 기록 `docs/benchmarks/sim/room_scan_20261014.md`.

## Blender 내보내기 규칙 (이대로 맞추면 바로 Gazebo에 들어감)
| 항목 | 규칙 |
|---|---|
| 단위 | **미터** (Blender Unit Scale 1.0, 스캔 결과의 미터 스케일 유지 — RTAB-Map/Open3D는 이미 미터) |
| 축 | **Z 위, X/Y = 지도 축** (glTF/DAE 내보낼 때 "Y Up" 끄기 또는 Z-up 확인) |
| 원점 | **지도(map) 원점**. `tools/scan/validate_room_alignment.py`로 구한 T_map←scan을 적용한 뒤 내보낸다 |
| 바닥 | z = 0 (로봇 base_footprint 높이). 바닥면은 메쉬에서 빼도 됨(월드에 바닥 평면 있음) |
| visual | `meshes/room_visual.glb`(model.sdf uri). **glTF는 Z-up 그대로(`export_yup` 끔)** — Gazebo는 Y-up을 되돌리지 않는다(troubleshooting/040). 감량 목표 ≤ 300k 삼각형, 텍스처 ≤ 2048² |
| collision | `meshes/room_collision.stl`: **단순 형상**(벽 = 상자, 책상 = 상판+다리 따로, 의자 = 상자). ≤ 5k 삼각형. 로봇이 들어갈 수 있는 틈(책상 아래 등)은 막지 않는다 |
| 텍스처 | `materials/textures/` (DAE가 상대경로로 참조) |

## git
메쉬/텍스처는 **Git LFS**(저장소 루트 `.gitattributes`). host에서 1회: `sudo apt install git-lfs && git lfs install`.
Jetson에는 git-lfs가 없어 포인터 파일만 받는다(Jetson에서는 Gazebo를 돌리지 않으므로 무관).

## 사용
에셋을 넣으면: `python3 scripts/map_to_world.py <map.yaml> worlds/room_lap2.sdf --room-model room_lap2 --no-walls`
→ `ros2 launch jetrover_gazebo sim.launch.py world:=room_lap2.sdf` (launch가 `models/`를 GZ_SIM_RESOURCE_PATH에 넣음).
