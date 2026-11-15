#!/usr/bin/env python3
"""Compile only the two Asterisk DSOs, sequentially, using exact extracted headers.

No configure, installation, service operations, or runtime loading occur here.
The parent may patch src/addons/chan_mobile.c and src/channels/chan_iax2.c first.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import shlex
import subprocess
import sys
import time


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--module', choices=('mobile', 'iax', 'both'), default='both')
    parser.add_argument('--cc', default='cc')
    args = parser.parse_args()
    root = Path(__file__).resolve().parent
    if platform.machine() != 'x86_64':
        raise SystemExit('This build input set is for the verified x86_64 target only')
    manifest = json.loads((root / 'manifest.json').read_text())
    for relative, expected in manifest['immutable_files_sha256'].items():
        if digest(root / relative) != expected:
            raise SystemExit('Immutable input mismatch: ' + relative)
    buildopts = (root / 'include-dev/asterisk/buildopts.h').read_text()
    if '#define AST_BUILDOPT_SUM "1fb7f5c06d7a2052e38d021b3d8ca151"' not in buildopts:
        raise SystemExit('Unexpected target ABI checksum')
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    include = ['-I' + str(root / p) for p in (
        'include-dev', 'include-source', 'include-bluetooth', 'src/channels')]
    # Preserve distro optimisation / partial-inlining workaround. LTO/native
    # tuning are deliberately omitted so neither build nor link spawns a pool.
    common = ['-g', '-O3', '-fno-partial-inlining', '-fno-lto', '-fPIC',
              '-pthread', '-fstack-protector-strong', '-fstack-clash-protection',
              '-fcf-protection', '-Wdate-time', '-D_FORTIFY_SOURCE=3',
              '-Wall', '-Wstrict-prototypes', '-Wmissing-prototypes',
              '-Wmissing-declarations', '-Wformat=2', '-Werror=format-security']
    link = ['-shared', '-pthread', '-fno-lto', '-Wl,--as-needed',
            '-Wl,-Bsymbolic-functions', '-Wl,-z,relro', '-Wl,-z,now',
            '-Wl,--warn-common', '-Wl,--version-script=' + str(root / 'default.exports')]
    record = {'base_package_version': manifest['asterisk_version'],
              'abi_checksum': manifest['abi_checksum'],
              'compiler': subprocess.check_output([args.cc, '--version'], text=True).splitlines()[0],
              'uname': platform.uname()._asdict(),
              'commands': [], 'inputs_sha256': {}, 'outputs_sha256': {}}
    selected = {'mobile': ['chan_mobile'], 'iax': ['chan_iax2'],
                'both': ['chan_mobile', 'chan_iax2']}[args.module]
    started = time.monotonic()
    try:
        for module in selected:
            if module == 'chan_mobile':
                sources = [root / 'src/addons/chan_mobile.c']
                libraries = ['-l:libbluetooth.so.3']
            else:
                sources = [root / 'src/channels/chan_iax2.c']
                sources += sorted((root / 'src/channels/iax2').glob('*.c'))
                if len(sources) != 7:
                    raise SystemExit('Expected chan_iax2 plus the six upstream iax2 helper sources')
                libraries = []
            object_dir = out / (module + '-objects')
            object_dir.mkdir(exist_ok=True)
            objects = []
            defines = ['-DAST_MODULE="' + module + '"',
                       '-DAST_MODULE_SELF_SYM=__internal_' + module + '_self']
            for source in sources:
                record['inputs_sha256'][str(source.relative_to(root))] = digest(source)
                obj = object_dir / (source.stem + '.o')
                command = [args.cc] + common + include + defines + ['-c', str(source), '-o', str(obj)]
                record['commands'].append(command)
                print(shlex.join(command), flush=True)
                subprocess.run(command, check=True)
                objects.append(str(obj))
            target = out / (module + '.so')
            command = [args.cc] + link + objects + libraries + ['-o', str(target)]
            record['commands'].append(command)
            print(shlex.join(command), flush=True)
            subprocess.run(command, check=True)
            record['outputs_sha256'][target.name] = digest(target)
            print(subprocess.check_output(['readelf', '-h', str(target)], text=True), flush=True)
            print(subprocess.check_output(['readelf', '-d', str(target)], text=True), flush=True)
    finally:
        record['duration_seconds'] = time.monotonic() - started
        (out / 'build-record.json').write_text(json.dumps(record, indent=2) + '\n')


if __name__ == '__main__':
    main()
