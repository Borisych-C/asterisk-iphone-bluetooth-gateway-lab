#!/usr/bin/python3
"""TLS/digest MESSAGE to reserved smscheck; never sends a cellular message."""
import hashlib,json,re,secrets,socket,ssl,subprocess,sys
D='home.example.net';U='1003';uri='sip:smscheck@'+D
to_user=sys.argv[1] if len(sys.argv)>1 else 'smscheck'
assert re.fullmatch(r'[a-z0-9+-]{1,40}',to_user)
test_body=('SMS route check — Привет! שלום!\nEnd ()' if '--unicode' in sys.argv else 'SMS route check only; do not send to cellular network.').encode()
password=subprocess.run(['/usr/bin/python3','/home/gateway/asterisk/linphone-push/keyring_credentials.py','lookup','--host',D,'--username',U,'--kind','travel-sip'],capture_output=True,text=True,check=True).stdout
with socket.create_connection((D,5061),timeout=8) as raw:
 with ssl.create_default_context().wrap_socket(raw,server_hostname=D) as s:
  s.settimeout(10);ip,port=s.getsockname()[:2];cid=secrets.token_hex(16);tag=secrets.token_hex(8);buf=b'';codes=[]
  def send(seq,auth=None):
   body=test_body
   h=[f'MESSAGE {uri} SIP/2.0',f'Via: SIP/2.0/TLS {ip}:{port};branch=z9hG4bK{secrets.token_hex(8)};rport','Max-Forwards: 10',f'From: <sip:{U}@{D}>;tag={tag}',f'To: <sip:{to_user}@{D}>',f'Call-ID: {cid}',f'CSeq: {seq} MESSAGE','Content-Type: text/plain;charset=utf-8']
   if auth:h.append('Authorization: '+auth)
   h+=['Content-Length: '+str(len(body)),'',''];s.sendall('\r\n'.join(h).encode()+body)
  def receive():
   global buf
   while True:
    while b'\r\n\r\n' not in buf:buf+=s.recv(16384)
    head,rest=buf.split(b'\r\n\r\n',1);m=re.search(br'(?im)^Content-Length:\s*(\d+)',head);n=int(m[1]) if m else 0
    if len(rest)<n:buf+=s.recv(16384);continue
    buf=rest[n:];code=int(head.split()[1]);codes.append(code)
    if code>=200:return code,head.decode()
  send(1);code,h=receive();assert code==401, 'unauthenticated MESSAGE was not challenged'
  challenge=re.search(r'(?im)^WWW-Authenticate:\s*(.*)$',h)[1].strip()
  v={k.lower():a or b for k,a,b in re.findall(r'(\w+)=(?:"([^"]*)"|([^,\s]+))',challenge)}
  assert v.get('algorithm','MD5').upper()=='MD5'
  md5=lambda x:hashlib.md5(x.encode()).hexdigest();cn=secrets.token_hex(8);nc='00000001'
  response=md5(md5(U+':'+v['realm']+':'+password)+':'+v['nonce']+':'+nc+':'+cn+':auth:'+md5('MESSAGE:'+uri))
  auth=f'Digest username="{U}", realm="{v["realm"]}", nonce="{v["nonce"]}", uri="{uri}", response="{response}", algorithm=MD5, qop=auth, nc={nc}, cnonce="{cn}"'
  if 'opaque' in v:auth+=', opaque="'+v['opaque']+'"'
  send(2,auth);code,h=receive();assert code in (200,202),str(code)
  print(json.dumps({'statuses':codes,'tls':s.version(),'certificate_verified':True,'cellular_send':False,'destination':'smscheck','authenticated_user':'1003','expected_request_id':hashlib.sha256(json.dumps([cid,'2 MESSAGE','pjsip:'+to_user+'@'+D,test_body.decode()],ensure_ascii=False).encode()).hexdigest()}))
