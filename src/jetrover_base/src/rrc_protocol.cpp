#include "jetrover_base/rrc_protocol.hpp"

#include <algorithm>
#include <cstring>

namespace jetrover_base
{

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

void RrcParser::feed(const uint8_t * data, std::size_t length)
{
  buffer_.insert(buffer_.end(), data, data + length);
}

bool RrcParser::next(RrcPacket & packet)
{
  while (true) {
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
