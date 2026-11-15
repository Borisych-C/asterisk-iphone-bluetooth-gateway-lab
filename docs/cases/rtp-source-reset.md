# RTP arrives but outgoing Bluetooth audio stops intermittently

Case: `rtp-source-reset` · Evidence: **confirmed-reproduced**

Search terms: Asterisk ast_translate NULL, SSRC change, seqno reset, 2016_opus_plc.patch, Debian 1150408, Ubuntu 2053070

## Diagnosis

The distribution translator patch retained old sequence history across a new SSRC. A smaller random new sequence looked late; RTP kept arriving but no PCM reached mbl_write.

## Resolution

Opt-in RtpSourceReset framehook resets translator sequence history on AST_CONTROL_SRCCHANGE. Keep late packet rejection for the same source. Inspect the installed distro code, not only upstream version tags.

## Evidence and limits

Isolated real PCMA→PCM test: failing phases 0/50 before; 450/450 correct after; an extra genuinely late packet still dropped. Real calls confirmed. Rebuild after ABI changes; upstream bug status must be checked separately.

## Code and reproduction

- [Implementation](../../recovery/2026-11-14/work/app_rtp_source_reset.c)
- [Test or detailed evidence](../../recovery/2026-11-14/work/isolated-rtp.py)

Read [agent instructions](../../AGENTS.md) before executing scripts. A test may place a real call, send SMS or change a live system; inspect its effect first.
