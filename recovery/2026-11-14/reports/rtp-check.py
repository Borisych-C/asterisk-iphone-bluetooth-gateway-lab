import collections
import os
from pathlib import Path
import re
import runpy
import subprocess

def cli(command):
    return subprocess.check_output(['asterisk','-rx',command],text=True,timeout=6)

name = 'direct-phone-rtp-' + str(os.getpid())
log = Path('/var/log/asterisk')/name
try:
    print(cli('logger add channel '+name+' debug,verbose,warning,error'),flush=True)
    print(cli('core set debug 3 res_rtp_asterisk'),flush=True)
    runpy.run_path('/home/gateway/asterisk-host-framing-20261114/check.py',run_name='__main__')
finally:
    cli('core set debug 0 res_rtp_asterisk')
    cli('logger remove channel '+name)
    if log.exists():
        counts = collections.Counter()
        for line in log.read_text(errors='replace').splitlines():
            if any(x in line.lower() for x in ('strict rtp','dropping','unknown','payload','ssrc','rtp allocated','rtp instance')):
                line = re.sub(r'0x[0-9a-fA-F]+','<ptr>',line)
                # Group repetitive rejection lines without retaining audio or SIP data.
                line = re.sub(r'^\[[^]]+\] \w+\[\d+\]: ', '', line)
                counts[line] += 1
        for line,count in counts.most_common(40):
            print('RTP_LOG',count,line,flush=True)
        log.unlink()
