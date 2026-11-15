# Minimal target build inputs

For x86_64 Linux Mint 22.3 / Ubuntu noble, Asterisk
`1:20.6.0~dfsg+~cs6.13.40431414-2build5` only. No module has been compiled as
part of preparing this archive.

Archive root: `target-build-inputs/`.

- `include-dev/`: all headers extracted from the exact Ubuntu `asterisk-dev`
  binary package. This include directory **must come first**. It contains the
  generated `autoconfig.h`, `buildopts.h` and distro-modified public headers.
  `AST_BUILDOPT_SUM` is `1fb7f5c06d7a2052e38d021b3d8ca151`, matching the running
  target's `OPTIONAL_API, TEST_FRAMEWORK`.
- `include-source/`: upstream source include tree, supplying private
  `jitterbuf.h`. Generated public headers continue to come from `include-dev`.
- `include-bluetooth/`: headers from target-compatible
  `libbluetooth-dev=5.72-0ubuntu5.8`. No static library is included or required.
- `src/addons/chan_mobile.c`: unmodified exact source; replace/patch this file.
- `src/channels/chan_iax2.c`: unmodified exact source; replace/patch this file.
- `src/channels/iax2/`: **all six** IAX helper C files and their local headers,
  required by the upstream channels Makefile's `MOD_ADD_C` rule.
- `default.exports`: upstream loadable-module GNU linker version script.

The two module sources and IAX helpers are identical between the upstream
20.6.0 files and this Ubuntu orig source. None of the Debian/Ubuntu patches in
the exact source package modifies them. Public distro header changes, notably
`format_cache.h`, are included through the exact dev package rather than by
trying to regenerate configure output.

After applying the reviewed patches, run on the target (as the build user):

```sh
python3 target-build-inputs/build-modules.py --out /absolute/build/output
```

Or build one module with `--module mobile` / `--module iax`. Compilation is
sequential; there is no LTO or `target-cpu=native`. The distro's `-O3` and
`-fno-partial-inlining` workaround and normal hardening are retained. Build
commands, input/output hashes and environment are saved in `build-record.json`.

`chan_mobile.so` links directly to the target's already installed
`libbluetooth.so.3` with `-l:libbluetooth.so.3`. Do not rely on the dev package's
`libbluetooth.so` symlink: its versioned target is not in this extracted tree.
IAX calls Asterisk's crypto optional API, so it does not need PJPROJECT headers
or a rebuilt PJPROJECT. The distro `--as-needed` link drops unused libcrypto;
compare the resulting DT_NEEDED entries with the original module on target.

The original source build uses `default.exports` for both DSOs. Keep that
version script: compiling a DSO without it may expose helper symbols and
change symbol interposition. Do not add `-z defs` for modules: unresolved
`ast_*` references intentionally resolve against the Asterisk core at load.

## Before installation

1. Verify the running core's package version, architecture and ABI checksum.
2. Confirm the DSO contains the expected build hash, and inspect DT_NEEDED,
   GNU_RELRO and BIND_NOW with readelf. Compare undefined/public symbol sets to
   the original module; no new unresolved internal helper should appear.
3. Load against an isolated instance of the installed core with its own
   configuration/run/state directories and no real calling endpoints. The
   loader checks `module_info.buildopt_sum` before calling `load_module`.
   A missing Bluetooth adapter can make mobile decline after the ABI check;
   that is not evidence of a successful functional Bluetooth test.
4. Run the dedicated algorithm/race tests and the isolated protocol scenarios.
   Only a real Bluetooth call can prove Bluetooth negotiation and audio.

This script does not install, replace, load, unload or restart anything.
Package/deployment policy and rollback belong to the parent implementation.
The minimal-inputs archive is not a complete distro source build tree.
