#!/usr/bin/env python3
"""Manage only the authorized Asterisk mappings; preserve other router rules."""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import secrets
import subprocess
import urllib.parse
import urllib.request

HOST='192.168.50.1'
NAT='Device/NAT/PortMappings'
EVIDENCE=Path('/home/gateway/asterisk/diagnostics/2026-11-14-public-sip')
PROPOSED=[
    dict(Alias='PORTFW_RULE_6',Description='Asterisk SIP TLS',Protocol='TCP',ExternalPort=5061,ExternalPortEndRange=0,InternalPort=5062),
]
for index, port in enumerate(range(10000,10016)):
    PROPOSED.append(dict(Alias='PORTFW_RULE_'+str(7+index),
        Description='Asterisk SRTP' if index==0 else 'Asterisk SRTP '+str(port),
        Protocol='UDP',ExternalPort=port,ExternalPortEndRange=0,InternalPort=port))
for rule in PROPOSED:
    rule.update(Enable=True,Service='NONE',Creator='USER',RemoteHost='',InternalClient='192.168.50.10',
                ExternalInterface='Device/IP/Interfaces/Interface[IP_DATA]',
                InternalInterface='Device/IP/Interfaces/Interface[IP_BR_LAN]')

class Router:
    def __init__(self):
        p=subprocess.run(['/usr/bin/python3','-c',
            'import json,runpy; print(json.dumps(runpy.run_path("/home/gateway/Router/router-keyring.py")["lookup"]()))'],
            capture_output=True,timeout=45,check=True)
        credentials=json.loads(p.stdout)
        assert credentials['host'].rstrip('/') in (HOST,'http://'+HOST)
        self.user=credentials['user']
        self.h=lambda value:hashlib.sha512(value.encode()).hexdigest()
        self.password_hash=self.h(credentials['password']+':Salt123')
        self.session,self.nonce,self.token,self.index='0','','',0
        self.opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
        login=self.request([{'method':'logIn','parameters':{'user':self.user,'persistent':'true','session-options':{
            'nss':[{'name':'gtw','uri':'http://sagemcom.com/gateway-data'}],
            'context-flags':{'get-content-name':True,'local-time':True},'capability-depth':2,
            'capability-flags':{'name':True,'default-value':False,'restriction':True,'description':False},
            'time-format':'ISO_8601','jwt-auth':'true'}}}])
        p=login['actions'][0]['callbacks'][0]['parameters']
        self.session,self.nonce=p['id'],p['nonce']
        self.token=login.get('auth',{}).get('token','')

    def request(self,actions):
        cnonce=secrets.randbelow(4294967295)
        auth=self.token or self.h(self.h(self.user+':'+str(self.nonce)+':'+self.password_hash)+':'+str(self.index)+':'+str(cnonce)+':JSON:/cgi/json-req')
        body={'request':{'id':self.index,'session-id':self.session,'priority':True,'cnonce':cnonce,
            'auth-key':auth,'actions':[dict(a,id=i) for i,a in enumerate(actions)]}}
        self.index+=1
        data=urllib.parse.urlencode({'req':json.dumps(body)}).encode()
        with self.opener.open(urllib.request.Request('http://'+HOST+'/cgi/json-req',data=data),timeout=15) as response:
            reply=json.load(response)['reply']
        assert reply.get('error',{}).get('code')==16777216,'Router request failed'
        for action in reply.get('actions',[]):
            assert action.get('error',{}).get('code')==16777238,'Router action failed'
            for cb in action.get('callbacks',[]):
                assert cb.get('result',{}).get('code')==16777238,'Router callback failed'
        return reply

    def get(self):
        r=self.request([{'method':'getValue','xpath':NAT}])
        return r['actions'][0]['callbacks'][0]['parameters']['value']

def matches(actual,wanted):
    return all(actual.get(k)==v for k,v in wanted.items())

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--apply',action='store_true')
    parser.add_argument('--rollback',action='store_true')
    args=parser.parse_args()
    assert not(args.apply and args.rollback)
    os.umask(0o077)
    stamp=datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
    router=Router()
    try:
        before=router.get()
        (EVIDENCE/('nat-'+stamp+'-before.json')).write_text(json.dumps(before,indent=2)+'\n')
        if args.apply:
            for wanted in PROPOSED:
                current=router.get()
                same=[r for r in current if r['Alias']==wanted['Alias']]
                if same:
                    assert len(same)==1 and matches(same[0],wanted),'Alias conflict; no overwrite'
                    continue
                lo,hi=wanted['ExternalPort'],wanted['ExternalPortEndRange'] or wanted['ExternalPort']
                for r in current:
                    if r['Enable'] and r['Protocol'] in (wanted['Protocol'],'BOTH','ALL'):
                        rlo,rhi=r['ExternalPort'],r['ExternalPortEndRange'] or r['ExternalPort']
                        assert hi<rlo or lo>rhi,'External port conflict'
                router.request([{'method':'addChild','xpath':NAT,'parameters':{'value':{'PortMapping':wanted}}}])
                installed=[r for r in router.get() if r['Alias']==wanted['Alias']]
                assert len(installed)==1 and matches(installed[0],wanted),'Added rule differs from request'
        elif args.rollback:
            for wanted in PROPOSED:
                for r in router.get():
                    if r['Alias']==wanted['Alias']:
                        assert matches(r,wanted),'Rule changed since deployment; inspect manually'
                        router.request([{'method':'deleteChild','xpath':NAT+'/PortMapping[@uid='+str(r['uid'])+']'}])
        after=router.get()
        (EVIDENCE/('nat-'+stamp+'-after.json')).write_text(json.dumps(after,indent=2)+'\n')
        managed={r['Alias'] for r in PROPOSED}
        assert [r for r in before if r['Alias'] not in managed]==[r for r in after if r['Alias'] not in managed],'Unrelated rules changed'
        print(json.dumps({'action':'apply' if args.apply else 'rollback' if args.rollback else 'read',
                          'rules':[r for r in after if r['Alias'] in managed],
                          'unrelated_rules_unchanged':True},ensure_ascii=False,indent=2))
    finally:
        router.request([{'method':'logOut'}])

if __name__=='__main__':
    main()
