#!/usr/bin/env python3
"""Single authorized delivery test, TLS verified, no Linphone account credentials."""
import json,re,secrets,socket,ssl
remote='sip.linphone.org';domain='home.example.net';target='sip:traveler-example@'+remote
body='SMS bridge test — Привет! שלום!'.encode()
with socket.create_connection((remote,5061),timeout=10) as raw:
 with ssl.create_default_context().wrap_socket(raw,server_hostname=remote) as s:
  s.settimeout(20);ip,port=s.getsockname()[:2]
  lines=[f'MESSAGE {target} SIP/2.0',f'Via: SIP/2.0/TLS {ip}:{port};branch=z9hG4bK{secrets.token_hex(8)};rport','Max-Forwards: 20',f'From: "Home SIM test" <sip:sms-test@{domain}>;tag={secrets.token_hex(8)}',f'To: <{target}>',f'Call-ID: {secrets.token_hex(16)}@{domain}','CSeq: 1 MESSAGE',f'Contact: <sip:sms-test@{domain}:5061;transport=tls>','Content-Type: text/plain;charset=utf-8','Content-Length: '+str(len(body)),'','']
  s.sendall('\r\n'.join(lines).encode()+body)
  buf=b'';statuses=[];final=0
  while not final:
   chunk=s.recv(65536)
   if not chunk:raise RuntimeError('Connection closed before final reply')
   buf+=chunk
   while b'\r\n\r\n' in buf:
    h,t=buf.split(b'\r\n\r\n',1);m=re.search(br'(?im)^Content-Length:\s*(\d+)',h);n=int(m[1]) if m else 0
    if len(t)<n:break
    buf=t[n:];line=h.decode().splitlines()[0];code=int(line.split()[1]);statuses.append(line)
    if code>=200:final=code;break
  print(json.dumps({'statuses':statuses,'tls':s.version(),'certificate_verified':True,'authorization_used':False,'body_bytes':len(body)}))
