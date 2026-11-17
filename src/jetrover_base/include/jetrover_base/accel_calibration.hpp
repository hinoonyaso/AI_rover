#pragma once
#include <array>
#include <cmath>
#include <vector>

namespace jetrover_base
{
// Validate finite axis calibration before using it for sensor output.
// 한글: 센서 출력에 적용하기 전 축별 보정값의 유효 범위를 검사한다.
inline bool valid_accel_calibration(const std::vector<double> & offset, const std::vector<double> & scale)
{
  if (offset.size() != 3 || scale.size() != 3) return false;
  for (std::size_t i = 0; i < 3; ++i) {
    if (!std::isfinite(offset[i]) || !std::isfinite(scale[i]) || std::abs(offset[i]) > 10.0 ||
        scale[i] < 0.5 || scale[i] > 2.0) return false;
  }
  return true;
}

// Apply offset then scale in the published IMU frame, in m/s^2.
// 한글: 발행 IMU 좌표계의 가속도(m/s^2)에 오프셋 후 배율을 적용한다.
inline std::array<double, 3> calibrate_accel(const std::array<double, 3> & raw,
                                             const std::vector<double> & offset,
                                             const std::vector<double> & scale)
{
  return {(raw[0]-offset[0])*scale[0], (raw[1]-offset[1])*scale[1], (raw[2]-offset[2])*scale[2]};
}
}  // namespace jetrover_base
