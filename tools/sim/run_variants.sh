#!/bin/bash
# 한글: Nav2 변형 파라미터 파일 여러 개를 S 시나리오별로 연속 시험한다(host에서 실행). 결과는 stdout(로그로 리다이렉트).
# Runs several Nav2 param variants over scenarios in sequence (host). Usage:
#   VARIANTS="a b" SCENS="S4 S2" REPEATS=6 bash tools/sim/run_variants.sh > /tmp/log 2>&1
# a variant "a" means tools/nav/ab_params/nav2_params_a.yaml
cd "$(dirname "$0")/../.."
for v in ${VARIANTS:?}; do for s in ${SCENS:-S4 S2}; do
  TAG=${v}_$s SCEN=$s REPEATS=${REPEATS:-6} CTRL=dwb APPROACH=1 LOGDIR=/tmp \
    PARAMS=tools/nav/ab_params/nav2_params_$v.yaml bash tools/sim/sim_avoid_run.sh 2>&1 | cut -c1-175
done; done
echo ALL_DONE
