"""Check non-destructive stale socket recovery. / 오래된 소켓의 비파괴 복구를 검사한다."""
from pathlib import Path
import os
import socket
import tempfile
import unittest
from unittest.mock import patch

import prepare_mysql_socket


class SocketRecoveryTests(unittest.TestCase):
    def test_old_lock_is_preserved(self):
        with tempfile.TemporaryDirectory(dir='/tmp') as tmp, patch.object(Path, 'home', return_value=Path(tmp)):
            directory = Path(tmp) / '.local/share/jetinspect-ops/mysql-run'
            directory.mkdir(parents=True)
            (directory / 'mysql.sock.lock').write_text('99999999')
            (directory / 'mysql.pid').write_text('99999999')
            prepare_mysql_socket.main()
            backups = list(directory.glob('stale-*'))
            self.assertEqual(len(backups), 1)
            self.assertEqual((backups[0] / 'mysql.sock.lock').read_text(), '99999999')
            self.assertFalse((directory / 'mysql.sock.lock').exists())

    def test_live_socket_is_not_moved(self):
        with tempfile.TemporaryDirectory(dir='/tmp') as tmp, patch.object(Path, 'home', return_value=Path(tmp)):
            directory = Path(tmp) / '.local/share/jetinspect-ops/mysql-run'
            directory.mkdir(parents=True)
            (directory / 'mysql.sock.lock').write_text(str(os.getpid()))
            server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            try:
                server.bind(str(directory / 'mysql.sock'))
                server.listen(1)
                with self.assertRaises(RuntimeError):
                    prepare_mysql_socket.main()
                self.assertTrue((directory / 'mysql.sock.lock').exists())
            finally:
                server.close()


if __name__ == '__main__':
    unittest.main()
