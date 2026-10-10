// RRC 프레임 코덱 단위시험 (하드웨어/ROS 불필요). Unit tests for the host-side RRC codec.
#include <gtest/gtest.h>

#include <cstring>
#include <vector>

#include "jetrover_base/rrc_protocol.hpp"

using namespace jetrover_base;  // NOLINT

namespace
{
RrcPacket feed_one(const std::vector<uint8_t> & bytes, bool & ok)
{
  RrcParser parser;
  parser.feed(bytes.data(), bytes.size());
  RrcPacket packet;
  ok = parser.next(packet);
  return packet;
}
}  // namespace

// CRC-8/MAXIM 표준 검증값: "123456789" -> 0xA1.
TEST(Crc8, StandardCheckValue)
{
  const char * s = "123456789";
  EXPECT_EQ(crc8_maxim(reinterpret_cast<const uint8_t *>(s), 9), 0xA1);
}

TEST(Crc8, EmptyIsZero)
{
  EXPECT_EQ(crc8_maxim(nullptr, 0), 0x00);
}

TEST(BuildPacket, LayoutAndCrcExcludesHeader)
{
  const auto f = build_packet(0x03, {0x01, 0x02});
  ASSERT_EQ(f.size(), 7u);
  EXPECT_EQ(f[0], 0xAA);
  EXPECT_EQ(f[1], 0x55);
  EXPECT_EQ(f[2], 0x03);
  EXPECT_EQ(f[3], 2);
  EXPECT_EQ(f.back(), crc8_maxim(f.data() + 2, 4));
}

TEST(MotorPacket, IdIsZeroBasedOnWire)
{
  const auto f = build_motor_packet({{1, 1.0f}, {4, -2.0f}});
  // AA 55 03 LEN | 01 N | id rps(4) id rps(4) | CRC
  ASSERT_EQ(f.size(), 4u + 2 + 10 + 1);
  EXPECT_EQ(f[2], kRrcFuncMotor);
  EXPECT_EQ(f[4], 0x01);
  EXPECT_EQ(f[5], 2);
  EXPECT_EQ(f[6], 0);   // port 1 -> id 0
  EXPECT_EQ(f[11], 3);  // port 4 -> id 3
  float v;
  std::memcpy(&v, &f[12], 4);
  EXPECT_FLOAT_EQ(v, -2.0f);
}

// 한글: 전체 정지 프레임이 프로토콜 PDF/실기 시험과 같은 바이트인지 확인.
TEST(RrcProtocol, MotorStopPacketMatchesHardwareTest)
{
  // Bytes sent on the robot on 2026-10-07 (tools/stm32_diagnostics/motor_stop_hum_test.py).
  const std::vector<uint8_t> expected{0xAA, 0x55, 0x03, 0x02, 0x03, 0x0F, 0xD3};
  EXPECT_EQ(build_motor_stop_packet(0x0F), expected);
}

TEST(Parser, RoundTrip)
{
  bool ok;
  const auto p = feed_one(build_packet(0x07, {1, 2, 3}), ok);
  ASSERT_TRUE(ok);
  EXPECT_EQ(p.function, 0x07);
  EXPECT_EQ(p.payload, (std::vector<uint8_t>{1, 2, 3}));
}

TEST(Parser, BadCrcIsDiscarded)
{
  auto f = build_packet(0x07, {1, 2, 3});
  f.back() ^= 0xFF;
  bool ok;
  feed_one(f, ok);
  EXPECT_FALSE(ok);
}

TEST(Parser, ResyncsAfterGarbageAndCorruptedFrame)
{
  auto bad = build_packet(0x05, {9, 9});
  bad.back() ^= 0x01;
  const auto good = build_packet(0x00, {0x04, 0x10, 0x2F});
  std::vector<uint8_t> stream = {0x00, 0xAA, 0x12, 0xFF};  // 쓰레기 + 가짜 헤더
  stream.insert(stream.end(), bad.begin(), bad.end());
  stream.insert(stream.end(), good.begin(), good.end());
  bool ok;
  const auto p = feed_one(stream, ok);
  ASSERT_TRUE(ok);
  EXPECT_EQ(p.function, 0x00);
}

TEST(Parser, ByteByByteAndPartialFrame)
{
  const auto f = build_packet(0x07, {5, 6});
  RrcParser parser;
  RrcPacket p;
  for (std::size_t i = 0; i + 1 < f.size(); ++i) {
    parser.feed(&f[i], 1);
    EXPECT_FALSE(parser.next(p));  // 마지막 바이트 전까지는 불완전
  }
  parser.feed(&f.back(), 1);
  EXPECT_TRUE(parser.next(p));
  EXPECT_FALSE(parser.next(p));
}

TEST(Parser, TwoBackToBackFrames)
{
  auto a = build_packet(0x00, {1});
  const auto b = build_packet(0x07, {2});
  a.insert(a.end(), b.begin(), b.end());
  RrcParser parser;
  parser.feed(a.data(), a.size());
  RrcPacket p;
  ASSERT_TRUE(parser.next(p));
  EXPECT_EQ(p.function, 0x00);
  ASSERT_TRUE(parser.next(p));
  EXPECT_EQ(p.function, 0x07);
}

TEST(Decode, Battery)
{
  RrcPacket p{kRrcFuncSys, {0x04, 0xB8, 0x2E}};  // 0x2EB8 = 11960 mV
  uint16_t mv = 0;
  ASSERT_TRUE(decode_battery(p, mv));
  EXPECT_EQ(mv, 11960);
  p.payload = {0x04, 0x00};
  EXPECT_FALSE(decode_battery(p, mv));
  p.function = kRrcFuncImu;
  p.payload = {0x04, 0xB8, 0x2E};
  EXPECT_FALSE(decode_battery(p, mv));
}

TEST(Decode, ImuRejectsWrongSize)
{
  float v[6] = {0.1f, 0.2f, 0.3f, 4.f, 5.f, 6.f};
  RrcPacket p{kRrcFuncImu, std::vector<uint8_t>(24)};
  std::memcpy(p.payload.data(), v, 24);
  ImuRaw imu;
  ASSERT_TRUE(decode_imu(p, imu));
  EXPECT_FLOAT_EQ(imu.ax, 0.1f);
  EXPECT_FLOAT_EQ(imu.gz, 6.f);
  p.payload.pop_back();
  EXPECT_FALSE(decode_imu(p, imu));
}

// 한글: 자체 펌웨어 바퀴 피드백(FUNC 0x21): rps 4개 + 카운터 4개, 리틀엔디안. 실기 값 예(2026-10-10 바퀴 띄움).
TEST(Decode, WheelFeedbackFromRrcM4)
{
  const float rps[4] = {0.5f, -0.25f, 1.5f, -3.0f};
  const int32_t counter[4] = {11836, -11860, 70000, -1};
  std::vector<uint8_t> data(32);
  std::memcpy(data.data(), rps, 16);
  std::memcpy(data.data() + 16, counter, 16);
  const auto frame = build_packet(kRrcFuncExtWheel, data);
  RrcParser parser;
  parser.feed(frame.data(), frame.size());
  RrcPacket packet;
  ASSERT_TRUE(parser.next(packet));
  WheelFeedback fb;
  ASSERT_TRUE(decode_wheel_feedback(packet, fb));
  for (int i = 0; i < 4; ++i) {
    EXPECT_FLOAT_EQ(fb.rps[i], rps[i]);
    EXPECT_EQ(fb.counter[i], counter[i]);
  }
  // wrong size or function is rejected (vendor firmware never sends 0x21)
  packet.payload.resize(31);
  EXPECT_FALSE(decode_wheel_feedback(packet, fb));
  RrcPacket imu{kRrcFuncImu, std::vector<uint8_t>(32, 0)};
  EXPECT_FALSE(decode_wheel_feedback(imu, fb));
}

TEST(BusServo, ReadPositionRequestAndResponse)
{
  const auto f = build_bus_servo_read_position(3);
  EXPECT_EQ(f[2], kRrcFuncBusServo);
  EXPECT_EQ(f[4], 0x05);
  EXPECT_EQ(f[5], 3);

  // 응답: id, 05, success, pulse i16 LE (음수 pulse 포함)
  RrcPacket p{kRrcFuncBusServo, {3, 0x05, 0x00, 0x9C, 0xFF}};  // -100
  BusServoPosition pos;
  ASSERT_TRUE(decode_bus_servo_position(p, pos));
  EXPECT_EQ(pos.id, 3);
  EXPECT_EQ(pos.pulse, -100);
  p.payload[1] = 0x01;
  EXPECT_FALSE(decode_bus_servo_position(p, pos));
}

TEST(BusServo, SetPositionDurationClampAndLayout)
{
  const auto f = build_bus_servo_set_position(1.5, {{1, 500}, {10, 1000}});
  // DATA: 01, dur_lo, dur_hi, N, (id, lo, hi)*N
  EXPECT_EQ(f[4], 0x01);
  EXPECT_EQ(f[5] | (f[6] << 8), 1500);
  EXPECT_EQ(f[7], 2);
  EXPECT_EQ(f[8], 1);
  EXPECT_EQ(f[9] | (f[10] << 8), 500);
  EXPECT_EQ(f[11], 10);

  EXPECT_EQ(build_bus_servo_set_position(-3.0, {})[5], 0);  // 음수 -> 0
  const auto big = build_bus_servo_set_position(999.0, {});
  EXPECT_EQ(big[5] | (big[6] << 8), 65000);  // 65초로 제한
}

// 2026-10-05 실기 확인: 0x0B = 토크 해제, 0x0C = 토크 걸기 (troubleshooting/027 회귀 방지).
TEST(BusServo, TorqueSubcommandsMatchHardware)
{
  EXPECT_EQ(build_bus_servo_torque(1, true)[4], 0x0C);
  EXPECT_EQ(build_bus_servo_torque(1, false)[4], 0x0B);
}
