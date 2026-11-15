"""Temporary, bounded counters around module/socket/USB while check.py runs."""
import collections
import hashlib
import json
import os
from pathlib import Path
import re
import runpy
import selectors
import subprocess
import threading
import time

trace = Path('/sys/kernel/tracing')
module = Path('/usr/lib/x86_64-linux-gnu/asterisk/modules/chan_mobile.so')
assert hashlib.sha256(module.read_bytes()).hexdigest() == '9aa871cd579d2547e1ba5633218fab50830bc3ada777b9b5eec3cdd3f105632c'
assert subprocess.check_output(['uname','-r'],text=True).strip() == '7.0.0-43-generic'
group = 'mobile_phase_' + str(os.getpid())
instance = trace/'instances'/group
device = Path('/sys/bus/usb/devices/1-9')
bus, dev = (int((device/x).read_text()) for x in ('busnum','devnum'))
events = {
    'mobile': ('uprobe_events', f'p:{group}/mobile {module}:0x6b50 type=+0(%si):u32 bytes=+32(%si):u32', ''),
    'send': ('kprobe_events', f'r:{group}/send bluetooth:sco_sock_sendmsg result=$retval:s64', ''),
    'queue': ('kprobe_events', f'p:{group}/queue bluetooth:hci_send_sco adapter=+112(+3664($arg1)):u16 queued=+2440($arg1):u32 sent=+2420($arg1):u32 credits=+1184(+3664($arg1)):u32', 'adapter == 0'),
    'usb': ('kprobe_events', f'p:{group}/usb btusb:btusb_isoc_tx_complete bus=+16(+80(+64($arg1))):u32 dev=+0(+64($arg1)):u32 status=+88($arg1):s32 length=+136($arg1):u32 actual=+140($arg1):u32 errors=+172($arg1):s32 p0=+204($arg1):s32 p1=+220($arg1):s32 p2=+236($arg1):s32 p3=+252($arg1):s32 packets=+164($arg1):u32', f'bus == {bus} && dev == {dev}'),
}
created = []
totals = collections.defaultdict(collections.Counter)
stopped = threading.Event()
reader_errors = []
started = time.monotonic()

def command(file, line):
    fd = os.open(trace/file, os.O_WRONLY|os.O_APPEND)
    try:
        os.write(fd, (line+'\n').encode())
    finally:
        os.close(fd)

def read_trace():
    fd = os.open(instance/'trace_pipe', os.O_RDONLY|os.O_NONBLOCK)
    pending = b''
    try:
        with selectors.DefaultSelector() as watch:
            watch.register(fd,selectors.EVENT_READ)
            while not stopped.is_set():
                if not watch.select(.2):
                    continue
                try:
                    pending += os.read(fd,65536)
                except BlockingIOError:
                    continue
                lines = pending.split(b'\n'); pending = lines.pop()
                for line in lines:
                    match = re.search(rb'(\d+\.\d+): (mobile|send|queue|usb): (.*)',line)
                    if not match:
                        if b'LOST' in line:
                            reader_errors.append('lost trace events')
                        continue
                    timestamp, event, body = match.groups()
                    sec = int(float(timestamp)-started)
                    fields = dict((k.decode(),int(v)) for k,v in re.findall(rb'(type|bytes|result|queued|sent|credits|status|length|actual|errors|p[0-3]|packets)=(-?\d+)',body))
                    name = event.decode()
                    if name == 'mobile':
                        key = f'mobile_type_{fields.get("type")}_bytes_{fields.get("bytes")}'
                    elif name == 'send':
                        key = f'send_result_{fields.get("result")}'
                    elif name == 'usb':
                        key = 'usb_'+str(tuple(fields.get(k) for k in ('status','length','actual','errors','p0','p1','p2','packets')))
                    else:
                        key = 'enqueue'
                        totals[sec]['max_queue'] = max(totals[sec]['max_queue'],fields.get('queued',0))
                    totals[sec][key] += 1
    except Exception as e:
        reader_errors.append(type(e).__name__)
    finally:
        os.close(fd)

worker = None
try:
    for name,(file,line,filter_) in events.items():
        command(file,line); created.append((file,name))
    instance.mkdir()
    (instance/'trace_clock').write_text('mono')
    (instance/'buffer_size_kb').write_text('256')
    for name,(_,_,filter_) in events.items():
        p = instance/'events'/group/name
        if filter_: (p/'filter').write_text(filter_)
        (p/'enable').write_text('1')
    worker = threading.Thread(target=read_trace)
    worker.start()
    runpy.run_path('/home/gateway/asterisk-host-framing-20261114/check.py',run_name='__main__')
finally:
    if instance.exists():
        (instance/'events'/group/'enable').write_text('0')
    stopped.set()
    if worker: worker.join(2)
    if instance.exists(): instance.rmdir()
    for file,name in reversed(created): command(file,'-:'+group+'/'+name)
    for sec, counts in sorted(totals.items()):
        print(json.dumps(dict(event='kernel_rates',second=sec,counts=dict(counts))),flush=True)
    print(json.dumps(dict(event='trace_finished',errors=reader_errors)),flush=True)
