#!/usr/bin/env python3
"""TLS/certificate and SIP checks; never place a call to the phone."""
import argparse
import json
import re
import secrets
import socket
import ssl

parser=argparse.ArgumentParser()
parser.add_argument('--host',default='192.168.50.10')
parser.add_argument('--port',type=int,default=5062)
args=parser.parse_args()
domain='home.example.net'

def probe(method,user,expected):
    assert method=='OPTIONS' or user=='612', 'Only invalid call targets may be tested'
    context=ssl.create_default_context()
    with socket.create_connection((args.host,args.port),timeout=6) as raw:
        with context.wrap_socket(raw,server_hostname=domain) as sock:
            sock.settimeout(6)
            local,port=sock.getsockname()[:2]
            branch='z9hG4bK'+secrets.token_hex(8)
            call_id=secrets.token_hex(12)+'@probe'
            tag=secrets.token_hex(8)
            uri='sips:'+user+'@'+domain
            to='<sips:1002@'+domain+'>'
            via=f'SIP/2.0/TLS {local}:{port};branch={branch};rport'
            from_hdr=f'<sips:diagnostic@{local}>;tag={tag}'
            fields=[f'{method} {uri} SIP/2.0','Via: '+via,'Max-Forwards: 5',
                    'From: '+from_hdr,'To: '+to,'Call-ID: '+call_id,
                    f'CSeq: 1 {method}',f'Contact: <sips:diagnostic@{local}:{port}>',
                    'Content-Length: 0','','']
            sock.sendall('\r\n'.join(fields).encode())
            data=b'';statuses=[];final=''
            while not final:
                data+=sock.recv(16384)
                while b'\r\n\r\n' in data:
                    header,tail=data.split(b'\r\n\r\n',1)
                    length=re.search(br'(?im)^Content-Length:\s*(\d+)',header)
                    size=int(length[1]) if length else 0
                    if len(tail)<size:break
                    data=tail[size:]
                    header=header.decode(errors='replace')
                    status=header.splitlines()[0];statuses.append(status)
                    if int(status.split()[1])>=200:
                        final=header;break
            if method=='INVITE':
                remote_to=re.search(r'(?im)^To:\s*(.*)$',final)[1].strip()
                ack=[f'ACK {uri} SIP/2.0','Via: '+via,'Max-Forwards: 5',
                     'From: '+from_hdr,'To: '+remote_to,'Call-ID: '+call_id,
                     'CSeq: 1 ACK','Content-Length: 0','','']
                sock.sendall('\r\n'.join(ack).encode())
            result={'method':method,'target':user,'statuses':statuses,
                    'tls':sock.version(),'certificate_verified':True,
                    'host':args.host,'port':args.port}
            print(json.dumps(result),flush=True)
            assert int(statuses[-1].split()[1])==expected,result

probe('OPTIONS','1002',200)
probe('INVITE','612',404)
