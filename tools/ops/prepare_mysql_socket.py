"""Preserve orphaned MySQL socket files before startup.

한글: MySQL 시작 전 소유자가 없는 소켓 파일을 보존한다.
"""
import os
from pathlib import Path
import socket
import time


def main():
    """Move stale socket artifacts only when no MySQL owner is live.

    한글: 실행 중인 MySQL 소유자가 없을 때만 오래된 소켓 파일을 옮긴다.
    """
    directory = Path.home() / '.local/share/jetinspect-ops/mysql-run'
    sock = directory / 'mysql.sock'
    lock = directory / 'mysql.sock.lock'
    if not lock.exists():
        return
    try:
        pid = int(lock.read_text().strip())
        comm = (Path('/proc') / str(pid) / 'comm').read_text().strip()
        if comm == 'mysqld':
            raise RuntimeError('MySQL lock is owned by a live mysqld')
    except (ValueError, FileNotFoundError, ProcessLookupError):
        pass
    probe = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        probe.settimeout(1)
        if probe.connect_ex(str(sock)) == 0:
            raise RuntimeError('MySQL socket is in use')
    finally:
        probe.close()
    backup = directory / f'stale-{time.time_ns()}'
    backup.mkdir(mode=0o700)
    for name in ('mysql.sock', 'mysql.sock.lock', 'mysql.pid'):
        path = directory / name
        if path.exists() or path.is_socket():
            os.rename(path, backup / name)


if __name__ == '__main__':
    main()
