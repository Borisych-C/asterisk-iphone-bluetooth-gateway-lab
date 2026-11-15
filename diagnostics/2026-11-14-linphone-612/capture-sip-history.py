#!/usr/bin/env python3
"""Run via SSH on .128 as root; bounded, temporary Asterisk SIP observation."""
import json
import os
import pathlib
import re
import signal
import subprocess
import sys
import time


def cli(command):
    return subprocess.run(
        ['/usr/sbin/asterisk', '-rx', command],
        capture_output=True, text=True, timeout=8, check=True,
    ).stdout


def count(state):
    match = re.search(r'(\d+) calls processed', state)
    return int(match[1]) if match else -1


def scrub(text):
    text = re.sub(r'\x1b\[[0-9;]*m', '', text)
    text = re.sub(r'(?im)^(a=crypto:\d+ \S+) .*$', r'\1 [KEY REMOVED]', text)
    text = re.sub(r'(?im)^a=ice-pwd:.*$', 'a=ice-pwd:[REMOVED]', text)
    return '\n'.join(line for line in text.splitlines() if not re.match(
        r'(?i)\s*(proxy-authorization|authorization|www-authenticate|'
        r'proxy-authenticate|authentication-info|proxy-authentication-info):', line
    ))


def stop(*args):
    raise KeyboardInterrupt()


signal.signal(signal.SIGTERM, stop)
os.umask(0o077)
label = sys.argv[1]
assert re.fullmatch(r'[a-z0-9-]+', label)
folder = pathlib.Path('/home/gateway/asterisk-linphone-612-20261114')
folder.mkdir(exist_ok=True, mode=0o700)
initial = count(cli('core show channels'))
stats = []
try:
    print(cli('pjsip set history on'), flush=True)
    print('READY: SIP observation, maximum 180 seconds', flush=True)
    deadline = time.monotonic() + 180
    while time.monotonic() < deadline:
        state = cli('core show channels')
        if count(state) > initial and '0 active channels' in state:
            time.sleep(3)
            break
        if '0 active channels' not in state:
            stats.append({'time': time.strftime('%Y-%m-%dT%H:%M:%S%z'),
                          'stats': cli('pjsip show channelstats')})
        time.sleep(2)
finally:
    print(cli('pjsip set history off'), flush=True)
    table = cli('pjsip show history')
    entries = []
    for line in table.splitlines():
        match = re.match(r'\s*(\d+)\s+', line)
        if match:
            entries.append(scrub(cli('pjsip show history entry ' + match[1])))
    result = {'captured_at': time.strftime('%Y-%m-%dT%H:%M:%S%z'),
              'table': scrub(table), 'entries': entries, 'channelstats': stats}
    path = folder / (label + '-sip-redacted.json')
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2))
    path.chmod(0o600)
    print('SAVED', path, 'entries=' + str(len(entries)), flush=True)
    print(scrub(table), flush=True)
    print(cli('pjsip set history clear'), flush=True)
