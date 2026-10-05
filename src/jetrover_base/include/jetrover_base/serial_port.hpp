// 한글: STM32(CH9102 USB-UART)와 통신하는 시리얼 포트 래퍼 헤더.
#pragma once

#include <cstddef>
#include <cstdint>
#include <string>

namespace jetrover_base
{

// Minimal POSIX termios wrapper: raw 8N1, no flow control.
// 한글: 최소한의 POSIX termios 시리얼 래퍼: raw 8N1, 흐름 제어 없음. RAII로 소멸 시 자동 close.
class SerialPort
{
public:
  SerialPort() = default;
  ~SerialPort();

  SerialPort(const SerialPort &) = delete;
  SerialPort & operator=(const SerialPort &) = delete;

  // Returns false on failure; the reason is available from last_error().
  // 한글: 실패하면 false, 이유는 last_error()로 확인한다.
  bool open(const std::string & path, int baudrate);
  void close();
  bool is_open() const {return fd_ >= 0;}
  int fd() const {return fd_;}

  // Waits up to timeout_ms for data. Returns bytes read (0 on timeout), -1 on error.
  // 한글: timeout_ms 동안 데이터를 기다린다. 읽은 바이트 수(타임아웃이면 0), 오류면 -1.
  int read(uint8_t * buffer, std::size_t length, int timeout_ms);

  // Writes the whole buffer. Returns false on error.
  // 한글: 버퍼 전체를 쓴다(부분 쓰기는 반복). 오류면 false.
  bool write(const uint8_t * data, std::size_t length);

  const std::string & last_error() const {return last_error_;}

private:
  int fd_{-1};
  std::string last_error_;
};

}  // namespace jetrover_base
