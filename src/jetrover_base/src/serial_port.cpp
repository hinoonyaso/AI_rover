// 한글: 시리얼 포트 구현(termios + poll).
#include "jetrover_base/serial_port.hpp"

#include <fcntl.h>
#include <poll.h>
#include <termios.h>
#include <unistd.h>

#include <cerrno>
#include <cstring>

namespace jetrover_base
{

namespace
{

// 한글: 숫자 baudrate를 termios 상수로 변환한다. 지원하지 않는 값이면 B0(open이 거부).
speed_t to_speed(int baudrate)
{
  switch (baudrate) {
    case 9600: return B9600;
    case 19200: return B19200;
    case 38400: return B38400;
    case 57600: return B57600;
    case 115200: return B115200;
    case 230400: return B230400;
    case 460800: return B460800;
    case 500000: return B500000;
    case 921600: return B921600;
    case 1000000: return B1000000;
    case 2000000: return B2000000;
    default: return B0;
  }
}

}  // namespace

SerialPort::~SerialPort()
{
  close();
}

bool SerialPort::open(const std::string & path, int baudrate)
{
  close();

  const speed_t speed = to_speed(baudrate);
  if (speed == B0) {
    last_error_ = "unsupported baudrate: " + std::to_string(baudrate);
    return false;
  }

  // 한글: O_NONBLOCK으로 열고 read는 poll로 기다린다(블로킹 read로 노드가 멈추는 것 방지). O_NOCTTY로 제어 터미널이 되지 않게 한다.
  fd_ = ::open(path.c_str(), O_RDWR | O_NOCTTY | O_NONBLOCK);
  if (fd_ < 0) {
    last_error_ = "open " + path + ": " + std::strerror(errno);
    return false;
  }

  termios tty{};
  if (tcgetattr(fd_, &tty) != 0) {
    last_error_ = std::string("tcgetattr: ") + std::strerror(errno);
    close();
    return false;
  }

  // 한글: raw 모드(문자 변환/에코 없음), 8N1, CRTSCTS(하드웨어 흐름 제어) 끔. VMIN=VTIME=0은 poll이 대기를 맡기 때문.
  cfmakeraw(&tty);
  cfsetispeed(&tty, speed);
  cfsetospeed(&tty, speed);
  tty.c_cflag |= (CLOCAL | CREAD);
  tty.c_cflag &= ~(CSTOPB | CRTSCTS);
  tty.c_cc[VMIN] = 0;
  tty.c_cc[VTIME] = 0;

  if (tcsetattr(fd_, TCSANOW, &tty) != 0) {
    last_error_ = std::string("tcsetattr: ") + std::strerror(errno);
    close();
    return false;
  }

  // 한글: 열자마자 이전 잔여 데이터를 버린다.
  tcflush(fd_, TCIOFLUSH);
  return true;
}

void SerialPort::close()
{
  if (fd_ >= 0) {
    ::close(fd_);
    fd_ = -1;
  }
}

int SerialPort::read(uint8_t * buffer, std::size_t length, int timeout_ms)
{
  if (fd_ < 0) {
    return -1;
  }

  pollfd pfd{fd_, POLLIN, 0};
  const int ready = poll(&pfd, 1, timeout_ms);
  if (ready < 0) {
    if (errno == EINTR) {
      return 0;
    }
    last_error_ = std::string("poll: ") + std::strerror(errno);
    return -1;
  }
  if (ready == 0) {
    return 0;
  }
  // 한글: USB-UART가 뽑히면 POLLHUP/POLLERR이 온다 → 호출자가 재연결하도록 -1을 돌려준다.
  if (pfd.revents & (POLLERR | POLLHUP | POLLNVAL)) {
    last_error_ = "serial device error or disconnected";
    return -1;
  }

  const ssize_t n = ::read(fd_, buffer, length);
  if (n < 0) {
    if (errno == EAGAIN || errno == EINTR) {
      return 0;
    }
    last_error_ = std::string("read: ") + std::strerror(errno);
    return -1;
  }
  return static_cast<int>(n);
}

bool SerialPort::write(const uint8_t * data, std::size_t length)
{
  if (fd_ < 0) {
    return false;
  }

  std::size_t written = 0;
  while (written < length) {
    const ssize_t n = ::write(fd_, data + written, length - written);
    if (n < 0) {
      if (errno == EINTR) {
        continue;
      }
      // 한글: TX 버퍼가 가득 찬 경우: 최대 10ms 기다렸다가 이어서 쓴다.
      if (errno == EAGAIN) {
        pollfd pfd{fd_, POLLOUT, 0};
        poll(&pfd, 1, 10);
        continue;
      }
      last_error_ = std::string("write: ") + std::strerror(errno);
      return false;
    }
    written += static_cast<std::size_t>(n);
  }
  return true;
}

}  // namespace jetrover_base
