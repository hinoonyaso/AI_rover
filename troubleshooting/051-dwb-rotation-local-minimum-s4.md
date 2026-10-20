# 051. 상자가 경로 정면(S4)일 때 DWB가 제자리 회전(±0.12 rad/s)에 갇혀 20~40초 정지

## 증상
- S4에서 시행의 약 25~50%가 상자 앞 0.3~0.4 m에서 vx=0, wz ±0.12로 번갈아 회전만 하다 timeout. 위치 오차 60~90 cm.

## 원인 (`dwb_eval_probe.py`로 /evaluation 확인)
- 이동 후보의 55~70%가 Oscillation 평가자에게 죽고, 남은 이동 후보는 상자 쪽 비용(BaseObstacle ≈ 13)이 붙어 회전 후보(총점 16.1)보다 불리(16.2~16.3). 점수 차가 0.1~0.2라 회전이 국소 최소가 됨.

## 해결 (sim 시험용 변형)
- `BaseObstacle.scale` 0.1 → 0.05, `Twirling.scale` 10 → 30. 둘 다 바꾼 변형만 S4 12/12, 최종 20/20. BaseObstacle만 낮추면 11/12, Oscillation 제거는 9/12, 팽창만 키우면 악화.

## 확인·재발 방지
- 정지 시 `dwb_eval_probe.py --scenario S4 --leg BA --at 6 14`로 후보 점수를 본다. 실기 적용 전 실기 S4형(정면 상자) 시험 필요.
