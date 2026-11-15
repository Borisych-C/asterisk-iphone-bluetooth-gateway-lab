#!/usr/bin/env python3
"""Offline checks only: syntax, case links, privacy boundary, unit tests and C harness.
Does not install, restart services, access Bluetooth or place calls/messages.
"""
from pathlib import Path
import ast,json,re,subprocess,sys,tempfile,hashlib
root=Path(__file__).resolve().parents[1]
def run(*args,cwd=root):subprocess.run(args,cwd=cwd,check=True)
files=[p for p in root.rglob('*') if p.is_file() and not any(x in p.parts for x in ('.git','__pycache__','built'))]
for p in files:
 if p.suffix in ('.py','.agi'):ast.parse(p.read_text(),filename=str(p.relative_to(root)))
 if p.suffix=='.sh':run('bash','-n',str(p))
 if p.suffix=='.json':json.loads(p.read_text())
for case in json.loads((root/'docs/issues.json').read_text())['cases']:
 for field in ('source','test_or_evidence','case'):assert (root/case[field]).is_file(),case[field]
for name in ('README.md','README.ru.md','AGENTS.md','llms.txt','docs/INDEX.md','docs/DEVICE-QUIRKS.md'):
 p=root/name
 for link in re.findall(r'\]\(([^)]+)\)',p.read_text()):
  if '://' not in link:assert (p.parent/link.split('#')[0]).exists(),(name,link)
# Keep the public gate generic: do not put an operator's secrets in its denylist.
for p in files:
 rel=p.relative_to(root)
 if p.name=='check.py':continue
 assert not p.is_symlink(),str(rel)
 assert p.suffix.lower() not in {'.pem','.key','.p12','.pcap','.pcapng','.btsnoop','.sqlite','.sqlite3','.db','.heic','.tgz','.gz','.zip','.so','.o'},str(rel)
 s=p.read_text(errors='strict')
 assert not re.search(r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----',s),str(rel)
 assert not re.search(r'(?i)https://files\.linphone\.org/',s),str(rel)
 assert not re.search(r'(?i)\b(?!www\b)[a-z0-9-]+\.duckdns\.org\b',s),str(rel)
 assert not re.search(r'(?i)\b2a0d:[0-9a-f:]+',s),str(rel)
header_root=root/'recovery/2026-11-14/work/input'
manifest=json.loads((header_root/'manifest.json').read_text())
for rel,h in manifest['immutable_files_sha256'].items():assert hashlib.sha256((header_root/rel).read_bytes()).hexdigest()==h,rel
run(sys.executable,'-m','unittest','discover','-s','sms-bridge/tests','-v')
run(sys.executable,'network/duckdns/test_updater.py')
with tempfile.TemporaryDirectory(prefix='asterisk-offline-check-') as temp:
 binary=str(Path(temp)/'framing-test')
 work=root/'recovery/2026-11-14/work'
 run('cc','-Wall','-Wextra','-Werror','-fsanitize=address,undefined','-Iinput/include-bluetooth','test.c','-o',binary,cwd=work)
 run(binary)
print('PASS: syntax, JSON, navigation, publication boundary, immutable headers, SMS/DNS tests, C framing harness')
