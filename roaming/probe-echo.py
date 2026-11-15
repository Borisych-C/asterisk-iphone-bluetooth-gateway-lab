#!/usr/bin/env python3
"""Authorize a TLS/SRTP call to local Echo 600, then hang up; no SIM call."""
import base64,hashlib,json,re,secrets,socket,ssl,subprocess
D='home.example.net';U='1003';uri='sip:600@'+D
password=subprocess.run(['/usr/bin/python3','/home/gateway/asterisk/linphone-push/keyring_credentials.py','lookup','--host',D,'--username',U,'--kind','travel-sip'],capture_output=True,text=True,check=True).stdout
with socket.create_connection((D,5061),timeout=8) as raw:
 with ssl.create_default_context().wrap_socket(raw,server_hostname=D) as s:
  s.settimeout(8);ip,port=s.getsockname()[:2];tag=secrets.token_hex(8);cid=secrets.token_hex(12);buf=b'';statuses=[]
  frm=f'<sip:{U}@{D}>;tag={tag}';to=f'<{uri}>';contact=f'<sip:{U}@{ip}:{port};transport=tls>'
  body='\r\n'.join(['v=0',f'o=- 1 1 IN IP4 {ip}','s=Safe echo test',f'c=IN IP4 {ip}','t=0 0','m=audio 30000 RTP/SAVP 8 101','a=rtpmap:8 PCMA/8000','a=rtpmap:101 telephone-event/8000','a=crypto:1 AES_CM_128_HMAC_SHA1_80 inline:'+base64.b64encode(secrets.token_bytes(30)).decode(),'a=sendrecv',''])
  def send(method,seq,branch,target=uri,tohdr=None,auth=None,sdp=''):
   h=[f'{method} {target} SIP/2.0',f'Via: SIP/2.0/TLS {ip}:{port};branch={branch};rport','Max-Forwards: 10','From: '+frm,'To: '+(tohdr or to),'Call-ID: '+cid,f'CSeq: {seq} {method}','Contact: '+contact]
   if auth:h.append('Authorization: '+auth)
   if sdp:h.append('Content-Type: application/sdp')
   h += ['Content-Length: '+str(len(sdp.encode())),'','']
   s.sendall(('\r\n'.join(h)+sdp).encode())
  def receive():
   global buf
   while True:
    while b'\r\n\r\n' not in buf:
     chunk=s.recv(65536)
     if not chunk:raise RuntimeError('Closed SIP connection')
     buf+=chunk
    h,t=buf.split(b'\r\n\r\n',1);m=re.search(br'(?im)^Content-Length:\s*(\d+)',h);n=int(m[1]) if m else 0
    while len(t)<n:
     buf+=s.recv(65536);h,t=buf.split(b'\r\n\r\n',1)
    buf=t[n:];txt=h.decode();code=int(txt.split()[1]);statuses.append(code)
    if code>=200:return code,txt,t[:n].decode()
  header=lambda name,h:re.search(r'(?im)^'+re.escape(name)+r':\s*(.*)$',h)[1].strip()
  branch='z9hG4bK'+secrets.token_hex(8);send('INVITE',1,branch,sdp=body);code,h,_=receive();assert code==401
  send('ACK',1,branch,tohdr=header('To',h))
  challenge=header('WWW-Authenticate',h)
  vals={k.lower():v or w for k,v,w in re.findall(r'(\w+)=(?:"([^"]*)"|([^,\s]+))',challenge)}
  assert vals.get('algorithm','MD5').upper()=='MD5'
  md5=lambda t:hashlib.md5(t.encode()).hexdigest()
  cnonce=secrets.token_hex(8);qop='auth';nc='00000001'
  response=md5(md5(U+':'+vals['realm']+':'+password)+':'+vals['nonce']+':'+nc+':'+cnonce+':'+qop+':'+md5('INVITE:'+uri))
  auth=f'Digest username="{U}", realm="{vals["realm"]}", nonce="{vals["nonce"]}", uri="{uri}", response="{response}", algorithm=MD5, qop=auth, nc={nc}, cnonce="{cnonce}"'
  if 'opaque' in vals:auth+=', opaque="'+vals['opaque']+'"'
  branch='z9hG4bK'+secrets.token_hex(8);send('INVITE',2,branch,auth=auth,sdp=body);code,h,answer=receive()
  if code!=200:
   send('ACK',2,branch,tohdr=header('To',h));raise RuntimeError('Echo INVITE rejected: '+str(code))
  target=re.search(r'<([^>]+)>',header('Contact',h))[1];to=header('To',h)
  send('ACK',2,'z9hG4bK'+secrets.token_hex(8),target=target)
  send('BYE',3,'z9hG4bK'+secrets.token_hex(8),target=target);bye,_,_=receive();assert bye==200
  assert 'RTP/SAVP' in answer and 'a=crypto:' in answer
  print(json.dumps({'target':'600 Echo only','statuses':statuses,'tls':s.version(),'srtp_negotiated':True,'hangup':bye,'cellular_call':False}))
