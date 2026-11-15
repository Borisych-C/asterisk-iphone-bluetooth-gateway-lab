"""Bounded call counters through RTP, channel, translation and mobile write."""
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
group = 'phone_core_' + str(os.getpid())
instance = trace/'instances'/group
binary = Path('/usr/sbin/asterisk')
symbols = {}
for line in subprocess.check_output(['nm','-D',str(binary)],text=True).splitlines():
    fields=line.split()
    if len(fields)==3: symbols[fields[2]]=int(fields[0],16)
events = {}
for name,symbol in [('rtp','ast_rtp_instance_read'),('read','ast_read'),('read_stream','ast_read_stream'),('translate','ast_translate')]:
    events[name] = f'r:{group}/{name} {binary}:0x{symbols[symbol]:x} type=+0($retval):u32 bytes=+32($retval):u32'
events['write'] = f'p:{group}/write {binary}:0x{symbols["ast_write"]:x} channel=%di:x64 type=+0(%si):u32 bytes=+32(%si):u32'
events['write_stream'] = f'p:{group}/write_stream {binary}:0x{symbols["ast_write_stream"]:x} channel=%di:x64 type=+0(%dx):u32 bytes=+32(%dx):u32'
module = Path('/usr/lib/x86_64-linux-gnu/asterisk/modules/chan_mobile.so')
assert hashlib.sha256(module.read_bytes()).hexdigest()=='9aa871cd579d2547e1ba5633218fab50830bc3ada777b9b5eec3cdd3f105632c'
events['mobile'] = f'p:{group}/mobile {module}:0x6b50 type=+0(%si):u32 bytes=+32(%si):u32'
created=[]
counts=collections.defaultdict(collections.Counter)
stopped=threading.Event()
errors=[]
start=time.monotonic()

def command(line):
    fd=os.open(trace/'uprobe_events',os.O_WRONLY|os.O_APPEND)
    try: os.write(fd,(line+'\n').encode())
    finally: os.close(fd)

def reader():
    fd=os.open(instance/'trace_pipe',os.O_RDONLY|os.O_NONBLOCK)
    pending=b''
    try:
        with selectors.DefaultSelector() as watch:
            watch.register(fd,selectors.EVENT_READ)
            while not stopped.is_set():
                if not watch.select(.2): continue
                try: pending+=os.read(fd,65536)
                except BlockingIOError: continue
                lines=pending.split(b'\n');pending=lines.pop()
                for line in lines:
                    match=re.search(rb'(\d+\.\d+): (\w+): (.*)',line)
                    if not match:
                        if b'LOST' in line: errors.append('lost events')
                        continue
                    stamp,name,body=match.groups()
                    fields=re.findall(rb'(channel|type|bytes)=([^ ]+)',body)
                    key=name.decode()+':'+','.join(k.decode()+'='+v.decode() for k,v in fields)
                    counts[int(float(stamp)-start)][key]+=1
    except Exception as e: errors.append(repr(e))
    finally: os.close(fd)

worker=None
try:
    for name,line in events.items(): command(line);created.append(name)
    instance.mkdir()
    (instance/'trace_clock').write_text('mono')
    (instance/'buffer_size_kb').write_text('256')
    (instance/'events'/group/'enable').write_text('1')
    worker=threading.Thread(target=reader);worker.start()
    print(json.dumps(dict(event='core_trace_ready',binary_sha256=hashlib.sha256(binary.read_bytes()).hexdigest())),flush=True)
    runpy.run_path('/home/gateway/asterisk-host-framing-20261114/check.py',run_name='__main__')
finally:
    if instance.exists(): (instance/'events'/group/'enable').write_text('0')
    stopped.set()
    if worker: worker.join(2)
    if instance.exists(): instance.rmdir()
    for name in reversed(created): command('-:'+group+'/'+name)
    for second,values in sorted(counts.items()):
        print(json.dumps(dict(event='core_rates',second=second,counts=dict(values))),flush=True)
    print(json.dumps(dict(event='trace_finished',errors=errors)),flush=True)
