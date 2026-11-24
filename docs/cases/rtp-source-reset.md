# RTP arrives but outgoing Bluetooth audio stops intermittently

Case: `rtp-source-reset` · Evidence: **confirmed-reproduced**

Search terms: Asterisk ast_translate NULL, SSRC change, seqno reset, 2016_opus_plc.patch, Debian 1150408, Ubuntu 2053070

## Diagnosis

The distribution translator patch retained old sequence history across a new SSRC. A smaller random new sequence looked late; RTP kept arriving but no PCM reached mbl_write.

## Resolution

Opt-in RtpSourceReset framehook resets translator sequence history on AST_CONTROL_SRCCHANGE. Keep late packet rejection for the same source. Inspect the installed distro code, not only upstream version tags.

## Evidence and limits

A separate unprivileged Noble 20.6.0 instance yielded 250/450 valid PCMA-to-PCM frames, with complete loss in four of nine phases. With the local workaround, 450/450 frames were valid and an extra late packet produced no additional PCM. The package patch is tracked by Debian and Ubuntu. Rebuild the workaround against the target ABI.

[Per-phase results and exact reproduction commands](../../research/rtp-source-reset.md).

## Code and reproduction

- [Implementation](../../recovery/2026-11-14/work/app_rtp_source_reset.c)
- [Test or detailed evidence](../../recovery/2026-11-14/work/isolated-rtp.py)

Read [agent instructions](../../AGENTS.md) before executing scripts. A test may place a real call, send SMS or change a live system; inspect its effect first.

## Reports

[Debian #1150408](https://bugs.debian.org/1150408) · [Ubuntu #2053070](https://bugs.launchpad.net/ubuntu/+source/asterisk/+bug/2053070) · [Published results in Asterisk #1324](https://github.com/asterisk/asterisk/issues/1324#issuecomment-7140548093).
