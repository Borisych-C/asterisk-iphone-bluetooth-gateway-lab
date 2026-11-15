"""Loopback-only SIP/RTP stream restart reproduction; never calls real devices."""
import collections
import audioop
import json
import os
from pathlib import Path
import re
import select
import socket
import struct
import subprocess
import sys
import tempfile
import time

root = Path(tempfile.mkdtemp(prefix='asterisk-rtp-restart-', dir='/tmp'))
for name in ('etc', 'run', 'log', 'lib', 'spool'):
    (root/name).mkdir()
modules = '/usr/lib/x86_64-linux-gnu/asterisk/modules'
fix = '--fix' in sys.argv
if fix:
    module_dir=root/'modules';module_dir.mkdir()
    for module in Path(modules).glob('*.so'):
        (module_dir/module.name).symlink_to(module)
    (module_dir/'app_rtp_source_reset.so').symlink_to('/home/gateway/asterisk-host-framing-20261114/built/app_rtp_source_reset.so')
    modules=str(module_dir)
dirs = dict(astetcdir=root/'etc', astmoddir=modules, astvarlibdir=root/'lib',
            astdbdir=root/'lib', astkeydir=root/'lib/keys', astdatadir='/usr/share/asterisk',
            astagidir=root/'lib/agi', astspooldir=root/'spool', astrundir=root/'run', astlogdir=root/'log')
(root/'etc/asterisk.conf').write_text('[directories]\n'+''.join(f'{k} => {v}\n' for k,v in dirs.items())+
                                    '[options]\nverbose=0\ndebug=0\nhighpriority=no\nlive_dangerously=no\n')
loads = ['res_timing_timerfd', 'res_sorcery_config', 'res_sorcery_memory', 'res_sorcery_astdb',
         'res_pjproject', 'res_pjsip', 'res_pjsip_pubsub', 'res_pjsip_session', 'res_pjsip_sdp_rtp',
         'res_pjsip_endpoint_identifier_ip', 'res_pjsip_endpoint_identifier_user',
         'res_rtp_asterisk', 'chan_pjsip', 'codec_alaw', 'codec_ulaw', 'pbx_config', 'app_echo',
         'bridge_simple', 'bridge_softmix', 'app_dial', 'func_channel', 'res_audiosocket', 'app_audiosocket']
if fix: loads.append('app_rtp_source_reset')
(root/'etc/modules.conf').write_text('[modules]\nautoload=no\n'+''.join('load='+n+'.so\n' for n in loads))
(root/'etc/logger.conf').write_text('[logfiles]\nmessages=notice,warning,error,debug,verbose\n')
(root/'etc/rtp.conf').write_text('[general]\nrtpstart=24000\nrtpend=24100\nstrictrtp=yes\n')
(root/'etc/pjsip.conf').write_text('''[global]
type=global
endpoint_identifier_order=ip,username
[transport-test]
type=transport
protocol=udp
bind=127.0.0.1:15060
[fixture]
type=endpoint
context=fixture
disallow=all
allow=alaw
direct_media=no
media_address=127.0.0.1
bind_rtp_to_media_address=yes
[fixture-ip]
type=identify
endpoint=fixture
match=127.0.0.1/32
''')
(root/'etc/extensions.conf').write_text('''[general]
static=yes
writeprotect=yes
[fixture]
exten => echo,1,Answer()
 same => n,Echo()
exten => bridge,1,Dial(Local/echo@fixture/n)
exten => pcm,1,Answer()
 same => n,AudioSocket(00000000-0000-4000-8000-000000000001,127.0.0.1:15061)
''')
if fix:
    path=root/'etc/extensions.conf'
    path.write_text(path.read_text().replace(' same => n,AudioSocket(', ' same => n,RtpSourceReset()\n same => n,AudioSocket('))

def cli(text):
    return subprocess.check_output(['/usr/sbin/asterisk','-C',str(root/'etc/asterisk.conf'),'-rx',text],text=True,timeout=5)

log = (root/'startup.log').open('wb')
process = subprocess.Popen(['/usr/sbin/asterisk','-f','-g','-C',str(root/'etc/asterisk.conf')],
                           stdin=subprocess.DEVNULL,stdout=log,stderr=log)
results = []
try:
    for _ in range(60):
        if process.poll() is not None:
            raise RuntimeError('startup failed: '+(root/'startup.log').read_text()[-5000:])
        if (root/'run/asterisk.ctl').exists():
            break
        time.sleep(.1)
    time.sleep(.3)
    print(json.dumps(dict(event='ready',root=str(root),pid=process.pid,modules=cli('module show like pjsip'))),flush=True)
    for extension in ('pcm',):
        listener = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        listener.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
        listener.bind(('127.0.0.1',15061));listener.listen(1);listener.settimeout(4)
        sip = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        rtp = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        sip.bind(('127.0.0.1',0)); rtp.bind(('127.0.0.1',0))
        sip.setblocking(False); rtp.setblocking(False)
        sport, rport = sip.getsockname()[1], rtp.getsockname()[1]
        callid = f'fixture-{extension}-{os.getpid()}@localhost'
        tag = str(os.getpid())
        to = f'<sip:{extension}@127.0.0.1>'
        target = f'sip:{extension}@127.0.0.1:15060'
        def request(method, seq, body='', dest=target):
            head = [f'{method} {dest} SIP/2.0',
                    f'Via: SIP/2.0/UDP 127.0.0.1:{sport};branch=z9hG4bK-{method}-{seq}-{tag};rport',
                    'Max-Forwards: 70', f'From: <sip:fixture@127.0.0.1>;tag={tag}',f'To: {to}',
                    f'Call-ID: {callid}',f'CSeq: {seq} {method}',
                    f'Contact: <sip:fixture@127.0.0.1:{sport}>']
            if body: head.append('Content-Type: application/sdp')
            head.append(f'Content-Length: {len(body)}')
            sip.sendto(('\r\n'.join(head)+'\r\n\r\n'+body).encode(),('127.0.0.1',15060))
        sdp = ('v=0\r\no=- 1 1 IN IP4 127.0.0.1\r\ns=fixture\r\nc=IN IP4 127.0.0.1\r\nt=0 0\r\n'
               f'm=audio {rport} RTP/AVP 8\r\na=rtpmap:8 PCMA/8000\r\na=sendrecv\r\n')
        request('INVITE',1,sdp)
        deadline=time.monotonic()+5
        remote=None
        while time.monotonic()<deadline:
            if not select.select([sip],[],[],.2)[0]: continue
            data=sip.recv(65535).decode()
            if data.startswith('SIP/2.0 200'):
                to=re.search(r'\r\nTo: *([^\r]+)',data,re.I)[1]
                remote=('127.0.0.1',int(re.search(r'\r\nm=audio (\d+)',data)[1]))
                request('ACK',1)
                break
            if data.startswith(('SIP/2.0 4','SIP/2.0 5','SIP/2.0 6')):
                raise RuntimeError(data.split('\r\n')[0])
        if remote is None: raise TimeoutError('no answer')
        pcmconn,_=listener.accept();pcmconn.setblocking(False);pcmbuf=b''
        if fix:
            blocked=cli('module unload app_rtp_source_reset.so')
            if 'Unloaded' in blocked or 'app_rtp_source_reset.so' not in cli('module show like app_rtp_source_reset'):
                raise AssertionError('module unloaded with an active hook')
            print(json.dumps(dict(event='active_unload_guard',passed=True)),flush=True)
        # Recorded failing and successful stream restarts, with synthetic PCMA audio.
        phases=[(595501041,303,773136384),(1990059340,2633,287761015),(1742418235,59789,722386837),
                (1322162315,55456,1804415588),(1995688384,7909,716372377),(1501735964,10861,1515484020),
                (1154547706,17853,1179080597),(1213872525,8704,1961752686),(685985452,13394,1573387122)]
        for phase,(ssrc,seq,ts) in enumerate(phases):
            sent=received=valid=pcm_valid=late_sent=0
            payload=bytes([0x20+phase])*160
            start=time.monotonic(); next_send=start
            while time.monotonic()<start+1.2:
                now=time.monotonic()
                if sent<50 and now>=next_send:
                    packet=struct.pack('!BBHII',128,8|(128 if sent==0 else 0),(seq+sent)&65535,(ts+160*sent)&0xffffffff,ssrc)+payload
                    rtp.sendto(packet,remote);sent+=1;next_send=start+sent*.02
                    if phase==len(phases)-1 and sent==21:
                        duplicate=struct.pack('!BBHII',128,8,(seq+10)&65535,(ts+1600)&0xffffffff,ssrc)+payload
                        rtp.sendto(duplicate,remote);late_sent+=1
                for sock in select.select([rtp,sip,pcmconn],[],[],max(0,min(.02,next_send-time.monotonic())) if sent<50 else .02)[0]:
                    data=sock.recv(65535)
                    if sock is rtp:
                        received+=1
                        valid+=int(data[12:]==payload)
                    elif sock is pcmconn:
                        pcmbuf+=data
                        while len(pcmbuf)>=3:
                            size=int.from_bytes(pcmbuf[1:3],'big')
                            if len(pcmbuf)<size+3:break
                            kind=pcmbuf[0];body=pcmbuf[3:size+3];pcmbuf=pcmbuf[3+size:]
                            if kind==16:
                                pcm_valid+=int(body==audioop.alaw2lin(payload,2))
                                pcmconn.sendall(bytes([16])+len(body).to_bytes(2,'big')+body)
                    elif data.startswith(b'SIP/2.0 200'): request('ACK',1)
            result=dict(extension=extension,phase=phase,ssrc=ssrc,initial_seq=seq,sent=sent,late_sent=late_sent,received=received,valid=valid,pcm_valid=pcm_valid)
            results.append(result);print(json.dumps(result),flush=True)
            if fix and phase>0 and (valid!=50 or pcm_valid!=50): raise AssertionError('loss, surplus or damaged PCM')
        request('BYE',2)
        if fix:
            deadline=time.monotonic()+3
            while '0 active channels' not in cli('core show channels count') and time.monotonic()<deadline: time.sleep(.1)
            released=cli('module unload app_rtp_source_reset.so')
            if 'app_rtp_source_reset.so' in cli('module show like app_rtp_source_reset'):
                raise AssertionError('module retained after hangup')
            print(json.dumps(dict(event='hangup_releases_hook',passed=True)),flush=True)
        sip.close();rtp.close();pcmconn.close();listener.close()
    passed=all(x['valid']>=49 and x['pcm_valid']>=49 for x in results)
    print(json.dumps(dict(event='result',fix=fix,all_phases_passed=passed)),flush=True)
    if fix and not passed: raise AssertionError('audio missing with reset enabled')
finally:
    try: cli('core stop now')
    except Exception: process.terminate()
    try: process.wait(8)
    except subprocess.TimeoutExpired: process.kill();process.wait()
    log.close()
    print(json.dumps(dict(event='stopped',root=str(root),exit=process.returncode)),flush=True)
