#!/usr/bin/python3
"""Bounded in-memory SIP observation; emits headers/lengths only, never bodies/auth."""
import subprocess,time,json,re,signal
cli=lambda c:subprocess.run(['/usr/sbin/asterisk','-rx',c],capture_output=True,text=True,timeout=8,check=True).stdout
def stop(*_):raise KeyboardInterrupt
signal.signal(signal.SIGTERM,stop)
cli('pjsip set history clear');cli('pjsip set history on');print('READY',flush=True)
start=time.monotonic();facts=[]
try:
 while time.monotonic()-start<180:
  table=cli('pjsip show history')
  if 'MESSAGE' in table:
   time.sleep(5);break
  time.sleep(2)
finally:
 cli('pjsip set history off');table=cli('pjsip show history')
 for num in re.findall(r'^\s*(\d+)\s+',table,re.M):
  raw=cli('pjsip show history entry '+num)
  raw=re.sub(r'\x1b\[[0-9;]*m','',raw)
  if not re.search(r'(?im)^(?:MESSAGE |CSeq:.* MESSAGE)',raw):continue
  head=raw.replace('\r\n','\n').split('\n\n',1)[0]
  # History has a preamble; extract only explicitly approved SIP fields.
  header=lambda key:(re.search(r'(?im)^'+re.escape(key)+r':\s*([^\r\n]*)',raw).group(1) if re.search(r'(?im)^'+re.escape(key)+r':\s*([^\r\n]*)',raw) else '')
  first=re.search(r'(?m)^(?:MESSAGE .* SIP/2.0|SIP/2.0 \d{3}[^\r\n]*)',raw)
  redact=lambda s:re.sub(r'\+?\d{7,}', '[number]', s)
  facts.append({'entry':int(num),'first_line':redact(first.group(0)) if first else '', 'from':redact(header('From')),'to':redact(header('To')),'content_type':header('Content-Type'),'content_length':header('Content-Length'),'has_authorization':bool(header('Authorization')),'cseq':header('CSeq')})
 cli('pjsip set history clear')
 print(json.dumps({'elapsed':round(time.monotonic()-start,1),'message_packets':facts},ensure_ascii=False),flush=True)
