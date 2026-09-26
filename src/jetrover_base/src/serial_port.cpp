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
