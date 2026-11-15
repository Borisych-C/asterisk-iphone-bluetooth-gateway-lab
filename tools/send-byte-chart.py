"""Explicit diagnostic: seven real messages to the local T780P, bytes 32..255.
Run on .128. No retransmissions or persistent configuration changes.
"""
import json
import secrets
import socket
import time

for part, start in enumerate(range(32, 256, 32), 1):
    body = f'Bytes {part}/7: {start}-{start+31}\n'.encode('ascii')
    for row in range(start, start + 32, 8):
        body += f'{row:03d}:['.encode('ascii') + bytes(range(row, row + 8)) + b']\n'
    assert len(body) <= 200
    call_id = 'byte-chart-' + secrets.token_hex(12) + '@10.77.0.1'
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.bind(('10.77.0.1', 0))
        port = sock.getsockname()[1]
        header = (
            'MESSAGE sip:1002@10.77.0.2:5060 SIP/2.0\r\n'
            f'Via: SIP/2.0/UDP 10.77.0.1:{port};branch=z9hG4bK{secrets.token_hex(10)};rport\r\n'
            'Max-Forwards: 10\r\n'
            f'From: "Byte chart" <sip:asterisk@10.77.0.1>;tag={secrets.token_hex(6)}\r\n'
            'To: <sip:1002@10.77.0.2>\r\n'
            f'Call-ID: {call_id}\r\nCSeq: 1 MESSAGE\r\n'
            'Content-Type: text/plain; charset=ISO-8859-1\r\n'
            f'Content-Length: {len(body)}\r\n\r\n'
        )
        sock.sendto(header.encode('ascii') + body, ('10.77.0.2', 5060))
        deadline = time.monotonic() + 6
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError('No final response; no retry performed')
            sock.settimeout(remaining)
            packet, peer = sock.recvfrom(65535)
            if peer != ('10.77.0.2', 5060) or call_id.encode() not in packet:
                continue
            status = packet.split(b'\r\n', 1)[0].decode('ascii')
            if int(status.split()[1]) < 200:
                continue
            print(json.dumps({'part': part, 'range': [start, start + 31],
                              'body_hex': body.hex(), 'status': status}), flush=True)
            if not status.startswith('SIP/2.0 200 '):
                raise RuntimeError(status)
            break
    if part < 7:
        time.sleep(1)
