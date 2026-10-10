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
// Extension frames sent only by the project firmware (firmware/rrc_m4, lib/protocol/include/rrc_ext.h);
// the vendor firmware never sends them. 한글: 자체 펌웨어 전용 확장 프레임(vendor 펌웨어는 안 보냄).
constexpr uint8_t kRrcFuncExtWheel = 0x21;
constexpr std::size_t kRrcExtWheelPayloadSize = 32;
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

// Build a "stop several motors" frame: FUNC 0x03, DATA = 03, mask (bit i = motor id i, 0-based).
// Documented in the Hiwonder RRC protocol PDF; accepted by this robot's firmware with no side
// effects and speed commands still work afterwards (2026-10-07, wheels lifted, troubleshooting/032).
// 한글: 여러 모터 정지 프레임(서브커맨드 0x03 + 비트마스크, 비트 i = 0부터 센 모터 id). 실기에서 수락/부작용 없음 확인.
std::vector<uint8_t> build_motor_stop_packet(uint8_t mask);

// Decode a battery report (FUNC 0x00, DATA = 04, u16 LE millivolts).
// 한글: 배터리 보고(FUNC 0, 04 + u16 LE mV)를 해석한다.
bool decode_battery(const RrcPacket & packet, uint16_t & millivolts);

// Decode an IMU packet (FUNC 0x07, 24 bytes -> 6 little-endian floats).
// 한글: IMU 패킷(24바이트 = float32 6개)을 해석한다.
bool decode_imu(const RrcPacket & packet, ImuRaw & imu);

// Build a bus servo read-position request: FUNC 0x05, DATA = 05, servo_id.
// Extension frame of the rrc_m4 firmware: DIAG_CMD (0x22) subcommand 0x01 = clear the e-stop latch. The vendor
// firmware ignores unknown functions, so it is safe to send to either firmware. 한글: e-stop 해제(자체 펌웨어 전용).
constexpr uint8_t kRrcFuncExtDiagCmd = 0x22;
constexpr uint8_t kRrcDiagClearEstop = 0x01;
std::vector<uint8_t> build_diag_clear_estop();

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

// Measured wheel feedback (FUNC 0x21, 50 Hz, rrc_m4 only): rps[4] f32 LE then counter[4] i32 LE.
// Index 0..3 = board ports 1..4, rps uses the SAME sign convention as MotorCommand (vendor: right
// wheels negative when rolling forward), so it feeds mecanum_forward() directly. Encoder scale
// 3,996 ticks/rev (measured 2026-10-10, firmware/rrc_m4/app/inc/app_config.h).
// 한글: 측정 바퀴 속도(FUNC 0x21). 부호 규약은 MotorCommand와 같아 mecanum_forward()에 바로 넣는다.
struct WheelFeedback
{
  float rps[4]{0, 0, 0, 0};
  int32_t counter[4]{0, 0, 0, 0};
};
bool decode_wheel_feedback(const RrcPacket & packet, WheelFeedback & out);

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
