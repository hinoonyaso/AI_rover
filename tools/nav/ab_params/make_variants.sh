#!/usr/bin/env bash
# 한글: 직진 흔들림 A/B 시험 전용 파라미터 파일을 설치된 nav2_params.yaml에서 만든다(기본 설정은 안 바꿈).
#   두 파일 모두 BaseObstacle.scale 0.1 -> 0.02 (좁은 방에서 DWB가 전진 대신 제자리를 고르던 것 제거, troubleshooting/031)
#   wobble_limited  : A = LimitedAccelGenerator (현재 기본)
#   wobble_standard : C = StandardTrajectoryGenerator + vy_samples 10 (2026-10-07 이전)
# Usage: make_variants.sh, then
#   ros2 launch jetrover_navigation nav2.launch.py params_file:=$HOME/jetrover_ws/tools/nav/ab_params/nav2_params_wobble_limited.yaml
set -euo pipefail
src=~/jetrover_ws/install/jetrover_navigation/share/jetrover_navigation/config/nav2_params.yaml
dir=$(cd "$(dirname "$0")" && pwd)
test_only='s|^\(\s*\)BaseObstacle.scale: 0.1 .*|\1BaseObstacle.scale: 0.02  # WOBBLE TEST ONLY (default 0.1)|'
sed -e "$test_only" "$src" > "$dir/nav2_params_wobble_limited.yaml"
sed -e "$test_only" \
    -e 's|trajectory_generator_name: "dwb_plugins::LimitedAccelGenerator"|trajectory_generator_name: "dwb_plugins::StandardTrajectoryGenerator"|' \
    -e 's|^\(\s*\)vy_samples: 11 .*|\1vy_samples: 10  # A/B variant: pre-2026-10-07 value|' \
    "$src" > "$dir/nav2_params_wobble_standard.yaml"
for f in wobble_limited wobble_standard; do
  echo "== $f"; diff "$src" "$dir/nav2_params_$f.yaml" | grep '^>' || true
done
rm -f "$dir/nav2_params_standard_gen.yaml"
