#!/usr/bin/env python3
"""One-time deployment using SSH and Secret Service; never print credentials."""
from pathlib import Path
import json,os,secrets,string,subprocess
os.umask(0o077)
ROOT=Path('/home/gateway/asterisk')
helper=ROOT/'linphone-push/keyring_credentials.py'
keyargs=['--host','home.example.net','--username','1003','--kind','travel-sip']
check=subprocess.run(['/usr/bin/python3',str(helper),'exists',*keyargs],capture_output=True)
assert check.returncode==1,'Travel credential already exists; inspect before repeating deployment'
password=''.join(secrets.choice('abcdefghijkmnpqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ23456789') for _ in range(20))
r=subprocess.run(['/usr/bin/python3',str(helper),'store',*keyargs,'--label','Home SIM: Linphone outgoing via Asterisk'],input=password+'\n',text=True,capture_output=True)
assert r.returncode==0,'Could not store credential in keyring'
sources={p.name:p.read_text() for p in (ROOT/'roaming/config').glob('*.conf')}
script=r'''
from pathlib import Path
import os,grp,datetime,subprocess,shutil,re,json
os.umask(0o077)
def cli(c):return subprocess.run(['/usr/sbin/asterisk','-rx',c],capture_output=True,text=True,timeout=10,check=True).stdout
assert '0 active channels' in cli('core show channels count')
c=Path('/etc/asterisk')
assert not (c/'pjsip_roaming.conf').exists()
assert 'Unable to find object' in cli('pjsip show endpoint 1003')
b=Path('/var/backups/asterisk-roaming')/datetime.datetime.now().strftime('%Y%m%d-%H%M%S');b.mkdir(parents=True,mode=0o700)
modified=['pjsip.conf','extensions.conf','extensions_local.conf','extensions_direct_ip_phone.conf','extensions_linphone_push.conf']
for n in modified:shutil.copy2(c/n,b/n)
(b/'manifest.json').write_text(json.dumps({'modified':modified,'created':list(sources)+['pjsip_roaming_auth.conf']}))
def write(p,s):
 t=p.with_name(p.name+'.roaming-new');t.write_text(s);os.chmod(t,0o640);os.chown(t,0,grp.getgrnam('asterisk').gr_gid);os.replace(t,p)
for n,s in sources.items():write(c/n,s)
write(c/'pjsip_roaming_auth.conf','[travel-phone-auth]\ntype=auth\nauth_type=userpass\nusername=1003\npassword='+password+'\n')
s=(c/'pjsip.conf').read_text()
s,n=re.subn(r'^#include pjsip_linphone_push(?:_auth)?\.conf\s*$', '',s,flags=re.M);assert n==2
write(c/'pjsip.conf',s.rstrip()+'\n#include pjsip_roaming.conf\n#include pjsip_roaming_auth.conf\n')
write(c/'extensions.conf',(c/'extensions.conf').read_text().rstrip()+'\n#include extensions_roaming.conf\n')
new="""[from-home-mobile]
exten => s,1,NoOp(Incoming home SIM to personal Linphone)
 same => n,Dial(PJSIP/linphone-cellular/sip:traveler-example@sip.linphone.org:5061\\;transport=tls,45,b(direct-phone-rtp-source-reset^s^1))
 same => n,Hangup()
"""
s,n=re.subn(r'(?ms)^\[from-home-mobile\]\n.*?(?=^\[|\Z)',lambda m:new,(c/'extensions_local.conf').read_text());assert n==1
write(c/'extensions_local.conf',s)
for name in ['extensions_direct_ip_phone.conf','extensions_linphone_push.conf']:
 s=(c/name).read_text();assert 'PJSIP/linphone-push/sip:traveler-example@sip.linphone.org,45' in s
 s=s.replace('PJSIP/linphone-push/sip:traveler-example@sip.linphone.org,45','PJSIP/linphone-federation/sip:traveler-example@sip.linphone.org:5061\\;transport=tls,45,b(direct-phone-rtp-source-reset^s^1)')
 write(c/name,s)
print(json.dumps({'backup':str(b),'reload':[cli('module reload res_pjsip.so'),cli('dialplan reload')],
 'route':cli('dialplan show from-home-mobile'),'outgoing':cli('dialplan show from-travel-phone'),
 'old_auth':cli('pjsip show auth linphone-push-auth'),'old_endpoint':cli('pjsip show endpoint linphone-push'),
 'new_endpoint':cli('pjsip show endpoint 1003')},ensure_ascii=False,indent=2))
'''
cmd=['ssh','-o','BatchMode=yes','-o','ConnectTimeout=6','gateway@192.168.50.10','docker run -i --rm --pull=never --network none --pid host --privileged --entrypoint nsenter valkey/valkey:9.1.3 -t 1 -m -n -r -w python3 -']
r=subprocess.run(cmd,input='sources='+repr(sources)+'\npassword='+repr(password)+'\n'+script,capture_output=True,text=True,timeout=60)
password=''
if r.returncode:raise RuntimeError('Remote deployment failed: '+r.stderr)
x=json.loads(r.stdout)
(ROOT/'diagnostics/2026-11-14-roaming/install.json').write_text(r.stdout)
print(json.dumps({k:v for k,v in x.items() if k!='new_endpoint'},ensure_ascii=False,indent=2))
