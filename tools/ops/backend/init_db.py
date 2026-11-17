"""Create the local database and non-destructive initial tables.

한글: 로컬 DB 및 비파괴 방식의 초기 테이블을 생성한다.
"""
from pathlib import Path
import pymysql


def main():
    """Initialize only missing schema objects. / 존재하지 않는 스키마만 초기화한다."""
    socket = Path.home() / '.local/share/jetinspect-ops/mysql-run/mysql.sock'
    con = pymysql.connect(user='root', unix_socket=str(socket), autocommit=True, connect_timeout=5)
    with con:
        with con.cursor() as cur:
            cur.execute('CREATE DATABASE IF NOT EXISTS jetinspect CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci')
            cur.execute('USE jetinspect')
            cur.execute('''CREATE TABLE IF NOT EXISTS system_metrics (
                id BIGINT AUTO_INCREMENT PRIMARY KEY, recorded_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                cpu_percent FLOAT NOT NULL, memory_percent FLOAT NOT NULL,
                disk_percent FLOAT NOT NULL, temperature_c FLOAT NULL)''')
            cur.execute('''CREATE TABLE IF NOT EXISTS robot_events (
                id BIGINT AUTO_INCREMENT PRIMARY KEY, recorded_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                severity VARCHAR(16) NOT NULL, source VARCHAR(64) NOT NULL, message TEXT NOT NULL)''')
    print('MySQL schema ready')


if __name__ == '__main__':
    main()
