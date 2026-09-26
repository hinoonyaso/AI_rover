#pragma once

#include <cstddef>
#include <cstdint>
#include <string>

namespace jetrover_base
{

// Minimal POSIX termios wrapper: raw 8N1, no flow control.
class SerialPort
{
public:
  SerialPort() = default;
  ~SerialPort();

  SerialPort(const SerialPort &) = delete;
  SerialPort & operator=(const SerialPort &) = delete;

  // Returns false on failure; the reason is available from last_error().
  bool open(const std::string & path, int baudrate);
  void close();
  bool is_open() const {return fd_ >= 0;}
  int fd() const {return fd_;}

  // Waits up to timeout_ms for data. Returns bytes read (0 on timeout), -1 on error.
  int read(uint8_t * buffer, std::size_t length, int timeout_ms);

  // Writes the whole buffer. Returns false on error.
  bool write(const uint8_t * data, std::size_t length);

  const std::string & last_error() const {return last_error_;}

private:
  int fd_{-1};
  std::string last_error_;
};

}  // namespace jetrover_base
