#pragma once

#include <cstddef>
#include <cstdint>
#include <vector>

namespace jetrover_base
{

// Frame layout: AA 55 | FUNC | LEN | DATA[LEN] | CRC8
// CRC covers FUNC + LEN + DATA (header excluded).
constexpr uint8_t kRrcHeader1 = 0xAA;
constexpr uint8_t kRrcHeader2 = 0x55;
constexpr uint8_t kRrcFuncSys = 0x00;
constexpr uint8_t kRrcFuncMotor = 0x03;
constexpr uint8_t kRrcFuncImu = 0x07;
constexpr std::size_t kRrcImuPayloadSize = 24;

struct RrcPacket
{
  uint8_t function{0};
  std::vector<uint8_t> payload;
};

// Raw values as sent by the STM32 (units not yet verified against firmware).
struct ImuRaw
{
  float ax{0}, ay{0}, az{0};
  float gx{0}, gy{0}, gz{0};
};

// CRC-8/MAXIM (poly 0x31 reflected = 0x8C, init 0x00).
uint8_t crc8_maxim(const uint8_t * data, std::size_t length);

// One motor speed target. `id` is 1-based (board ports 1..4), `rps` is wheel rev/s.
struct MotorCommand
{
  uint8_t id;
  float rps;
};

// Build a complete frame (header + FUNC + LEN + DATA + CRC).
std::vector<uint8_t> build_packet(uint8_t function, const std::vector<uint8_t> & payload);

// Build a motor command frame: FUNC 0x03, DATA = 01, N, N x (id-1 u8, rps f32 LE).
std::vector<uint8_t> build_motor_packet(const std::vector<MotorCommand> & motors);

// Decode a battery report (FUNC 0x00, DATA = 04, u16 LE millivolts).
bool decode_battery(const RrcPacket & packet, uint16_t & millivolts);

// Decode an IMU packet (FUNC 0x07, 24 bytes -> 6 little-endian floats).
bool decode_imu(const RrcPacket & packet, ImuRaw & imu);

// Streaming parser: feed raw serial bytes, pop validated packets.
// Bad CRC frames are discarded and the parser resyncs on the next AA 55.
class RrcParser
{
public:
  void feed(const uint8_t * data, std::size_t length);

  // Returns true and fills `packet` if a complete, CRC-valid frame is available.
  bool next(RrcPacket & packet);

private:
  std::vector<uint8_t> buffer_;
};

}  // namespace jetrover_base
