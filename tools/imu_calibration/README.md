# IMU calibration

`base_node`가 발행하는 `/imu/data_raw`를 점검하고 보정하는 도구들이다.
먼저 `base_node`를 launch로 실행한다 (`base.yaml`이 적용되어야 한다).

```bash
source ~/jetrover_ws/install/setup.bash
ros2 launch jetrover_base base.launch.py
```

## 1. 축 방향 확인 — `check_axes.py`

`/imu/data_raw`가 base_link 방향(x 앞, y 왼쪽, z 위)인지 세 자세로 확인한다.

```bash
python3 check_axes.py
```

| 자세 | 기대값 |
|---|---|
| 평평하게 | z ≈ +9.8 |
| 왼쪽 면을 위로 (약 90°) | y ≈ +9.8 |
| 앞쪽을 아래로 (약 90°) | x ≈ −9.8 |

FAIL이면 `base_node.cpp`의 `publish_imu()` 축 변환을 다시 확인한다.
현재 STM32 센서 축은 X = 오른쪽, Y = 뒤, Z = 아래이고, 이를
`x = −y`, `y = −x`, `z = −z`로 변환한다.

## 2. 자이로 bias 보정 — `measure_gyro_bias.py`

로봇을 **완전히 정지**시킨 상태에서 실행한다.

```bash
python3 measure_gyro_bias.py 10                       # 측정만
python3 measure_gyro_bias.py 10 --write ~/jetrover_ws/src/jetrover_base/config/base.yaml
```

- 노드가 이미 빼고 있는 `gyro_bias`를 읽어서 `현재 값 + 측정 평균`을 새 bias로 계산한다.
- 측정 중 표준편차가 0.02 rad/s를 넘으면(로봇이 움직인 경우) 저장하지 않는다.
- `--write` 뒤에는 `colcon build`(설정 재설치) 후 다시 launch해야 적용된다.
- bias는 온도에 따라 조금 변하므로, 값이 이상해 보이면 다시 측정한다.

## 참고: 가속도 스케일

정지 상태에서 |acc|가 약 9.49 m/s²로 중력(9.81)보다 3% 정도 작고 축마다 배율이 다르다
(z ≈ −3.5%, x ≈ +4%). 아직 보정하지 않았다. EKF에서 가속도 비중이 커질 때 별도로 다룬다.
