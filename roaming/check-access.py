#!/usr/bin/env python3
"""Unauthenticated INVITEs must be challenged before any cellular call."""
import json,re,secrets,socket,ssl
DOMAIN='home.example.net'
for user,target in [('1003','+972501234567'),('untrusted','+972501234567'),('1003','600')]:
 with socket.create_connection((DOMAIN,5061),timeout=7) as raw:
  with ssl.create_default_context().wrap_socket(raw,server_hostname=DOMAIN) as s:
   s.settimeout(8)
   local,port=s.getsockname()[:2];tag=secrets.token_hex(8);branch='z9hG4bK'+secrets.token_hex(8);cid=secrets.token_hex(12)
   uri=f'sip:{target}@{DOMAIN}'
   common=[f'Via: SIP/2.0/TLS {local}:{port};branch={branch};rport','Max-Forwards: 5',f'From: <sip:{user}@{DOMAIN}>;tag={tag}',f'To: <{uri}>',f'Call-ID: {cid}']
   s.sendall(('\r\n'.join([f'INVITE {uri} SIP/2.0',*common,'CSeq: 1 INVITE',f'Contact: <sip:{user}@{local}:{port};transport=tls>','Content-Length: 0','',''])).encode())
   buf=b'';status=0;hdr=''
   while status<200:
    chunk=s.recv(65536)
    if not chunk:raise RuntimeError('Connection ended before final response')
    buf+=chunk
    while b'\r\n\r\n' in buf:
     h,t=buf.split(b'\r\n\r\n',1);m=re.search(br'(?im)^Content-Length:\s*(\d+)',h);n=int(m[1]) if m else 0
     if len(t)<n:break
     buf=t[n:];hdr=h.decode();status=int(hdr.split()[1])
     if status>=200:break
   assert status in (401,403,407),(user,target,status)
   to=re.search(r'(?im)^To:\s*(.*)$',hdr)[1].strip()
   ack=[f'ACK {uri} SIP/2.0',*[to if l.startswith('To:') else l for l in common],'CSeq: 1 ACK','Content-Length: 0','','']
   ack=[('To: '+l) if l==to else l for l in ack]
   s.sendall('\r\n'.join(ack).encode())
   print(json.dumps({'from':user,'target':target,'status':status,'tls':s.version(),'certificate_verified':True,'authorization_sent':False}),flush=True)
