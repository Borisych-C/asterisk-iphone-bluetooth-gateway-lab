#!/usr/bin/python3
"""Install authenticated MESSAGE entry point on the existing .128 Asterisk.
Run as administrator, then run ../install.sh as gateway. Preserves auth secrets.
"""
import datetime,grp,json,os,pwd,re,shutil,subprocess,tempfile
from pathlib import Path
assert os.geteuid()==0,'administrator required'
source=Path(__file__).resolve().parents[1];user=pwd.getpwnam('gateway');group=grp.getgrnam('asterisk')
os.umask(0o077)
backup=Path('/var/backups/asterisk-sms-outgoing')/datetime.datetime.now().strftime('%Y%m%d-%H%M%S');backup.mkdir(parents=True)
for name in ['pjsip_roaming.conf','extensions.conf']:
 shutil.copy2('/etc/asterisk/'+name,backup/name)
def write(path,data,uid,gid,mode):
 fd,tmp=tempfile.mkstemp(dir=path.parent,prefix='.'+path.name)
 try:
  with os.fdopen(fd,'w') as f:f.write(data);f.flush();os.fsync(f.fileno())
  os.chown(tmp,uid,gid);os.chmod(tmp,mode);os.replace(tmp,path)
 finally:Path(tmp).unlink(missing_ok=True)
socketdir=Path('/var/lib/asterisk-sms-bridge');socketdir.mkdir(exist_ok=True);os.chown(socketdir,user.pw_uid,group.gr_gid);os.chmod(socketdir,0o2750)
settings=Path('/etc/asterisk/asterisk.conf').read_text()
match=re.search(r'^\s*astagidir\s*(?:=>|=)\s*([^;\n]+)',settings,re.M);assert match,'AGI directory must be explicit'
agidir=Path(match[1].strip());assert agidir.is_dir()
write(agidir/'sms-submit.agi',(source/'sms-submit.agi').read_text(),0,group.gr_gid,0o750)
write(Path('/etc/asterisk/extensions_sms.conf'),(source/'asterisk/extensions_sms.conf').read_text(),0,group.gr_gid,0o640)
p=Path('/etc/asterisk/pjsip_roaming.conf');s=p.read_text();assert s.count('context=from-travel-phone\n')==1
if 'message_context=from-travel-sms' not in s:write(p,s.replace('context=from-travel-phone\n','context=from-travel-phone\nmessage_context=from-travel-sms\n'),0,group.gr_gid,0o640)
p=Path('/etc/asterisk/extensions.conf');s=p.read_text()
if '#include "extensions_sms.conf"' not in s:write(p,s+'\n#include "extensions_sms.conf"\n',0,group.gr_gid,0o640)
conf=Path(user.pw_dir)/'.config/asterisk-sms-bridge';conf.mkdir(parents=True,exist_ok=True);os.chown(conf,user.pw_uid,user.pw_gid);os.chmod(conf,0o700)
p=conf/'config.json';data=json.loads((p if p.exists() else source/'config.json').read_text());data.update(submit_socket=str(socketdir/'submit.sock'),submit_uid=pwd.getpwnam('asterisk').pw_uid)
write(p,json.dumps(data,indent=2)+'\n',user.pw_uid,user.pw_gid,0o600)
for cmd in ['pjsip reload','dialplan reload']:subprocess.run(['/usr/sbin/asterisk','-rx',cmd],check=True)
print('Backup:',backup)
