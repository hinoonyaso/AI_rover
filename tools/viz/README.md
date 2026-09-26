# 시각화 (SSH 환경용)

사용자는 VS Code Remote-SSH로 접속해서 RViz 창을 볼 수 없다. 대신 그림 파일을 만들거나, 브라우저로 스트리밍한다.

## 카메라: 실시간으로 보기 (web_video_server)
가장 간단하다. 카메라(또는 다른 이미지 토픽)를 MJPEG로 웹에 띄우고 브라우저로 본다.

```bash
# 터미널 1: 카메라
source ~/jetrover_ws/install/setup.bash
ros2 launch jetrover_perception camera.launch.py

# 터미널 2: 웹 서버
source ~/jetrover_ws/install/setup.bash
ros2 launch jetrover_perception web_video.launch.py
```
그다음 VS Code 하단의 **포트(Ports) 탭**에서 `8080`을 포워딩하고, 로컬 브라우저(또는 VS Code Simple Browser)에서
`http://localhost:8080`을 연다. 이미지 토픽 목록이 나오고, 각각 클릭하면 실시간 스트림이 보인다
(예: `http://localhost:8080/stream?topic=/depth_cam/color/image_raw`).
depth 이미지는 원시값이라 그대로 보면 잘 안 보일 수 있다 — 필요하면 `colormaps` 옵션이나
`/depth_cam/depth/image_raw/compressedDepth`처럼 압축 토픽을 시도한다.

## 스캔/지도: PNG 저장 (snapshot.py)
```
python3 ~/jetrover_ws/tools/viz/snapshot.py --frame map    # SLAM이 떠 있을 때 (지도 포함)
python3 ~/jetrover_ws/tools/viz/snapshot.py --frame odom   # SLAM 없이
# 결과: ~/jetrover_ws/tools/viz/out/snapshot.png  (VS Code에서 열기)
```
- 그림: 스캔 점(색=거리), `/map`(흰색 빈 공간 / 검은색 장애물 / 회색 미지), 로봇 윤곽(URDF 임시 0.30×0.20 m 상자, 실측 아님)과 정면 화살표, `lidar_frame`/`imu_link` 위치.
- `robot.launch.py`(와 SLAM은 `jetrover_navigation slam.launch.py`)가 떠 있어야 한다.

## 실시간 화면이 더 필요하면 (Foxglove)
`/scan`, `/map`, TF, 카메라를 한 화면에서 같이 보려면 web_video_server보다 Foxglove가 낫다.
```
sudo apt install ros-jazzy-foxglove-bridge
ros2 run foxglove_bridge foxglove_bridge      # WebSocket 8765
```
VS Code의 포트 탭에서 8765를 포워딩하고 PC의 Foxglove(앱 또는 브라우저)에서 `ws://localhost:8765`로 연결한다.
