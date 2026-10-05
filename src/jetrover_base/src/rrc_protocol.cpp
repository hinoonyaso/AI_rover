#include "jetrover_base/rrc_protocol.hpp"

#include <algorithm>
#include <cstring>

namespace jetrover_base
{

// 한글: 비트 단위 CRC-8/MAXIM 계산(테이블 없이 8회 시프트).
uint8_t crc8_maxim(const uint8_t * data, std::size_t length)
{
  uint8_t crc = 0x00;

  for (std::size_t i = 0; i < length; ++i) {
    crc ^= data[i];

    for (int bit = 0; bit < 8; ++bit) {
      if (crc & 0x01) {
        crc = (crc >> 1) ^ 0x8C;
      } else {
        crc >>= 1;
      }
    }
  }

  return crc;
}

// 한글: 헤더 + FUNC + LEN + DATA + CRC를 조립한다. CRC는 FUNC부터(index 2) 계산.
std::vector<uint8_t> build_packet(uint8_t function, const std::vector<uint8_t> & payload)
{
  std::vector<uint8_t> frame;
  frame.reserve(payload.size() + 5);

  frame.push_back(kRrcHeader1);
  frame.push_back(kRrcHeader2);
  frame.push_back(function);
  frame.push_back(static_cast<uint8_t>(payload.size()));
  frame.insert(frame.end(), payload.begin(), payload.end());
  frame.push_back(crc8_maxim(frame.data() + 2, frame.size() - 2));

  return frame;
}

// 한글: 모터 명령: DATA = 01(다중 설정), N, N×(id-1, rps float32 LE). 오른쪽 모터 부호 반전은 호출자(base_node) 책임.
std::vector<uint8_t> build_motor_packet(const std::vector<MotorCommand> & motors)
{
  std::vector<uint8_t> payload;
  payload.reserve(2 + motors.size() * 5);

  payload.push_back(0x01);
  payload.push_back(static_cast<uint8_t>(motors.size()));
  for (const auto & motor : motors) {
    payload.push_back(static_cast<uint8_t>(motor.id - 1));
    uint8_t bytes[4];
    std::memcpy(bytes, &motor.rps, 4);
    payload.insert(payload.end(), bytes, bytes + 4);
  }

  return build_packet(kRrcFuncMotor, payload);
}

bool decode_battery(const RrcPacket & packet, uint16_t & millivolts)
{
  if (packet.function != kRrcFuncSys || packet.payload.size() != 3 || packet.payload[0] != 0x04) {
    return false;
  }
  millivolts = static_cast<uint16_t>(packet.payload[1] | (packet.payload[2] << 8));
  return true;
}

bool decode_imu(const RrcPacket & packet, ImuRaw & imu)
{
  if (packet.function != kRrcFuncImu || packet.payload.size() != kRrcImuPayloadSize) {
    return false;
  }

  // 한글: 둘 다 리틀엔디안이라 memcpy로 float을 그대로 복사한다.
  // STM32 and Jetson (aarch64) are both little-endian.
  const uint8_t * p = packet.payload.data();
  std::memcpy(&imu.ax, p + 0, 4);
  std::memcpy(&imu.ay, p + 4, 4);
  std::memcpy(&imu.az, p + 8, 4);
  std::memcpy(&imu.gx, p + 12, 4);
  std::memcpy(&imu.gy, p + 16, 4);
  std::memcpy(&imu.gz, p + 20, 4);

  return true;
}

std::vector<uint8_t> build_bus_servo_read_position(uint8_t servo_id)
{
  return build_packet(kRrcFuncBusServo, {kRrcBusServoSubReadPosition, servo_id});
}

std::vector<uint8_t> build_bus_servo_set_position(
  double duration_s, const std::vector<BusServoTarget> & targets)
{
  // 한글: 이동 시간을 0~65초로 제한(ms로 u16에 담기 위해 65.535초 미만).
  const double clamped_s = std::min(std::max(duration_s, 0.0), 65.0);
  const uint16_t duration_ms = static_cast<uint16_t>(clamped_s * 1000.0);
  std::vector<uint8_t> payload;
  payload.push_back(kRrcBusServoSubSetPosition);
  payload.push_back(static_cast<uint8_t>(duration_ms & 0xFF));
  payload.push_back(static_cast<uint8_t>(duration_ms >> 8));
  payload.push_back(static_cast<uint8_t>(targets.size()));
  for (const auto & t : targets) {
    payload.push_back(t.id);
    payload.push_back(static_cast<uint8_t>(t.pulse & 0xFF));
    payload.push_back(static_cast<uint8_t>(t.pulse >> 8));
  }
  return build_packet(kRrcFuncBusServo, payload);
}

std::vector<uint8_t> build_bus_servo_torque(uint8_t servo_id, bool enable)
{
  return build_packet(
    kRrcFuncBusServo, {enable ? kRrcBusServoSubTorqueOn : kRrcBusServoSubTorqueOff, servo_id});
}

// 한글: 버스 서보 위치 응답: DATA = id, 05, success(0 정상/-1 실패), pulse int16 LE.
bool decode_bus_servo_position(const RrcPacket & packet, BusServoPosition & out)
{
  if (packet.function != kRrcFuncBusServo || packet.payload.size() != 5 ||
    packet.payload[1] != kRrcBusServoSubReadPosition)
  {
    return false;
  }
  out.id = packet.payload[0];
  out.success = static_cast<int8_t>(packet.payload[2]);
  out.pulse = static_cast<int16_t>(
    static_cast<uint16_t>(packet.payload[3]) | (static_cast<uint16_t>(packet.payload[4]) << 8));
  return true;
}

void RrcParser::feed(const uint8_t * data, std::size_t length)
{
  buffer_.insert(buffer_.end(), data, data + length);
}

bool RrcParser::next(RrcPacket & packet)
{
  while (true) {
    // 한글: AA 55 헤더를 찾는다. 버퍼 끝이 AA 단독이면 다음 바이트가 55일 수 있으니 남겨 둔다.
    // Find AA 55.
    auto it = buffer_.begin();
    while (it != buffer_.end()) {
      it = std::find(it, buffer_.end(), kRrcHeader1);
      if (it == buffer_.end() || std::next(it) == buffer_.end() ||
        *std::next(it) == kRrcHeader2)
      {
        break;
      }
      ++it;
    }
    buffer_.erase(buffer_.begin(), it);

    // Need at least AA 55 FUNC LEN.
    if (buffer_.size() < 4) {
      return false;
    }

    const std::size_t len = buffer_[3];
    const std::size_t total = 4 + len + 1;
    if (buffer_.size() < total) {
      return false;
    }

    const uint8_t calculated = crc8_maxim(buffer_.data() + 2, 2 + len);
    const uint8_t received = buffer_[total - 1];

    // 한글: 가짜 헤더이거나 깨진 프레임: AA 한 바이트만 버리고 다시 동기화한다(호스트/펌웨어 동일 동작).
    if (calculated != received) {
      // False header or corrupted frame: drop the AA and resync.
      buffer_.erase(buffer_.begin());
      continue;
    }

    packet.function = buffer_[2];
    packet.payload.assign(buffer_.begin() + 4, buffer_.begin() + 4 + len);
    buffer_.erase(buffer_.begin(), buffer_.begin() + total);
    return true;
  }
}

}  // namespace jetrover_base
