"""Install the verified optional source-reset module and scoped phone routes."""
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

def cli(command):
    return subprocess.check_output(['asterisk','-rx',command],text=True,timeout=8)

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def atomic(path, content, mode=None, uid=None, gid=None):
    if path.exists():
        stat=path.stat();mode=stat.st_mode & 0o777;uid=stat.st_uid;gid=stat.st_gid
    fd,name=tempfile.mkstemp(prefix='.'+path.name+'.',dir=path.parent)
    try:
        with os.fdopen(fd,'wb') as f:
            f.write(content);f.flush();os.fsync(f.fileno())
            os.fchmod(f.fileno(),mode);os.fchown(f.fileno(),uid,gid)
        os.replace(name,path)
        parent=os.open(path.parent,os.O_DIRECTORY)
        try: os.fsync(parent)
        finally: os.close(parent)
    finally:
        if os.path.exists(name): os.unlink(name)

assert '0 active channels' in cli('core show channels count')
assert digest(Path('/usr/sbin/asterisk'))=='213ec3c383725bf0762e15fcd795da6b28f8520b03109d12501f8d0e6cba57f6'
source=Path('/home/gateway/asterisk-host-framing-20261114/built/app_rtp_source_reset.so')
assert digest(source)=='a5114ee64b48cdf08ac51d2013dca33a676a13d4084da736266f1a095a6759ba'
target=Path('/usr/lib/x86_64-linux-gnu/asterisk/modules/app_rtp_source_reset.so')
assert not target.exists()
paths=[Path('/etc/asterisk/extensions_direct_ip_phone.conf'),Path('/etc/asterisk/extensions_local.conf')]
original={p:p.read_bytes() for p in paths}
texts={p:original[p].decode() for p in paths}
assert all('RtpSourceReset' not in value for value in texts.values())
text,count=re.subn(r'^(exten => [^\n]+,1,)Dial\(Mobile/home-iphone/\$\{EXTEN\},60\)$',
                  r'\1RtpSourceReset()\n same => n,Dial(Mobile/home-iphone/${EXTEN},60)',texts[paths[0]],flags=re.M)
assert count==4
texts[paths[0]]=text+'\n; Debian/Ubuntu PLC sequence reset workaround, scoped to SIP 1002.\n[direct-phone-rtp-source-reset]\nexten => s,1,RtpSourceReset()\n same => n,Return()\n'
count=0
for p in paths:
    count+=texts[p].count('Dial(PJSIP/1002,25)')
    texts[p]=texts[p].replace('Dial(PJSIP/1002,25)','Dial(PJSIP/1002,25,b(direct-phone-rtp-source-reset^s^1))')
assert count==3
backup=Path('/var/backups')/datetime.datetime.now().strftime('asterisk-rtp-source-reset-%Y%m%d-%H%M%S')
backup.mkdir(mode=0o700)
for p in paths: shutil.copy2(p,backup/p.name)
pid_before=subprocess.check_output(['pidof','asterisk'],text=True).strip()
try:
    atomic(target,source.read_bytes(),0o644,0,0)
    cli('module load app_rtp_source_reset.so')
    assert 'RtpSourceReset()' in cli('core show application RtpSourceReset')
    for p in paths: atomic(p,texts[p].encode())
    cli('dialplan reload')
    out=cli('dialplan show from-direct-ip-phone')
    assert out.count('RtpSourceReset()')==4
    assert 'RtpSourceReset()' in cli('dialplan show direct-phone-rtp-source-reset')
    assert 'b(direct-phone-rtp-source-reset^s^1)' in cli('dialplan show from-home-mobile')
    assert subprocess.check_output(['pidof','asterisk'],text=True).strip()==pid_before
except Exception:
    for p in paths: atomic(p,original[p])
    cli('dialplan reload')
    cli('module unload app_rtp_source_reset.so')
    raise
record=dict(backup=str(backup),module_sha256=digest(target),pid=pid_before,
            files={str(p):digest(p) for p in paths},outgoing_patterns=4,incoming_routes=3,
            status=cli('mobile show devices'),channels=cli('core show channels count'))
(backup/'deployment.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps(record,indent=2))
