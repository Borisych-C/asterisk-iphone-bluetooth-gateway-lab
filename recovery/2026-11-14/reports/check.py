"""Bounded passive call check. Retains levels/counts, never records audio or numbers."""
import audioop
import collections
import ctypes
import csv
import json
import os
from pathlib import Path
import re
import selectors
import signal
import socket
import struct
import subprocess
import time

def cli(command):
    return subprocess.check_output(['asterisk', '-rx', command], text=True, timeout=6)

def note(event, **values):
    print(json.dumps(dict(t=round(time.monotonic()-start, 3), event=event, **values)), flush=True)

def levels(key, pcm):
    if not pcm or len(pcm) % 2:
        return 0
    rms = audioop.rms(pcm, 2)
    counts[key]['packets'] += 1
    counts[key]['bytes'] += len(pcm)
    counts[key]['max_rms'] = max(counts[key]['max_rms'], rms)
    if rms > 100:
        counts[key]['nonquiet'] += 1
    lengths[key][len(pcm)] += 1
    seconds[int(time.monotonic()-start)][key] += 1
    return rms

def lan_packet(frame):
    if len(frame) < 42 or frame[12:14] != b'\x08\x00' or frame[23] != 17:
        return
    src, dst = frame[26:30], frame[30:34]
    if (src, dst) == (phone, server):
        direction = 'sip_to_asterisk'
    elif (src, dst) == (server, phone):
        direction = 'asterisk_to_sip'
    else:
        return
    offset = 14 + (frame[14] & 15)*4
    sport, dport, size = struct.unpack_from('!HHH', frame, offset)
    data = frame[offset+8:offset+size]
    if sport == 5060 or dport == 5060:
        first = data.split(b'\r\n', 1)[0]
        if b'\r\n\r\n' in data:
            sdp = data.split(b'\r\n\r\n', 1)[1]
            media = [line.decode('ascii', 'replace') for line in sdp.split(b'\r\n')
                     if line.startswith((b'm=audio ', b'c=IN ', b'a=rtpmap:', b'a=sendrecv', b'a=sendonly', b'a=recvonly', b'a=inactive'))]
            if media:
                note('sdp', direction=direction, lines=media)
        if first.startswith(b'SIP/2.0 '):
            code = first.split()[1].decode('ascii', 'replace')
            # REGISTER/OPTIONS replies are not call transitions.
            cseq = re.search(rb'\r\nCSeq: *\d+ +(INVITE|BYE|CANCEL)\r\n', data, re.I)
            if cseq:
                note('sip_status', direction=direction, code=code, method=cseq[1].decode())
        elif first.startswith((b'INVITE ', b'BYE ', b'CANCEL ', b'ACK ')):
            note('sip_method', direction=direction, method=first.split()[0].decode())
        return
    if not (10000 <= (dport if src == phone else sport) <= 20000):
        return
    if len(data) < 12 or data[0] >> 6 != 2 or data[1] & 127 not in (0, 8):
        return
    seq, timestamp, ssrc = struct.unpack_from('!HII', data, 2)
    stream = (sport, dport, data[1] & 127, ssrc)
    previous = stream_last.get(direction)
    if previous is None or previous[0] != stream:
        note('rtp_stream', direction=direction, source_port=sport, destination_port=dport,
             payload_type=data[1] & 127, ssrc=ssrc, seq=seq, timestamp=timestamp)
    elif ((seq-previous[1]) & 65535) != 1:
        note('rtp_sequence_gap', direction=direction, previous=previous[1], seq=seq)
    stream_last[direction] = (stream, seq)
    n = 12 + (data[0] & 15)*4
    if data[0] & 16:
        if n+4 > len(data):
            return
        n += 4 + 4*struct.unpack_from('!H', data, n+2)[0]
    payload = data[n:]
    if data[0] & 32 and payload and 0 < payload[-1] <= len(payload):
        payload = payload[:-payload[-1]]
    pcm = (audioop.ulaw2lin if data[1] & 127 == 0 else audioop.alaw2lin)(payload, 2)
    levels(direction, pcm)
    if src == phone:
        # One second rolling search window, discarded on exit.
        sip_pcm.extend(pcm)
        if len(sip_pcm) > 16000:
            del sip_pcm[:-16000]

def bt_packet(packet):
    global sco_serial
    if len(packet) < 6:
        return
    op, index, size = struct.unpack_from('<HHH', packet)
    if index != adapter or len(packet) < 6+size:
        return
    body = packet[6:6+size]
    if op == 3 and len(body) >= 6:
        if body[0] == 0x2c and body[2] == 0 and len(body) >= 19:
            handle = struct.unpack_from('<H', body, 3)[0]
            sco_serial += 1
            connections[handle] = sco_serial
            rx, tx = struct.unpack_from('<HH', body, 14)
            note('sco_open', serial=sco_serial, handle=handle, air_rx=rx, air_tx=tx,
                 interval_slots=body[12], air_mode=body[18])
        elif body[0] == 5:
            handle = struct.unpack_from('<H', body, 3)[0]
            if handle in connections:
                note('sco_close', serial=connections[handle], reason=body[5])
    elif op in (4, 5):
        for item in re.findall(rb'(?:\+CIEV: *\d+, *\d+|\+VGM: *\d+|\+VGS: *\d+|\+BSIR: *\d+|\bATA\r|ATD[^\r]*\r|AT\+CHUP\r)', body):
            # Deliberately suppress dialed numbers.
            text = 'ATD <number omitted>' if item.startswith(b'ATD') else item.decode('ascii', 'replace').strip()
            note('hfp', direction='host_tx' if op == 4 else 'host_rx', signal=text)
    elif op in (6, 7) and len(body) >= 3:
        raw_handle = struct.unpack_from('<H', body)[0]
        serial = connections.get(raw_handle & 4095, 0)
        key = ('host_to_adapter' if op == 6 else 'adapter_to_host') + '_' + str(serial)
        pcm = body[3:3+body[2]]
        rms = levels(key, pcm)
        if raw_handle & 0x3000:
            counts[key]['flagged'] += 1
        if op == 6 and rms > 100:
            counts[key]['pcm_exact_match' if pcm in sip_pcm else 'pcm_no_match'] += 1

def stop(signum, frame):
    global done
    done = True

phone, server = map(socket.inet_aton, ('10.77.0.2', '10.77.0.1'))
adapter = int(next(p.name[3:] for p in Path('/sys/class/bluetooth').glob('hci*') if re.fullmatch(r'hci\d+', p.name)))
assert 'Yes       Free' in cli('mobile show devices')
assert 'Avail' in cli('pjsip show aor 1002')
counts = collections.defaultdict(collections.Counter)
lengths = collections.defaultdict(collections.Counter)
seconds = collections.defaultdict(collections.Counter)
connections, sip_pcm, sco_serial = {}, bytearray(), 0
stream_last = {}
done = False
signal.signal(signal.SIGTERM, stop)
signal.signal(signal.SIGINT, stop)
start = time.monotonic()
cdr = Path('/var/log/asterisk/cdr-csv/Master.csv')
initial = cdr.stat().st_size
next_cdr = start
with socket.socket(socket.AF_PACKET, socket.SOCK_RAW, socket.htons(3)) as lan, socket.socket(socket.AF_BLUETOOTH, socket.SOCK_RAW, socket.BTPROTO_HCI) as bt:
    lan.bind(('enp3s0', 0))
    lib = ctypes.CDLL(None, use_errno=True)
    address = struct.pack('=HHH', socket.AF_BLUETOOTH, 65535, 2)
    if lib.bind(bt.fileno(), address, len(address)):
        raise OSError(ctypes.get_errno(), 'HCI monitor bind')
    with selectors.DefaultSelector() as watch:
        for sock, handler in ((lan, lan_packet), (bt, bt_packet)):
            sock.setblocking(False)
            watch.register(sock, selectors.EVENT_READ, handler)
        note('ready', adapter=adapter, deadline_seconds=180)
        while not done and time.monotonic()-start < 180:
            for item, _ in watch.select(.2):
                for _ in range(32):
                    try:
                        item.data(item.fileobj.recv(4096))
                    except BlockingIOError:
                        break
            if time.monotonic() >= next_cdr:
                next_cdr = time.monotonic()+.5
                if cdr.stat().st_size > initial:
                    with cdr.open() as f:
                        f.seek(initial)
                        for row in csv.reader(f):
                            if len(row) > 14 and ('Mobile/home-iphone' in row[5] or 'Mobile/home-iphone' in row[6]):
                                note('call_end', direction='outgoing' if row[3]=='from-direct-ip-phone' else 'incoming',
                                     start=row[9], answered=row[10], seconds=row[13], disposition=row[14])
                                done = True
                    initial = cdr.stat().st_size
for key in sorted(counts):
    note('totals', stream=key, counts=dict(counts[key]), sizes=dict(lengths[key]))
for second, values in sorted(seconds.items()):
    note('rates', second=second, packets=dict(values))
note('finished')
