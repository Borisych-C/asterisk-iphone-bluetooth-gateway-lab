#!/usr/bin/env python3
"""Run as root on .128 with this source directory; no secrets in output."""
import datetime
import grp
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess

os.umask(0o077)
assert os.geteuid() == 0
SOURCE = Path(__file__).resolve().parent
CONF = Path('/etc/asterisk')

def run(args, timeout=20):
    return subprocess.run(args, check=True, capture_output=True, text=True, timeout=timeout).stdout

def cli(cmd):
    return run(['/usr/sbin/asterisk', '-rx', cmd])

assert '0 active channels' in cli('core show channels count'), 'Wait for calls to finish'
assert not (CONF/'pjsip_public.conf').exists(), 'Public config already exists; inspect before updating'
assert not run(['ss', '-H', '-ltn', 'sport = :5062']).strip(), 'TCP 5062 is already in use'
stamp = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
backup = Path('/var/backups/asterisk-public-sip')/stamp
backup.mkdir(parents=True, mode=0o700)
targets = [CONF/'pjsip.conf', CONF/'extensions.conf', CONF/'rtp.conf', CONF/'dnsmgr.conf',
           CONF/'pjsip_public.conf', CONF/'extensions_public.conf',
           Path('/etc/letsencrypt/renewal-hooks/deploy/asterisk-public-cert.sh')]
manifest = {}
for f in targets:
    entry = {'existed': f.exists()}
    if f.exists():
        out = backup/str(f).lstrip('/')
        out.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(f, out)
        st = f.stat()
        entry.update(mode=st.st_mode & 0o777, uid=st.st_uid, gid=st.st_gid,
                     sha256=hashlib.sha256(f.read_bytes()).hexdigest())
    manifest[str(f)] = entry
(backup/'manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
(backup/'ufw-before.txt').write_text(run(['ufw','status','numbered']))
(backup/'asterisk-before.txt').write_text(cli('pjsip show transports')+cli('pjsip show endpoints')+cli('mobile show devices'))
asterisk_gid = grp.getgrnam('asterisk').gr_gid

def atomic_write(dest, text, mode=0o640, gid=asterisk_gid):
    tmp = dest.with_name(dest.name+'.public-sip-new')
    tmp.write_text(text)
    os.chmod(tmp, mode)
    os.chown(tmp, 0, gid)
    os.replace(tmp, dest)

hook = Path('/etc/letsencrypt/renewal-hooks/deploy/asterisk-public-cert.sh')
atomic_write(hook, (SOURCE/'asterisk-public-cert-deploy.sh').read_text(), 0o700, 0)
run(['bash','-n',str(hook)])
run([str(hook),'--no-reload'])
for name in ['pjsip_public.conf','extensions_public.conf']:
    atomic_write(CONF/name, (SOURCE/name).read_text())
for name, include in [('pjsip.conf','pjsip_public.conf'),('extensions.conf','extensions_public.conf')]:
    f=CONF/name
    assert not re.search(r'^#include\s+'+re.escape(include)+r'\s*$', f.read_text(), re.M)
    atomic_write(f, f.read_text().rstrip()+'\n\n#include '+include+'\n')
rtp=(CONF/'rtp.conf').read_text()
assert re.search(r'^rtpstart\s*=\s*10000\s*$',rtp,re.M)
rtp, n = re.subn(r'^rtpend\s*=\s*20000\s*$', 'rtpend=10015', rtp, flags=re.M)
assert n==1
atomic_write(CONF/'rtp.conf',rtp)
dns=(CONF/'dnsmgr.conf').read_text()
assert not re.search(r'^\s*enable\s*=',dns,re.M)
dns,n=re.subn(r'^\[general\]\s*$', '[general]\nenable=yes\nrefreshinterval=300', dns, count=1, flags=re.M)
assert n==1
atomic_write(CONF/'dnsmgr.conf',dns)

for command in ['dnsmgr reload','module reload res_rtp_asterisk.so','module reload res_pjsip.so','dialplan reload']:
    print(command+'\n'+cli(command))
print(json.dumps({'backup':str(backup),'installed':list(manifest),'server_restarted':False}))
print(cli('pjsip show transport transport-tls-public'))
print(cli('pjsip show endpoint public-stationary'))
print(cli('dialplan show from-public-sip'))
