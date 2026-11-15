"""Build against the verified target headers, without installing or loading."""
import hashlib
import json
from pathlib import Path
import subprocess
import time

root=Path(__file__).resolve().parent
headers=root/'input'
manifest=json.loads((headers/'manifest.json').read_text())
for relative,expected in manifest['immutable_files_sha256'].items():
    if hashlib.sha256((headers/relative).read_bytes()).hexdigest()!=expected:
        raise SystemExit('Immutable input mismatch: '+relative)
source=root/'app_rtp_source_reset.c'
output=root/'built/app_rtp_source_reset.so'
command=['cc','-O2','-g','-fno-lto','-fPIC','-pthread','-fstack-protector-strong',
         '-fstack-clash-protection','-fcf-protection','-D_FORTIFY_SOURCE=3',
         '-Wall','-Wextra','-Werror','-Wstrict-prototypes','-Wmissing-prototypes',
         '-Wmissing-declarations','-Wformat=2','-isystem','input/include-dev',
         '-isystem','input/include-source','-DAST_MODULE="app_rtp_source_reset"',
         '-DAST_MODULE_SELF_SYM=__internal_app_rtp_source_reset_self','-shared',
         '-Wl,-Bsymbolic-functions','-Wl,-z,relro','-Wl,-z,now',
         '-Wl,--version-script=input/default.exports','app_rtp_source_reset.c',
         '-o','built/app_rtp_source_reset.so']
start=time.monotonic()
subprocess.run(command,cwd=root,check=True)
record=dict(command=command,cwd=str(root),duration_seconds=time.monotonic()-start,
            compiler=subprocess.check_output(['cc','--version'],text=True).splitlines()[0],
            package=manifest['asterisk_version'],abi=manifest['abi_checksum'],
            source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
            module_sha256=hashlib.sha256(output.read_bytes()).hexdigest())
(root/'built/source-reset-build.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps(record,indent=2))
