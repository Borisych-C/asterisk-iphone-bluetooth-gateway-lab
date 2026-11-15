"""Explicitly send one English SIP MESSAGE to 1002; requires root on .128.
No voice call to a phone is placed. Temporary Local channel only.
"""
import json,os,re,socket,struct,subprocess,time
TEXT='Hello! This is a test message from Asterisk.'
context='phone-message-test-'+str(os.getpid())
def cli(text):
 return subprocess.check_output(['asterisk','-rx',text],text=True,timeout=8)
created=False
with socket.socket(socket.AF_PACKET,socket.SOCK_RAW,socket.htons(3)) as capture:
 capture.bind(('enp3s0',0));capture.settimeout(.5)
 try:
  for priority,app in enumerate(('Answer()',f'Set(MESSAGE(body)={TEXT})','MessageSend(pjsip:1002,sip:asterisk@10.77.0.1)','Hangup()'),1):
   out=cli(f'dialplan add extension "send,{priority},{app}" into {context}')
   created=True
   if 'added into' not in out.lower():raise RuntimeError(out)
  cli(f'channel originate Local/send@{context} application Wait 1')
  deadline=time.monotonic()+10;callid=None;result=None
  while time.monotonic()<deadline:
   try:packet=capture.recv(65535)
   except socket.timeout:continue
   if len(packet)<42 or packet[12:14]!=b'\x08\x00' or packet[23]!=17:continue
   offset=14+4*(packet[14]&15)
   sport,dport,size=struct.unpack_from('!HHH',packet,offset)
   if 5060 not in (sport,dport):continue
   data=packet[offset+8:offset+size]
   if not re.search(rb'\r\nCSeq: *\d+ MESSAGE\r\n',data,re.I):continue
   match=re.search(rb'\r\nCall-ID: *([^\r]+)',data,re.I)
   if not match:continue
   if data.startswith(b'MESSAGE ') and TEXT.encode() in data:
    callid=match[1]
    print(json.dumps({'event':'sent','recipient':'1002','text':TEXT}),flush=True)
   if data.startswith(b'SIP/2.0 ') and callid==match[1] and packet[26:30]==socket.inet_aton('10.77.0.2'):
    result=data.split(b'\r\n',1)[0].decode();print(json.dumps({'event':'phone_response','status':result}),flush=True)
    if int(result.split()[1])>=200:break
  if result is None:raise RuntimeError('No matching final response observed')
 finally:
  if created:cli(f'dialplan remove extension send@{context}')
