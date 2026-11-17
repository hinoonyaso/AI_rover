"""Create a private LAN HTTPS certificate and service configuration.

한글: 사용자 전용 LAN HTTPS 인증서와 서비스 설정을 생성한다.
"""
import argparse
import ipaddress
import os
from pathlib import Path
import subprocess
import tempfile


def main():
    """Create new credentials without replacing existing ones. / 기존 인증서를 덮어쓰지 않고 새 설정을 만든다."""
    parser = argparse.ArgumentParser()
    parser.add_argument('--address', required=True)
    parser.add_argument('--network', required=True)
    args = parser.parse_args()
    address = ipaddress.ip_address(args.address)
    network = ipaddress.ip_network(args.network, strict=True)
    if address.version != 4 or not address.is_private or address not in network or network.prefixlen < 16:
        raise SystemExit('a private IPv4 address and matching /16 or narrower network are required')
    directory = Path.home() / '.local/share/jetinspect-ops/tls'
    directory.mkdir(mode=0o700, parents=True, exist_ok=True)
    key, cert, config = (directory / name for name in ('dashboard.key', 'dashboard.crt', 'lan.env'))
    if any(path.exists() for path in (key, cert, config)):
        raise SystemExit('TLS files already exist; existing files were not modified')
    with tempfile.TemporaryDirectory(dir=directory) as temp:
        t = Path(temp)
        subprocess.run(['openssl', 'req', '-x509', '-newkey', 'rsa:3072', '-sha256', '-noenc',
                        '-days', '825', '-keyout', str(t / 'key'), '-out', str(t / 'cert'),
                        '-subj', '/CN=JetInspect-M',
                        '-addext', f'subjectAltName=IP:{address},IP:127.0.0.1,DNS:localhost',
                        '-addext', 'basicConstraints=critical,CA:FALSE',
                        '-addext', 'keyUsage=critical,digitalSignature,keyEncipherment',
                        '-addext', 'extendedKeyUsage=serverAuth'],
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        os.chmod(t / 'key', 0o600)
        os.chmod(t / 'cert', 0o644)
        (t / 'config').write_text(f'JETINSPECT_LAN_IP={address}\nJETINSPECT_LAN_CIDR={network}\n')
        os.chmod(t / 'config', 0o600)
        for source, target in ((t / 'key', key), (t / 'cert', cert), (t / 'config', config)):
            os.link(source, target)
    print(f'HTTPS address: https://{address}:8765')
    print(f'Public certificate: {cert}')
    subprocess.run(['openssl', 'x509', '-in', str(cert), '-noout', '-fingerprint', '-sha256'], check=True)


if __name__ == '__main__':
    main()
