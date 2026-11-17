/* Temporary local receiver: emit each PCM datagram as one hexadecimal line.
 * 한글: 임시 로컬 수신기이며 각 PCM 데이터그램을 한 줄의 16진수로 출력한다. */
#include <sys/socket.h>
#include <sys/un.h>
#include <sys/stat.h>
#include <unistd.h>
#include <stdlib.h>
#include <stdint.h>
#include <signal.h>
#include <errno.h>
#include <fcntl.h>
#include <sys/syscall.h>

static void cleanup(int signal_number) {
    (void)signal_number;
    unlink("/tmp/r818-doa.sock");
    _exit(0);
}

void _start(void) {
    struct sockaddr_un addr = {.sun_family = AF_UNIX, .sun_path = "/tmp/r818-doa.sock"};
    unsigned char packet[4104];
    char line[8209];
    const char hex[] = "0123456789abcdef";
    umask(077);
    int fd = socket(AF_UNIX, SOCK_DGRAM | SOCK_CLOEXEC, 0);
    if (fd < 0) _exit(1);
    if (bind(fd, (const struct sockaddr *)&addr, sizeof(addr)) != 0) {
        struct stat info;
        /* Recover only an owned dead socket, never an active receiver or other file.
         * 한글: 소유자가 같고 사용 중이 아닌 소켓만 복구하며 다른 파일은 건드리지 않는다. */
        if (errno != EADDRINUSE || connect(fd, (const struct sockaddr *)&addr, sizeof(addr)) == 0 ||
            errno != ECONNREFUSED || syscall(SYS_newfstatat, AT_FDCWD, addr.sun_path, &info, AT_SYMLINK_NOFOLLOW) != 0 ||
            !S_ISSOCK(info.st_mode) || info.st_uid != geteuid() || unlink(addr.sun_path) != 0 ||
            bind(fd, (const struct sockaddr *)&addr, sizeof(addr)) != 0) _exit(1);
    }
    signal(SIGPIPE, SIG_IGN);
    signal(SIGTERM, cleanup);
    signal(SIGINT, cleanup);
    for (int packet_count = 0; packet_count < 200; ++packet_count) {
        long n = recv(fd, packet, sizeof(packet), 0);
        if (n < 8) break;
        for (long i = 0; i < n; ++i) {
            line[2 * i] = hex[packet[i] >> 4];
            line[2 * i + 1] = hex[packet[i] & 15];
        }
        line[2 * n] = '\n';
        long bytes = n * 2 + 1, off = 0;
        while (off < bytes) {
            long count = write(1, line + off, bytes - off);
            if (count <= 0) { unlink(addr.sun_path); _exit(2); }
            off += count;
        }
    }
    unlink(addr.sun_path);
    _exit(0);
}
