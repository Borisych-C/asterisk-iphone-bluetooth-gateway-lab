# Reproducing loss of decoded audio after an RTP source change

On 24 November 2026 we ran the Ubuntu Noble package `1:20.6.0~dfsg+~cs6.13.40431414-2build5` twice in a separate unprivileged Asterisk process. Both runs used the installed translator and codec, identical synthetic RTP and a loopback SIP endpoint. AudioSocket exposed the decoded PCM for comparison with the source. Bluetooth and a real phone are unnecessary. The related package reports are [Debian #1150408](https://bugs.debian.org/1150408) and [Ubuntu #2053070](https://bugs.launchpad.net/ubuntu/+source/asterisk/+bug/2053070). A user running the distro package also reported the symptom in [Asterisk #1324](https://github.com/asterisk/asterisk/issues/1324).

| Phase in one call | Initial sequence | Valid PCM on package, of 50 | With local framehook, of 50 |
|---:|---:|---:|---:|
| 1 | 303 | 50 | 50 |
| 2 | 2633 | 50 | 50 |
| 3 | 59789 | 0 | 50 |
| 4 | 55456 | 0 | 50 |
| 5 | 7909 | 50 | 50 |
| 6 | 10861 | 50 | 50 |
| 7 | 17853 | 50 | 50 |
| 8 | 8704 | 0 | 50 |
| 9 | 13394 | 0 | 50 |
| **Total** | | **250/450** | **450/450** |

Each phase changes SSRC and injects 50 PCMA packets, each with one 20 ms frame. In phase 9 an extra late packet from the same SSRC produced no extra PCM with the workaround. Four whole phases yielded no decoded audio on the stock package. This is a deterministic check of the installed distribution translator. Upstream release builds and other distribution patches need their own comparison.

## Running the test

Use a disposable x86-64 Linux environment with the package modules, the `asterisk` executable, and Python 3.12 (the script imports `audioop`). Run as an ordinary user from the repository root. The script starts its own Asterisk instance with a temporary configuration, uses loopback SIP, RTP and AudioSocket, and stops that instance on exit. The test expects unused fixture ports. The per-phase output and the final `all_phases_passed` flag report the result. The per-run directory printed as `root` retains the fixture logs.

```sh
python3 recovery/2026-11-14/work/isolated-rtp.py
```

The stock test works without the optional module. For the comparison use the [framehook source](../recovery/2026-11-14/work/app_rtp_source_reset.c) built for this distribution's exact Asterisk ABI. Supply its absolute path on the isolated instance.

```sh
python3 recovery/2026-11-14/work/isolated-rtp.py --fix-module /path/to/app_rtp_source_reset.so
```

The local workaround resets the patched translator's sequence history on a source-change indication. The second run also passed the in-use module guard and released the hook after hangup. Maintainers can use the stock test to evaluate a package-level correction independently.
