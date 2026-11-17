/* Nonblocking, best-effort copy of interleaved 8-channel PCM via local datagrams.
 * 한글: 8채널 인터리브 PCM을 로컬 데이터그램으로 비차단 복사한다. */
#include <stdint.h>
#include <sys/socket.h>
#include <sys/un.h>
#include <stddef.h>
#include <string.h>

typedef struct _snd_pcm snd_pcm_t;
typedef unsigned long frames_t;
typedef long sframes_t;
typedef struct { void *addr; unsigned int first, step; } area_t;
extern void *compat_dlsym(void *, const char *);
__asm__(".symver compat_dlsym,dlsym@GLIBC_2.17");
static snd_pcm_t *capture;
static const area_t *latest;
static int sock = -1;
static uint32_t sequence;
static int same(const char *a, const char *b) {
    if (!a || !b) return 0;
    while (*a && *a == *b) { ++a; ++b; }
    return *a == *b;
}
int snd_pcm_open(snd_pcm_t **pcm, const char *name, int stream, int mode) {
    typedef int (*fn)(snd_pcm_t **, const char *, int, int);
    fn f = (fn)compat_dlsym((void *)-1, "snd_pcm_open");
    if (!f) return -1;
    int rc = f(pcm, name, stream, mode);
    if (rc == 0 && stream == 1 && (same(name, "hw:sndac10710036") || same(name, "hw:1,0")))
        capture = *pcm;
    return rc;
}
int snd_pcm_mmap_begin(snd_pcm_t *pcm, const area_t **areas, frames_t *offset, frames_t *frames) {
    typedef int (*fn)(snd_pcm_t *, const area_t **, frames_t *, frames_t *);
    fn f = (fn)compat_dlsym((void *)-1, "snd_pcm_mmap_begin");
    if (!f) return -1;
    int rc = f(pcm, areas, offset, frames);
    if (rc == 0 && pcm == capture) latest = *areas;
    return rc;
}
sframes_t snd_pcm_mmap_commit(snd_pcm_t *pcm, frames_t offset, frames_t frames) {
    typedef sframes_t (*fn)(snd_pcm_t *, frames_t, frames_t);
    fn f = (fn)compat_dlsym((void *)-1, "snd_pcm_mmap_commit");
    if (!f) return -1;
    if (pcm == capture && latest && frames && latest[0].addr &&
        latest[0].first == 0 && latest[0].step == 128 &&
        latest[1].addr == latest[0].addr && latest[1].first == 16 && latest[1].step == 128) {
        if (sock < 0) sock = socket(AF_UNIX, SOCK_DGRAM | SOCK_NONBLOCK | SOCK_CLOEXEC, 0);
        if (sock >= 0) {
            struct sockaddr_un addr = {.sun_family = AF_UNIX, .sun_path = "/tmp/r818-doa.sock"};
            const unsigned char *p = (const unsigned char *)latest[0].addr + offset * 16;
            frames_t remaining = frames;
            while (remaining) {
                unsigned int n = remaining > 256 ? 256 : (unsigned int)remaining;
                struct { uint32_t seq, count; unsigned char pcm[4096]; } packet;
                packet.seq = sequence++;
                packet.count = n;
                memcpy(packet.pcm, p, n * 16);
                /* Missing/slow receivers drop packets instead of blocking capture.
                 * 한글: 수신기가 없거나 느리면 캡처를 막지 않고 패킷을 버린다. */
                sendto(sock, &packet, 8 + n * 16, MSG_DONTWAIT | MSG_NOSIGNAL,
                       (const struct sockaddr *)&addr, sizeof(addr));
                p += n * 16;
                remaining -= n;
            }
        }
    }
    return f(pcm, offset, frames);
}
/* Forget the handle on close so a reused ALSA pointer cannot be mirrored.
 * 한글: ALSA 포인터가 재사용될 때 잘못 복사하지 않도록 종료 시 추적을 해제한다. */
int snd_pcm_close(snd_pcm_t *pcm) {
    typedef int (*fn)(snd_pcm_t *);
    fn f = (fn)compat_dlsym((void *)-1, "snd_pcm_close");
    if (!f) return -1;
    if (pcm == capture) { capture = 0; latest = 0; }
    return f(pcm);
}
