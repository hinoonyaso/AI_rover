// 한글: RRC 프레임 코덱(호스트 쪽). 펌웨어의 firmware/rrc_m4/lib/protocol과 같은 와이어 포맷이다.
#pragma once

#include <cstddef>
#include <cstdint>
#include <vector>

namespace jetrover_base
{

// Frame layout: AA 55 | FUNC | LEN | DATA[LEN] | CRC8
// CRC covers FUNC + LEN + DATA (header excluded).
// 한글: 프레임 구조: AA 55 | FUNC | LEN | DATA | CRC8. CRC는 FUNC+LEN+DATA만 계산(헤더 제외).
constexpr uint8_t kRrcHeader1 = 0xAA;
constexpr uint8_t kRrcHeader2 = 0x55;
// 한글: FUNC 번호: 0=시스템(배터리), 3=모터, 5=버스 서보, 7=IMU.
constexpr uint8_t kRrcFuncSys = 0x00;
constexpr uint8_t kRrcFuncMotor = 0x03;
constexpr uint8_t kRrcFuncBusServo = 0x05;
constexpr uint8_t kRrcFuncImu = 0x07;
constexpr std::size_t kRrcImuPayloadSize = 24;
// 한글: 버스 서보 서브커맨드: 0x01 이동, 0x05 위치 읽기, 0x0B 토크 켜기, 0x0C 토크 끄기.
constexpr uint8_t kRrcBusServoSubReadPosition = 0x05;
constexpr uint8_t kRrcBusServoSubSetPosition = 0x01;
// 2026-10-05 실기 확인: 0x0B = 토크 해제(limp, 손으로 움직임), 0x0C = 토크 걸기(load). 공식 PDF 문서와 같고
// board.cpp의 `enable ? 0x0B : 0x0C` 가정과는 반대다(이전 코드는 이름이 뒤집혀 있었다).
// Verified on hardware: 0x0B releases (limp), 0x0C loads -- the opposite of what the names used to say.
constexpr uint8_t kRrcBusServoSubTorqueOn = 0x0C;
constexpr uint8_t kRrcBusServoSubTorqueOff = 0x0B;

struct RrcPacket
{
  uint8_t function{0};
  std::vector<uint8_t> payload;
};

// Raw values as sent by the STM32 (units not yet verified against firmware).
// 한글: STM32가 보낸 IMU 원시값: 가속도 g, 자이로 deg/s, 센서 원시 축(X=오른쪽,Y=뒤,Z=아래).
struct ImuRaw
{
  float ax{0}, ay{0}, az{0};
  float gx{0}, gy{0}, gz{0};
};

// CRC-8/MAXIM (poly 0x31 reflected = 0x8C, init 0x00).
// 한글: CRC-8/MAXIM(다항식 0x31 반사형 0x8C, 초기값 0). 펌웨어/프로토콜 PDF와 동일.
uint8_t crc8_maxim(const uint8_t * data, std::size_t length);

// One motor speed target. `id` is 1-based (board ports 1..4), `rps` is wheel rev/s.
// 한글: 모터 속도 목표 1개. id는 사람이 부르는 포트 번호 1~4이고 패킷에는 id-1(0부터)로 실린다. 단위는 바퀴 rev/s.
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
// 한글: 배터리 보고(FUNC 0, 04 + u16 LE mV)를 해석한다.
bool decode_battery(const RrcPacket & packet, uint16_t & millivolts);

// Decode an IMU packet (FUNC 0x07, 24 bytes -> 6 little-endian floats).
// 한글: IMU 패킷(24바이트 = float32 6개)을 해석한다.
bool decode_imu(const RrcPacket & packet, ImuRaw & imu);

// Build a bus servo read-position request: FUNC 0x05, DATA = 05, servo_id.
std::vector<uint8_t> build_bus_servo_read_position(uint8_t servo_id);

struct BusServoTarget
{
  uint8_t id;
  uint16_t pulse;  // 0..1000 <-> 0..240 deg
};

// Build a bus servo move frame: FUNC 0x05, DATA = 01, duration_ms u16 LE, N,
// N x (id u8, pulse u16 LE). Layout taken from Hiwonder's ros_robot_controller_cpp
// (Board::bus_servo_set_position); not yet exercised on this robot.
std::vector<uint8_t> build_bus_servo_set_position(
  double duration_s, const std::vector<BusServoTarget> & targets);

// Torque on/off for one bus servo: FUNC 0x05, DATA = 0B|0C, servo_id (Board::bus_servo_enable_torque).
// With torque off the servo is limp (observed 2026-10-05: an unpowered-torque arm sags).
// 한글: 토크 끄면 팔이 늘어진다(2026-10-05 관찰). 켤 때/끌 때 서브커맨드가 다르다.
std::vector<uint8_t> build_bus_servo_torque(uint8_t servo_id, bool enable);

struct BusServoPosition
{
  uint8_t id{0};
  int8_t success{-1};
  int16_t pulse{0};
};

// Decode a bus servo position report (FUNC 0x05, DATA = id, 05, success, pulse i16 LE).
bool decode_bus_servo_position(const RrcPacket & packet, BusServoPosition & out);

// Streaming parser: feed raw serial bytes, pop validated packets.
// Bad CRC frames are discarded and the parser resyncs on the next AA 55.
// 한글: 스트리밍 파서: 시리얼 바이트를 넣고 검증된 패킷을 꺼낸다. CRC가 틀리면 버리고 다음 AA 55에서 다시 동기화한다.
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
