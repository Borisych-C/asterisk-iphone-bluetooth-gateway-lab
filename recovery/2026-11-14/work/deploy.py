import hashlib, os, subprocess, tempfile, time
from pathlib import Path

def run(*args):
    return subprocess.run(args,check=True,capture_output=True,text=True,timeout=35).stdout

def cli(cmd):
    return run('/usr/sbin/asterisk','-rx',cmd)

def sha(data):
    return hashlib.sha256(data).hexdigest()

def replace(data):
    fd,temp=tempfile.mkstemp(prefix='.chan_mobile.',dir=path.parent)
    try:
        with os.fdopen(fd,'wb') as f:
            os.fchown(f.fileno(),attrs.st_uid,attrs.st_gid)
            os.fchmod(f.fileno(),attrs.st_mode & 0o777)
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        os.replace(temp,path)
    finally:
        Path(temp).unlink(missing_ok=True)

path=Path('/usr/lib/x86_64-linux-gnu/asterisk/modules/chan_mobile.so')
candidate=Path('/home/gateway/asterisk-host-framing-20261114/built/chan_mobile.so').read_bytes()
previous=path.read_bytes()
attrs=path.stat()
old_sha='d0d8cbb5d4ef4c6e73d72dc6cd96814366521dfbf706e79ba4aa4a6355a2410a'
new_sha='9aa871cd579d2547e1ba5633218fab50830bc3ada777b9b5eec3cdd3f105632c'
assert sha(candidate)==new_sha
assert sha(previous)==old_sha
assert '0 active channels' in cli('core show channels count')
assert 'Yes       Free' in cli('mobile show devices')
assert '1002/sip:' in cli('pjsip show aor 1002')
backup=Path('/var/backups/asterisk-host-framing-20261114')
backup.mkdir(mode=0o700)
(backup/path.name).write_bytes(previous)
assert sha((backup/path.name).read_bytes())==old_sha
pid=run('systemctl','show','asterisk','-p','MainPID','--value').strip()
print(cli('module unload chan_mobile.so').strip(),flush=True)
assert 'Running' not in cli('module show like chan_mobile')
try:
    replace(candidate)
    print(cli('module load chan_mobile.so').strip(),flush=True)
    assert 'Running' in cli('module show like chan_mobile')
    maps=Path(f'/proc/{pid}/maps').read_text().splitlines()
    assert {int(l.split()[4]) for l in maps if l.endswith(str(path))}=={path.stat().st_ino}
    for _ in range(22):
        state=cli('mobile show devices')
        if 'Yes       Free' in state:
            break
        time.sleep(2)
    else:
        raise RuntimeError('Bluetooth did not reconnect')
    assert '1002/sip:' in cli('pjsip show aor 1002')
    print(state,flush=True)
except Exception:
    assert '0 active channels' in cli('core show channels count')
    if 'Running' in cli('module show like chan_mobile'):
        cli('module unload chan_mobile.so')
        assert 'Running' not in cli('module show like chan_mobile')
    replace(previous)
    cli('module load chan_mobile.so')
    raise
