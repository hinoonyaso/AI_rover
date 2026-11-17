"""Validate the dashboard's direct LAN HTTPS boundary.

한글: 대시보드의 LAN 직접 HTTPS 접속 경계를 검증한다.
"""
import ipaddress
import os


def request_allowed(request):
    """Permit configured local hosts or a specific LAN over HTTPS.

    한글: 지정된 로컬 주소 또는 특정 LAN의 HTTPS 연결만 허용한다.
    """
    host = request.headers.get('host', '').lower()
    try:
        peer = ipaddress.ip_address(request.client.host)
        address = os.environ.get('JETINSPECT_LAN_IP')
        cidr = os.environ.get('JETINSPECT_LAN_CIDR')
        if not address and not cidr:
            return (peer.is_loopback and request.url.scheme == 'http' and
                    host in ('localhost:8765', '127.0.0.1:8765'))
        lan_ip = ipaddress.ip_address(address)
        network = ipaddress.ip_network(cidr, strict=True)
        if (lan_ip.version != 4 or not lan_ip.is_private or lan_ip not in network or
                network.prefixlen < 16 or request.url.scheme != 'https'):
            return False
        return ((peer.is_loopback or (peer.version == 4 and peer in network)) and
                host in (f'{lan_ip}:8765', '127.0.0.1:8765', 'localhost:8765'))
    except (AttributeError, TypeError, ValueError):
        return False


def same_origin(request):
    """Require the browser's origin to match its validated request URL.

    한글: 브라우저 출처가 검증된 요청 주소와 같은지 확인한다.
    """
    return request.headers.get('origin', '').lower() == f"{request.url.scheme}://{request.headers.get('host', '').lower()}"
