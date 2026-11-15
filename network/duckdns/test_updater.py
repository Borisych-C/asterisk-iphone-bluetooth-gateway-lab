#!/usr/bin/env python3
"""Run the real shell updater against bounded fake HTTP/IP executables."""
import fcntl
import json
import os
from pathlib import Path
import subprocess
import tempfile

SCRIPT=Path(__file__).with_name('update_duckdns.sh').resolve()
CURL='''#!/usr/bin/python3
import json,os,sys
from pathlib import Path
from urllib.parse import urlparse,parse_qs
assert "test-token" not in " ".join(sys.argv)
data=sys.stdin.read()
url=data.split('"',2)[1]
q=parse_qs(urlparse(url).query)
stage="public" if "checkip.amazonaws.com" in url else "clear" if q.get("clear")==["true"] else "update"
scenario=json.loads(Path(os.environ["SCENARIO"]).read_text())
counter=Path(os.environ["COUNTER"])
n=int(counter.read_text()) if counter.exists() else 0
item=scenario[n]
assert item[0]==stage,(n,stage,item)
assert stage=="public" or q["token"]==["test-token"]
if stage=="update":
 assert q.get("ip")==["192.0.2.2"]
 expected_ipv6=os.environ["EXPECTED_IPV6"]
 if expected_ipv6:assert q.get("ipv6")==[expected_ipv6]
 else:assert "ipv6" not in q,q
counter.write_text(str(n+1))
print(item[2]+"\\n"+str(item[1]),end="")
sys.exit(item[3] if len(item)>3 else 0)
'''
IP='''#!/usr/bin/python3
import os
ip=os.environ.get("MOCK_IPV6","")
if ip:print("2: enp1s0 inet6 "+ip+"/64 scope global dynamic "+os.environ.get("MOCK_IPV6_FLAGS",""))
'''
def case(name,steps,initial='',ipv6='',expected_rc=0,expected_state='',locked=False,ipv6_flags='',expected_ipv6=None):
 with tempfile.TemporaryDirectory(prefix='duckdns-test-') as tmp:
  p=Path(tmp);(p/'bin').mkdir()
  for file,content in [('curl',CURL),('ip',IP),('sleep','#!/bin/sh\nexit 0\n')]:
   f=p/'bin'/file;f.write_text(content);f.chmod(0o755)
  config=p/'private.conf';config.write_text('DOMAIN="example"\nTOKEN="test-token"\nIPV6_IF="enp1s0"\n')
  state=p/'state'
  if initial is not None:state.write_text(initial)
  scenario=p/'scenario.json';scenario.write_text(json.dumps(steps))
  lock=p/'lock';holder=lock.open('w')
  if locked:fcntl.flock(holder,fcntl.LOCK_EX|fcntl.LOCK_NB)
  env={**os.environ,'PATH':str(p/'bin')+':/usr/bin:/bin:/sbin','DUCKDNS_CONFIG':str(config),'DUCKDNS_STATE_FILE':str(state),'DUCKDNS_LOCK_FILE':str(lock),'SCENARIO':str(scenario),'COUNTER':str(p/'counter'),'MOCK_IPV6':ipv6,'MOCK_IPV6_FLAGS':ipv6_flags,'EXPECTED_IPV6':ipv6 if expected_ipv6 is None else expected_ipv6}
  result=subprocess.run(['/bin/bash',str(SCRIPT)],env=env,capture_output=True,text=True,timeout=10)
  holder.close()
  assert result.returncode==expected_rc,(name,result.returncode,result.stdout,result.stderr)
  assert state.read_text()==expected_state,(name,state.read_text())
  assert int((p/'counter').read_text()) if (p/'counter').exists() else not steps
  if steps:assert int((p/'counter').read_text())==len(steps),name
  assert 'test-token' not in result.stdout+result.stderr,name
  if expected_rc:assert 'DuckDNS=FAIL' in result.stdout and 'DuckDNS=OK' not in result.stdout,name
  print('PASS',name)

PUBLIC=['public',200,'192.0.2.2\n']
OK=['update',200,'OK\n']
case('normal-ipv4',[PUBLIC,OK])
case('transient-502-recovers',[['public',502,'bad gateway'],PUBLIC,['update',502,'bad gateway'],OK])
case('bounded-timeout',[['public','000','',28]]*3,initial='old',expected_rc=1,expected_state='old')
case('invalid-public-ip',[['public',200,'not-an-address']],initial='old',expected_rc=1,expected_state='old')
case('api-KO-keeps-state',[PUBLIC,['update',200,'KO']],initial='old',ipv6='2001:db8::4',expected_rc=1,expected_state='old')
case('ipv6-success',[PUBLIC,OK],initial='old',ipv6='2001:db8::4',expected_state='2001:db8::4\n')
case('ipv6-removal',[PUBLIC,['clear',200,'OK'],OK],initial='2001:db8::4\n')
case('missing-state-clears-ipv6',[PUBLIC,['clear',200,'OK'],OK],initial=None)
case('tentative-ipv6-not-published',[PUBLIC,['clear',200,'OK'],OK],initial='2001:db8::4\n',ipv6='2001:db8::5',ipv6_flags='tentative',expected_ipv6='')
case('dadfailed-ipv6-not-published',[PUBLIC,['clear',200,'OK'],OK],initial='2001:db8::4\n',ipv6='2001:db8::5',ipv6_flags='dadfailed',expected_ipv6='')
case('clear-failure-still-restores-A',[PUBLIC,*([['clear',502,'bad gateway']]*3),OK],initial='2001:db8::4\n',expected_rc=1,expected_state='2001:db8::4\n')
case('temporary-ipv6-not-published',[PUBLIC,['clear',200,'OK'],OK],initial='2001:db8::4\n',ipv6='2001:db8::5',ipv6_flags='temporary',expected_ipv6='')
case('deprecated-ipv6-not-published',[PUBLIC,['clear',200,'OK'],OK],initial='2001:db8::4\n',ipv6='2001:db8::5',ipv6_flags='deprecated',expected_ipv6='')
case('ula-not-published',[PUBLIC,['clear',200,'OK'],OK],initial='2001:db8::4\n',ipv6='fd00:50::1',expected_ipv6='')
case('ipv6-prefix-changed',[PUBLIC,OK],initial='2001:db8::4\n',ipv6='2001:db8:2::6',expected_state='2001:db8:2::6\n')
case('concurrent-run-skips',[],initial='old',expected_state='old',locked=True)
