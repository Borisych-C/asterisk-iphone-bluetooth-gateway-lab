# Build, test and effect boundaries

## Offline public-source acceptance

Requires Python 3, Bash, a C compiler and Address/UndefinedBehavior sanitizer runtimes. No account credentials or Bluetooth device are needed.

```sh
python3 scripts/check.py
```

This parses Python/AGI and shell, validates JSON and important navigation, checks source-header hashes and basic publication boundaries, runs 18 SMS bridge tests, 16 fake-network DNS scenarios and the real Unix seqpacket C framing harness. It does not load modules, touch system configuration or make a real SIP/HTTP/phone request. Mocking only proves the modeled cases.

If installed, run the independent scanner as well:

```sh
gitleaks detect --no-git --source . --config .gitleaks.toml --redact
```

The allowlist covers only SHA256-shaped integrity records. Do not suppress a directory of actual code to silence findings. Automated scanners do not establish absence of every form of private data.

## Compile modules without installing them

The extracted headers are for the recorded x86-64 Ubuntu/Mint Asterisk package and ABI, **not automatically your installed build**. Read `recovery/2026-11-14/work/input/README.md` and its manifest. That README was written before patching; the public `input/src/addons/chan_mobile.c` already matches the final patched `work/chan_mobile.c`.

```sh
cd recovery/2026-11-14/work
mkdir -p built
python3 input/build-modules.py --module mobile --out "$PWD/built"
python3 build-source-reset.py
```

Build requires target-compatible libraries/headers. This produces binaries only; do not load them into a different ABI. `built/` and all `.so` files are ignored by Git. Paths and environment data in generated build records may be private; they are not publication inputs.

`previous.c` is the intermediate incorrect framing version, `recovery.c` the earlier partial fix, `chan_mobile.c` the final source. `from-previous.patch` and `from-recovery.patch` are relative to those exact baselines. They are not universal patches against every upstream release. `prepare.py` regenerates the final version from recovery.c; inspect before overwriting files.

## Device and live-service tests (not CI)

`isolated-rtp.py` runs a separate Asterisk with local ports and real translation; inspect binary paths/dependencies first. It is not part of the offline check because it requires the exact server environment. Existing historical results document 450/450 PCM frames and rejection of the extra late packet; CI does not reassert that result on arbitrary versions.

Any script that deploys, installs, changes DNS/router rules, captures traffic, sends messages, calls a phone or restarts a service needs explicitly configured local values and the user's authorized scenario. Inventory classification is a navigation aid, not a substitute for reading the script. Keep full SIP/AGI captures private. A `smscheck` route deliberately sends no cellular message and now creates no user-facing chat notice.

After adaptation, validate both call directions, caller ID, hangup, blocked-screen incoming, carrier SMS separately from iMessage, outgoing without touching the home iPhone, and a genuinely external network. Update/reboot recovery and long-run reliability remain separate acceptance work.
